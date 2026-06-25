# Personal Shop Manager

Personal Shop Manager is a desktop application for individual online-store sellers. It helps manage daily shop operations across **Inventory**, **Orders**, and **Customer Service Tickets** in one local PySide6 application.

The app uses a local SQLite database, so it can run without a server or cloud account.

---

## Features

### 📦 Inventory Management

- Add, edit, and delete products
- Track SKU, product name, category, price, stock quantity, low-stock threshold, and description
- Search products by name or SKU
- Filter products by category
- Show low-stock products with visual highlighting
- Import products from Excel or CSV
- Export products to Excel or CSV
- Print product list
- Inventory table refreshes automatically after order stock changes

### 📋 Order Management

- Create new orders with customer information and product line items
- Search products while creating an order
- Automatically calculate line totals and order total
- Validate stock before saving an order
- Automatically deduct inventory when an order is created
- View order details
- Edit full order information:
  - Customer name
  - Customer contact
  - Notes
  - Product items
  - Quantities
- Automatically synchronize inventory when an order is edited
- Restore inventory when an order is cancelled
- Status flow:
  - `Pending` → `Shipped` → `Completed`
  - `Pending` → `Cancelled`
- Export orders to Excel or CSV
- Print order details

### 💬 Customer Service Ticket Management

- Create customer service tickets
- Link tickets to existing orders
- Track customer name, contact, subject, description, priority, and status
- Ticket priorities:
  - `Low`
  - `Medium`
  - `High`
- Ticket status flow:
  - `Open` → `In Progress` → `Resolved` → `Closed`
  - Closed tickets can be reopened
- Add processing logs to tickets
- View ticket details and linked order information
- Export tickets to Excel or CSV

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| GUI | PySide6 |
| Database | SQLite |
| ORM | SQLAlchemy 2.x |
| Import / Export | pandas, openpyxl |
| Printing | Qt Print Support / ReportLab dependency |

---

## Project Structure

```text
shop-manager/
├── main.py                  # Application entry point and global styling
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
├── data/
│   └── shop.db              # Local SQLite database, auto-created at runtime
├── database/
│   ├── __init__.py
│   ├── db.py                # Database initialization and session factory
│   └── models.py            # SQLAlchemy ORM models
├── ui/
│   ├── __init__.py
│   ├── inventory.py         # Inventory page and product dialog
│   ├── main_window.py       # Main window, sidebar navigation, page wiring
│   ├── order.py             # Order page, order dialog, stock synchronization
│   ├── service.py           # Customer service ticket page and ticket dialogs
│   └── widgets.py           # Shared dialog and table widgets
└── docs/
    ├── specs/               # Design documents
    └── superpowers/         # Implementation plan documents
```

---

## Installation

### 1. Clone or open the project

```bash
cd C:\Users\fanwu\OneDrive\Documents\PythonProjects\shop-manager
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

```bash
python main.py
```

The application opens a desktop window with a left sidebar:

- **Inventory**
- **Orders**
- **Service**

---

## Data Storage

The application stores data locally in:

```text
data/shop.db
```

The database is created automatically when the app starts.

Because this is a local SQLite database, back up `data/shop.db` if you want to preserve shop data before deleting or moving the project.

---

## Import / Export Notes

### Product Import

Product import supports `.xlsx` and `.csv` files.

Required columns:

- `sku`
- `name`
- `price`

Optional columns:

- `category`
- `stock`
- `min_stock`
- `description`

### Exports

The app can export:

- Products
- Orders
- Tickets

Supported export formats:

- `.xlsx`
- `.csv`

---

## Current Version Notes

This is a local personal shop manager focused on single-user workflows.

Included in the current version:

- Local desktop UI
- Local SQLite storage
- Inventory CRUD
- Order creation and full order editing
- Automatic stock deduction/restoration/synchronization
- Customer service tickets with processing logs
- Import/export and printing support
- Improved high-contrast styling for main windows and popup dialogs

Not included yet:

- Multi-user login
- Cloud synchronization
- Advanced analytics dashboard
- Shipping label generation
- Product image management
- Email/SMS notifications

---

## Development Notes

Useful syntax check command:

```bash
python -m py_compile main.py database\db.py database\models.py ui\*.py
```

Run the app after code changes:

```bash
python main.py
```

---

## Git Notes

`data/shop.db` contains local runtime data. If you do not want to commit local test data, avoid staging it:

```bash
git restore --staged data/shop.db
```

Or discard local database changes if appropriate:

```bash
git restore data/shop.db
```
