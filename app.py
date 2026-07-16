import os
import sqlite3
import uuid
from datetime import datetime

import qrcode
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "inventory.db")
QR_DIR = os.path.join(BASE_DIR, "static", "qr_codes")

app = Flask(__name__)
app.config["SECRET_KEY"] = "inventory-qr-tracking-dev-key"
app.config["QR_CODES"] = QR_DIR

os.makedirs(QR_DIR, exist_ok=True)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT DEFAULT 'General',
            quantity INTEGER NOT NULL DEFAULT 0,
            unit_price REAL NOT NULL DEFAULT 0,
            location TEXT DEFAULT '',
            qr_token TEXT UNIQUE NOT NULL,
            qr_filename TEXT NOT NULL,
            min_stock INTEGER NOT NULL DEFAULT 5,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """
    )
    db.commit()
    db.close()


def generate_sku():
    return f"SKU-{uuid.uuid4().hex[:8].upper()}"


def generate_qr_token():
    return uuid.uuid4().hex


def create_qr_image(token, filename, base_url=None):
    """Encode a trackable product URL into a QR code image."""
    root = (base_url or "http://127.0.0.1:5000").rstrip("/")
    track_url = f"{root}/track/{token}"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(track_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B3D2E", back_color="#F7F4EF")
    path = os.path.join(QR_DIR, filename)
    img.save(path)
    return path


def product_from_form(form, existing=None):
    name = (form.get("name") or "").strip()
    description = (form.get("description") or "").strip()
    category = (form.get("category") or "General").strip() or "General"
    location = (form.get("location") or "").strip()
    try:
        quantity = int(form.get("quantity") or 0)
        unit_price = float(form.get("unit_price") or 0)
        min_stock = int(form.get("min_stock") or 5)
    except ValueError:
        return None, "Quantity, price, and minimum stock must be numbers."

    if not name:
        return None, "Product name is required."
    if quantity < 0 or unit_price < 0 or min_stock < 0:
        return None, "Numeric values cannot be negative."

    sku = (form.get("sku") or "").strip()
    if not sku:
        sku = existing["sku"] if existing else generate_sku()

    return {
        "sku": sku,
        "name": name,
        "description": description,
        "category": category,
        "quantity": quantity,
        "unit_price": unit_price,
        "location": location,
        "min_stock": min_stock,
    }, None


def log_movement(db, product_id, movement_type, quantity, note=""):
    db.execute(
        """
        INSERT INTO movements (product_id, movement_type, quantity, note, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (product_id, movement_type, quantity, note, datetime.utcnow().isoformat()),
    )


@app.route("/")
def dashboard():
    db = get_db()
    stats = db.execute(
        """
        SELECT
            COUNT(*) AS total_products,
            COALESCE(SUM(quantity), 0) AS total_units,
            COALESCE(SUM(quantity * unit_price), 0) AS inventory_value,
            SUM(CASE WHEN quantity <= min_stock THEN 1 ELSE 0 END) AS low_stock
        FROM products
        """
    ).fetchone()

    recent = db.execute(
        """
        SELECT m.*, p.name AS product_name, p.sku
        FROM movements m
        JOIN products p ON p.id = m.product_id
        ORDER BY m.created_at DESC
        LIMIT 8
        """
    ).fetchall()

    low_stock = db.execute(
        """
        SELECT * FROM products
        WHERE quantity <= min_stock
        ORDER BY quantity ASC
        LIMIT 6
        """
    ).fetchall()

    categories = db.execute(
        """
        SELECT category, COUNT(*) AS count, SUM(quantity) AS units
        FROM products
        GROUP BY category
        ORDER BY units DESC
        """
    ).fetchall()

    return render_template(
        "dashboard.html",
        stats=stats,
        recent=recent,
        low_stock=low_stock,
        categories=categories,
    )


@app.route("/products")
def products():
    db = get_db()
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()

    sql = "SELECT * FROM products WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE ? OR sku LIKE ? OR location LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY updated_at DESC"

    items = db.execute(sql, params).fetchall()
    categories = db.execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    ).fetchall()
    return render_template(
        "products.html",
        products=items,
        q=q,
        category=category,
        categories=categories,
    )


@app.route("/products/new", methods=["GET", "POST"])
def product_new():
    if request.method == "POST":
        data, error = product_from_form(request.form)
        if error:
            flash(error, "error")
            return render_template("product_form.html", product=request.form, mode="new")

        db = get_db()
        existing = db.execute(
            "SELECT id FROM products WHERE sku = ?", (data["sku"],)
        ).fetchone()
        if existing:
            flash("A product with this SKU already exists.", "error")
            return render_template("product_form.html", product=request.form, mode="new")

        now = datetime.utcnow().isoformat()
        token = generate_qr_token()
        filename = f"{token}.png"
        create_qr_image(token, filename, base_url=request.url_root)

        cur = db.execute(
            """
            INSERT INTO products (
                sku, name, description, category, quantity, unit_price,
                location, qr_token, qr_filename, min_stock, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["sku"],
                data["name"],
                data["description"],
                data["category"],
                data["quantity"],
                data["unit_price"],
                data["location"],
                token,
                filename,
                data["min_stock"],
                now,
                now,
            ),
        )
        product_id = cur.lastrowid
        if data["quantity"] > 0:
            log_movement(db, product_id, "in", data["quantity"], "Initial stock")
        db.commit()
        flash("Product created and QR code generated.", "success")
        return redirect(url_for("product_detail", product_id=product_id))

    return render_template("product_form.html", product=None, mode="new")


@app.route("/products/<int:product_id>")
def product_detail(product_id):
    db = get_db()
    product = db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    movements = db.execute(
        """
        SELECT * FROM movements
        WHERE product_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (product_id,),
    ).fetchall()
    return render_template("product_detail.html", product=product, movements=movements)


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def product_edit(product_id):
    db = get_db()
    product = db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    if request.method == "POST":
        data, error = product_from_form(request.form, existing=product)
        if error:
            flash(error, "error")
            return render_template(
                "product_form.html", product=request.form, mode="edit", product_id=product_id
            )

        conflict = db.execute(
            "SELECT id FROM products WHERE sku = ? AND id != ?",
            (data["sku"], product_id),
        ).fetchone()
        if conflict:
            flash("Another product already uses this SKU.", "error")
            return render_template(
                "product_form.html", product=request.form, mode="edit", product_id=product_id
            )

        qty_delta = data["quantity"] - product["quantity"]
        db.execute(
            """
            UPDATE products SET
                sku = ?, name = ?, description = ?, category = ?,
                quantity = ?, unit_price = ?, location = ?, min_stock = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                data["sku"],
                data["name"],
                data["description"],
                data["category"],
                data["quantity"],
                data["unit_price"],
                data["location"],
                data["min_stock"],
                datetime.utcnow().isoformat(),
                product_id,
            ),
        )
        if qty_delta != 0:
            log_movement(db, product_id, "adjust", abs(qty_delta), "Manual quantity edit")
        db.commit()
        flash("Product updated.", "success")
        return redirect(url_for("product_detail", product_id=product_id))

    return render_template(
        "product_form.html", product=product, mode="edit", product_id=product_id
    )


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def product_delete(product_id):
    db = get_db()
    product = db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if product:
        qr_path = os.path.join(QR_DIR, product["qr_filename"])
        if os.path.isfile(qr_path):
            os.remove(qr_path)
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        flash("Product deleted.", "success")
    else:
        flash("Product not found.", "error")
    return redirect(url_for("products"))


@app.route("/products/<int:product_id>/stock", methods=["POST"])
def product_stock(product_id):
    db = get_db()
    product = db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    action = request.form.get("action")
    note = (request.form.get("note") or "").strip()
    try:
        amount = int(request.form.get("amount") or 0)
    except ValueError:
        flash("Enter a valid quantity.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    if amount <= 0:
        flash("Quantity must be greater than zero.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    if action == "in":
        new_qty = product["quantity"] + amount
        log_movement(db, product_id, "in", amount, note or "Stock in")
    elif action == "out":
        if amount > product["quantity"]:
            flash("Not enough stock available.", "error")
            return redirect(url_for("product_detail", product_id=product_id))
        new_qty = product["quantity"] - amount
        log_movement(db, product_id, "out", amount, note or "Stock out")
    else:
        flash("Invalid stock action.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    db.execute(
        "UPDATE products SET quantity = ?, updated_at = ? WHERE id = ?",
        (new_qty, datetime.utcnow().isoformat(), product_id),
    )
    db.commit()
    flash(f"Stock {'added' if action == 'in' else 'removed'} successfully.", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/scan", methods=["GET", "POST"])
def scan():
    product = None
    token = ""
    if request.method == "POST":
        token = (request.form.get("token") or "").strip()
        # Accept full track paths or raw tokens
        if "/track/" in token:
            token = token.rstrip("/").split("/track/")[-1]
        token = token.replace(" ", "")
        if token:
            db = get_db()
            product = db.execute(
                "SELECT * FROM products WHERE qr_token = ? OR sku = ?",
                (token, token),
            ).fetchone()
            if not product:
                flash("No product found for that QR code or SKU.", "error")
        else:
            flash("Enter a QR token, scan result, or SKU.", "error")

    return render_template("scan.html", product=product, token=token)


@app.route("/track/<token>")
def track(token):
    db = get_db()
    product = db.execute(
        "SELECT * FROM products WHERE qr_token = ?", (token,)
    ).fetchone()
    if not product:
        flash("Invalid or unknown QR code.", "error")
        return redirect(url_for("scan"))

    movements = db.execute(
        """
        SELECT * FROM movements
        WHERE product_id = ?
        ORDER BY created_at DESC
        LIMIT 10
        """,
        (product["id"],),
    ).fetchall()
    return render_template(
        "track.html", product=product, movements=movements, scanned=True
    )


@app.route("/movements")
def movements():
    db = get_db()
    rows = db.execute(
        """
        SELECT m.*, p.name AS product_name, p.sku
        FROM movements m
        JOIN products p ON p.id = m.product_id
        ORDER BY m.created_at DESC
        LIMIT 100
        """
    ).fetchall()
    return render_template("movements.html", movements=rows)


@app.template_filter("money")
def money_filter(value):
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


@app.template_filter("dt")
def datetime_filter(value):
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value).strftime("%b %d, %Y · %H:%M")
    except ValueError:
        return value


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
