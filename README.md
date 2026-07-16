# StockMark — Inventory Management with QR Tracking

A Python Flask web app for managing product inventory. Every product gets a unique QR code that links to its stock details, so you can look items up quickly by scanning or searching.

## Features

- Dashboard with total products, units on hand, inventory value, and low-stock alerts
- Add, edit, search, and delete products
- Automatic QR code generation for each product
- Stock in / stock out with movement history
- QR scan page (paste a token, URL, or SKU)
- Category overview and movement log

## What to download / install

### 1. Python 3.10 or newer

Download and install from: [https://www.python.org/downloads/](https://www.python.org/downloads/)

During setup on Windows, check **Add python.exe to PATH**.

Confirm it works:

```bash
python --version
```

If `python` is not found, try:

```bash
py --version
```

### 2. Project files

Clone or download this repository, then open a terminal in the project folder (the one that contains `app.py`).

### 3. Python packages

Install the required libraries from `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---------|---------|
| Flask | Web framework for the site |
| qrcode | Generate product QR codes |
| Pillow | Image support for QR codes |

## How to run

From the project folder:

```bash
python app.py
```

You should see something like:

```text
 * Running on http://127.0.0.1:5000
```

Open your browser and go to:

**http://127.0.0.1:5000**

To stop the server, press `Ctrl + C` in the terminal.

The first run creates `inventory.db` (SQLite database) and a `static/qr_codes/` folder for QR images automatically.

### Optional: virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

python -m pip install -r requirements.txt
python app.py
```

## How to use the website

### Overview (home)

Shows inventory totals, recent stock movements, low-stock items, and category breakdowns.

### Products

1. Open **Products** in the sidebar.
2. Click **Add product** (or **+ New product**).
3. Fill in name, quantity, price, location, category, and minimum stock.
4. Save — a QR code is generated automatically.
5. Open a product to view its QR image, edit details, or change stock.

You can search by name, SKU, or location, and filter by category.

### Stock in / stock out

On a product detail page:

- **Stock in** — add units to inventory
- **Stock out** — remove units (cannot exceed current quantity)

Each change is saved in the movement history.

### QR codes

- Each product has a unique QR code pointing to `/track/<token>`.
- Print or display the QR from the product detail page.
- Scanning it (or opening the link) shows that product’s tracking page.

### QR Scan page

1. Open **QR Scan**.
2. Paste a QR token, a full track URL, or a SKU.
3. Submit to find the matching product.

### Movements

Open **Movements** to see recent stock in, stock out, and adjustment records across all products.

## Project structure

```text
.
├── app.py                 # Flask application and routes
├── requirements.txt       # Python dependencies
├── inventory.db           # SQLite database (created on first run)
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── qr_codes/          # Generated QR images
└── templates/             # HTML pages
```

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `python` / `pip` not recognized | Reinstall Python with **Add to PATH**, or use `py -m pip` and `py app.py` |
| Port 5000 already in use | Stop the other process using that port, or change `port=5000` in `app.py` |
| Page shows an error after code changes | Restart the server (`Ctrl + C`, then `python app.py` again) |
| QR image missing | Open the product detail page again after creating the product; check `static/qr_codes/` |

## Notes

- This uses Flask’s built-in development server — fine for local use, not for public production hosting.
- Data is stored locally in `inventory.db`. Back up that file if you want to keep your inventory.
