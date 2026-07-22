# StockMark — Inventory Management with QR Tracking

A Python Flask web app for managing product inventory. Every product gets a unique QR code that links to its stock details, so you can look items up quickly by scanning with your webcam, phone, or manual search.

## Features

- **Dashboard** — total products, units on hand, inventory value, low-stock alerts, and category breakdown
- **Product management** — add, edit, search, filter, and delete products
- **QR codes** — automatically generated for each product
- **Webcam scanner** — scan product QR codes from the browser with selectable cameras
- **Stock in / stock out** — update quantities with full movement history
- **Movement log** — track stock in, stock out, and manual adjustments

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| Database | SQLite |
| QR generation | `qrcode`, Pillow |
| QR scanning (browser) | [html5-qrcode](https://github.com/mebjas/html5-qrcode) (loaded via CDN) |
| Frontend | HTML, CSS, JavaScript |

## Requirements

- **Python 3.10+**
- A modern web browser (Chrome, Edge, or Firefox recommended)
- Webcam (optional, for live QR scanning)

## Installation

### 1. Install Python

Download from [python.org/downloads](https://www.python.org/downloads/).

On Windows, enable **Add python.exe to PATH** during setup.

Verify installation:

```bash
python --version
```

If `python` is not found, try:

```bash
py --version
```

On Windows, you may also need the full path:

```powershell
C:\Users\<YourName>\AppData\Local\Programs\Python\Python312\python.exe --version
```

### 2. Get the project

Clone or download this repository, then open a terminal in the project folder (the one containing `app.py`).

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

Packages installed:

| Package | Purpose |
|---------|---------|
| Flask | Web framework |
| qrcode | Generate product QR codes |
| Pillow | Image support for QR codes |

## How to run

From the project folder:

```bash
python app.py
```

Expected output:

```text
 * Running on http://127.0.0.1:5000
```

Open in your browser:

**http://127.0.0.1:5000**

Stop the server with `Ctrl + C`.

On first run, the app automatically creates:

- `inventory.db` — SQLite database
- `static/qr_codes/` — folder for generated QR images

### Virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

python -m pip install -r requirements.txt
python app.py
```

## How to use

### Overview (home page)

View inventory totals, recent stock movements, low-stock warnings, and products grouped by category.

### Products

1. Go to **Products** in the sidebar.
2. Click **Add product** or **+ New product**.
3. Enter name, quantity, price, location, category, and minimum stock level.
4. Save — a QR code is created automatically.
5. Open any product to view its QR code, edit details, or update stock.

Search by name, SKU, or location. Filter by category.

### Stock in / stock out

On a product detail page:

- **Stock in** — add units to inventory
- **Stock out** — remove units (cannot go below zero)

Every change is recorded in the movement history.

### QR codes

- Each product has a unique QR code linking to `/track/<token>`.
- View or print the QR from the product detail page.
- Scanning the code opens the live tracking page for that product.

### QR Scan (webcam + manual lookup)

1. Open **QR Scan** in the sidebar.
2. Choose a camera from the **Camera** dropdown (click **Refresh list** if none appear).
3. Click **Start camera** and allow webcam access when prompted.
4. Point the camera at a product QR code — the product page opens automatically.
5. Switch cameras anytime from the dropdown while scanning; your last choice is remembered.
6. Click **Stop camera** when finished, or paste a token / URL / SKU in the lookup field.

**Camera note:** Webcam scanning works on `http://127.0.0.1` or `http://localhost`. Other addresses may require HTTPS before the browser allows camera access.

### Movements

Open **Movements** to see the latest stock in, stock out, and adjustment records across all products.

## Project structure

```text
.
├── app.py                 # Flask app, routes, and database setup
├── requirements.txt       # Python dependencies
├── README.md
├── inventory.db           # SQLite database (created on first run)
├── static/
│   ├── css/style.css      # Styles
│   ├── js/app.js          # Shared UI behavior
│   ├── js/scan.js         # Webcam QR scanner
│   └── qr_codes/          # Generated QR images
└── templates/             # HTML pages
    ├── base.html
    ├── dashboard.html
    ├── products.html
    ├── product_detail.html
    ├── product_form.html
    ├── scan.html
    ├── track.html
    └── movements.html
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python` or `pip` not recognized | Reinstall Python with **Add to PATH**, or use `py -m pip` and `py app.py` |
| Port 5000 already in use | Stop the other app on that port, or change `port=5000` in `app.py` |
| Page error after editing code | Restart the server (`Ctrl + C`, then `python app.py`) |
| QR image missing | Re-open the product page; check `static/qr_codes/` |
| Camera won't start | Allow camera permission in browser settings; close other apps using the webcam |
| No cameras in dropdown | Click **Refresh list** on the QR Scan page to grant permission and reload devices |
| Camera blocked on non-localhost URL | Use `http://127.0.0.1:5000` or deploy with HTTPS |
| Git / commit not working | Install [Git for Windows](https://git-scm.com/download/win), then run `git init` in the project folder |

## Git setup (optional)

If you want to commit this project to GitHub:

1. Install Git from [git-scm.com/download/win](https://git-scm.com/download/win).
2. Restart your terminal or IDE after installation.
3. In the project folder:

```bash
git init
git add .
git commit -m "Initial commit: inventory management with QR tracking"
```

## Notes

- Uses Flask's built-in development server — suitable for local use, not for production deployment.
- Inventory data is stored in `inventory.db`. Back up this file to keep your data.
- Webcam scanning requires an internet connection on first load (html5-qrcode is loaded from CDN).
