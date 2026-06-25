# Personal Shop Manager — Design Document

**Date:** 2026-06-24
**Version:** v1.0
**Status:** Design Draft

---

## 1. Overview

Personal Shop Manager is a desktop application that helps individual sellers manage three core aspects of their online store operations: **Inventory Management**, **Order Management**, and **Customer Service Ticket Management**.

### 1.1 Tech Stack

| Component | Choice | Notes |
|-----------|--------|-------|
| Language | Python 3.10+ | Cross-platform, rich ecosystem |
| GUI Framework | PySide6 | Qt for Python official binding, LGPL license |
| Database | SQLite + SQLAlchemy ORM | Zero configuration, single-file storage |
| Reports/Printing | QPrinter / ReportLab | PDF export and physical printing |
| Import/Export | pandas + openpyxl | Excel/CSV format support |

### 1.2 Project Structure

```
shop-manager/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── database/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy ORM data models
│   └── db.py                  # Database connection & initialization
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Main window (navigation + content area)
│   ├── inventory.py           # Inventory management page
│   ├── order.py               # Order management page
│   ├── service.py             # Customer service ticket page
│   └── widgets.py             # Shared components (dialogs, tables, etc.)
├── utils/
│   ├── __init__.py
│   ├── exporters.py           # Import/export logic
│   └── helpers.py             # Utility functions
└── docs/
    └── specs/
        └── 2026-06-24-shop-manager-design.md
```

---

## 2. Data Models

### 2.1 Products Table (products)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| sku | String(50) | UNIQUE, NOT NULL | Product SKU code |
| name | String(200) | NOT NULL | Product name |
| category | String(100) | DEFAULT 'Uncategorized' | Category |
| price | Float | NOT NULL | Unit price |
| stock | Integer | NOT NULL, DEFAULT 0 | Current stock quantity |
| min_stock | Integer | DEFAULT 10 | Low-stock alert threshold |
| description | Text | | Product description |
| created_at | DateTime | DEFAULT now | Creation timestamp |
| updated_at | DateTime | DEFAULT now, ON UPDATE | Last update timestamp |

### 2.2 Orders Table (orders)

`id` is the internal auto-increment primary key used for database relationships (foreign keys from `order_items` and `tickets` reference this field). `order_no` is the human-readable display identifier (e.g., `ORD202606240001`) shown to users in the UI and used for search/display.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, Auto | Internal primary key (used for FK relationships) |
| order_no | String(50) | UNIQUE, NOT NULL | Human-readable display ID (e.g., ORD202606240001) |
| customer_name | String(100) | NOT NULL | Customer name |
| customer_contact | String(100) | | Contact info |
| total_amount | Float | NOT NULL | Total amount |
| status | String(20) | NOT NULL, DEFAULT 'Pending' | Order status |
| note | Text | | Notes |
| created_at | DateTime | DEFAULT now | Order timestamp |
| updated_at | DateTime | DEFAULT now, ON UPDATE | Last update timestamp |

**Status Enum:** `Pending` → `Shipped` → `Completed` | `Cancelled`

### 2.3 Order Items Table (order_items)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| order_id | Integer | FK → orders.id, NOT NULL | Parent order |
| product_id | Integer | FK → products.id, NOT NULL | Product ID |
| product_name | String(200) | NOT NULL | Product name (snapshot) |
| price | Float | NOT NULL | Unit price (snapshot) |
| quantity | Integer | NOT NULL | Quantity |
| subtotal | Float | NOT NULL | Line total |

### 2.4 Tickets Table (tickets)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| ticket_no | String(50) | UNIQUE, NOT NULL | Human-readable display ID (e.g., TKT202606240001) |
| customer_name | String(100) | NOT NULL | Customer name |
| customer_contact | String(100) | | Contact info |
| order_id | Integer | FK → orders.id, NULLABLE | Linked order |
| subject | String(200) | NOT NULL | Ticket subject |
| description | Text | | Issue description |
| status | String(20) | NOT NULL, DEFAULT 'Open' | Ticket status |
| priority | String(10) | NOT NULL, DEFAULT 'Medium' | Priority level |
| resolution | String(100) | | Resolution method |
| created_at | DateTime | DEFAULT now | Creation timestamp |
| updated_at | DateTime | DEFAULT now, ON UPDATE | Last update timestamp |

**Status Enum:** `Open` → `In Progress` → `Resolved` → `Closed`
**Priority Enum:** `Low` / `Medium` / `High`

### 2.5 Ticket Logs Table (ticket_logs)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| ticket_id | Integer | FK → tickets.id, NOT NULL | Parent ticket |
| content | Text | NOT NULL | Log entry content |
| operator | String(50) | | Operator name |
| created_at | DateTime | DEFAULT now | Log timestamp |

---

## 3. UI Design

### 3.1 Main Window Layout

```
+-----------------------------------------------------------+
| [Title Bar] Personal Shop Manager v1.0          [_][□][×] |
+----------+------------------------------------------------+
| Nav Panel | Content Area (QStackedWidget)                  |
|           |                                                 |
| [📦 Inventory] | Switches between pages based on nav:      |
| [📋 Orders]    |  - InventoryPage                          |
| [💬 Service]   |  - OrderPage                              |
|           |  - ServicePage                                 |
|           |                                                 |
+----------+------------------------------------------------+
| [Status Bar] Products: XX | Orders: XX | Alerts: X         |
+-----------------------------------------------------------+
```

### 3.2 Inventory Page

- **Top Toolbar:** Search box + Category filter dropdown + Low-stock alert filter toggle + "Add Product" button
- **Product Table:** QTableWidget displaying SKU/Name/Category/Stock/Price/Min Stock/Actions
- **Alert Highlighting:** Rows where stock ≤ min_stock shown with red text or yellow background
- **Bottom Summary:** Total products, total inventory value, alert count
- **Context Menu:** Edit, Delete, Copy SKU
- **Import/Export:** Toolbar buttons for Excel/CSV import and export
- **Print:** Support printing product list

### 3.3 Order Page

- **Top Toolbar:** Search box + Status filter + Date filter + "New Order" button
- **Order Table:** Displaying order No./Customer/Amount/Item count/Status/Date/Actions
- **Status Color Tags:** Different statuses shown with distinct color labels
- **Bottom Pagination:** Page navigation support
- **New Order Dialog:**
  - Fill in customer info
  - Select products from inventory (with search), auto-fill name and price
  - Quantity changes auto-calculate line totals and grand total
  - On save: auto-deduct stock; show error if insufficient stock
- **Order Detail Dialog:** Full order info + item details + status change actions
- **Status Changes:** Via context menu or buttons in detail view
  - Cancelling an order auto-restores stock
- **Export/Print:** Export order list to Excel, print order details

### 3.4 Service Page

- **Top Toolbar:** Search box + Status filter + Priority filter + Date filter + "New Ticket" button
- **Ticket Table:** Displaying ticket No./Customer/Subject/Priority/Status/Created/Actions
- **Priority Icons:** 🔴 High 🟡 Medium 🟢 Low
- **New Ticket Dialog:**
  - Fill in customer info
  - Optional: link to an existing order (popup order search dialog)
  - Select priority
  - Fill in subject and description
- **Ticket Detail Panel:** Full ticket info + processing log list
- **Processing Logs:** Add notes during processing
- **Status Transitions:** Open → In Progress → Resolved → Closed; Closed can be reopened
- **Export:** Export ticket list to Excel

---

## 4. Core Business Flows

### 4.1 Create Order → Stock Deduction

```
User fills order → selects products → enters quantities
    ↓
System checks stock availability
    ├── Insufficient → Show error for specific products, block save
    └── Sufficient → Save order → Deduct stock for each product
                      ↓
                    Set order status to "Pending"
```

### 4.2 Cancel Order → Stock Restoration

```
User cancels order → Confirm cancellation
    ↓
System restores stock for all items in the order
    ↓
Update order status to "Cancelled"
```

### 4.3 Ticket Linked to Order

```
Create ticket → Optionally link to an order
    ↓
When order is selected → auto-fill customer name and contact
    ↓
Ticket detail view allows one-click navigation to linked order
```

---

## 5. Error Handling

| Scenario | Handling |
|----------|----------|
| Database file corruption | Detect on startup, prompt backup and rebuild |
| Insufficient stock | Validate on order create/edit, show specific error |
| Delete referenced product | Check for active orders referencing it, block deletion |
| Duplicate SKU | Validate on create/edit, show duplicate error |
| Import file format error | Catch parsing errors, show specific line number error |
| Database operation failure | Global exception handler, rollback transaction, show error dialog |

---

## 6. Data Storage

- Database file: `shop-manager/data/shop.db`
- Auto-create database and tables on first launch
- Import/export files saved to user-selected paths
- Manual database backup via file copy

---

## 7. Future Scope (Not in v1.0)

- Multi-user login with permissions
- Cloud data sync
- Sales analytics charts
- Batch shipping label printing
- Product image management
- Push notifications (email/SMS)