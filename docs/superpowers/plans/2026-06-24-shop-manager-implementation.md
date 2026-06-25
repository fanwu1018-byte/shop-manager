# Personal Shop Manager — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a desktop application for managing inventory, orders, and customer service tickets for individual online store sellers.

**Architecture:** Single-window PySide6 application with left navigation panel and QStackedWidget content area. SQLite database managed via SQLAlchemy ORM. Three independent page modules (Inventory, Orders, Service) that share the same database session.

**Tech Stack:** Python 3.10+, PySide6, SQLAlchemy 2.0, SQLite, pandas, openpyxl, ReportLab

## Global Constraints

- Python 3.10+ required
- PySide6 (not PyQt5) for GUI
- SQLAlchemy 2.0 ORM with SQLite backend
- Database file stored at `data/shop.db`
- All UI text in English
- No multi-user or cloud features in v1.0

---

### Task 1: Project Scaffolding + Database Models

**Files:**
- Create: `shop-manager/requirements.txt`
- Create: `shop-manager/database/__init__.py`
- Create: `shop-manager/database/models.py`
- Create: `shop-manager/database/db.py`
- Create: `shop-manager/data/.gitkeep`

**Interfaces:**
- Consumes: nothing (foundation task)
- Produces: `Base` (SQLAlchemy declarative base), `Product`, `Order`, `OrderItem`, `Ticket`, `TicketLog` model classes, `get_session()` function returning `Session`, `init_db()` function

- [ ] **Step 1: Create requirements.txt**

```txt
PySide6>=6.6.0
SQLAlchemy>=2.0.0
pandas>=2.0.0
openpyxl>=3.1.0
reportlab>=4.0.0
```

- [ ] **Step 2: Create database/__init__.py**

Empty file.

- [ ] **Step 3: Create database/models.py**

```python
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100), default="Uncategorized")
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    min_stock = Column(Integer, default=10)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    order_items = relationship("OrderItem", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_contact = Column(String(100), default="")
    total_amount = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="Pending")
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="order")

    def __repr__(self):
        return f"<Order(id={self.id}, order_no='{self.order_no}', status='{self.status}')>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, product='{self.product_name}', qty={self.quantity})>"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_no = Column(String(50), unique=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_contact = Column(String(100), default="")
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), nullable=False, default="Open")
    priority = Column(String(10), nullable=False, default="Medium")
    resolution = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    order = relationship("Order", back_populates="tickets")
    logs = relationship("TicketLog", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket(id={self.id}, ticket_no='{self.ticket_no}', status='{self.status}')>"


class TicketLog(Base):
    __tablename__ = "ticket_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    content = Column(Text, nullable=False)
    operator = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.now)

    ticket = relationship("Ticket", back_populates="logs")

    def __repr__(self):
        return f"<TicketLog(id={self.id}, ticket_id={self.ticket_id})>"
```

- [ ] **Step 4: Create database/db.py**

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "shop.db")


def init_db():
    """Initialize the database: create directory, engine, and all tables."""
    os.makedirs(DB_DIR, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session() -> Session:
    """Create and return a new database session."""
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()
```

- [ ] **Step 5: Create data/.gitkeep**

Empty file.

- [ ] **Step 6: Verify models import correctly**

Run: `python -c "from database.models import Product, Order, OrderItem, Ticket, TicketLog; print('Models OK')"`
Expected: `Models OK`

- [ ] **Step 7: Verify database initialization**

Run: `python -c "from database.db import init_db; engine = init_db(); print('DB OK')"`
Expected: `DB OK`

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: add project scaffolding and database models"
```

---

### Task 2: Main Window + Navigation Shell

**Files:**
- Create: `shop-manager/ui/__init__.py`
- Create: `shop-manager/ui/main_window.py`
- Create: `shop-manager/ui/widgets.py`

**Interfaces:**
- Consumes: `get_session()` from `database.db`
- Produces: `MainWindow` class (QMainWindow subclass) with navigation and QStackedWidget, placeholder pages for Inventory/Orders/Service

- [ ] **Step 1: Create ui/__init__.py**

Empty file.

- [ ] **Step 2: Create ui/widgets.py**

```python
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class BaseDialog(QDialog):
    """Base class for all editor dialogs with OK/Cancel buttons."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.layout = QVBoxLayout(self)

    def add_widget(self, widget):
        self.layout.addWidget(widget)

    def add_buttons(self):
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        self.layout.addLayout(btn_layout)


class TableWidget(QTableWidget):
    """Standardized table with sortable columns and stretch behavior."""
    def __init__(self, headers: list, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
```

- [ ] **Step 3: Create ui/main_window.py**

```python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QStatusBar, QLabel, QPushButton,
    QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Shop Manager v1.0")
        self.setMinimumSize(1200, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navigation panel
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(180)
        self.nav_list.setFont(QFont("Segoe UI", 12))
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 10px;
            }
            QListWidget::item {
                padding: 12px 10px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #3498db;
            }
            QListWidget::item:hover {
                background-color: #34495e;
            }
        """)

        self.nav_items = [
            ("📦  Inventory", 0),
            ("📋  Orders", 1),
            ("💬  Service", 2),
        ]
        for text, idx in self.nav_items:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, idx)
            self.nav_list.addItem(item)

        # Content area
        self.content_stack = QStackedWidget()

        # Placeholder pages
        from ui.inventory import InventoryPage
        from ui.order import OrderPage
        from ui.service import ServicePage

        self.inventory_page = InventoryPage()
        self.order_page = OrderPage()
        self.service_page = ServicePage()

        self.content_stack.addWidget(self.inventory_page)  # index 0
        self.content_stack.addWidget(self.order_page)       # index 1
        self.content_stack.addWidget(self.service_page)     # index 2

        # Connect navigation
        self.nav_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        # Assemble layout
        main_layout.addWidget(self.nav_list)
        main_layout.addWidget(self.content_stack, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

    def update_status(self, text: str):
        self.status_label.setText(text)
```

- [ ] **Step 4: Verify main window imports**

Run: `python -c "from ui.main_window import MainWindow; print('MainWindow OK')"`
Expected: `MainWindow OK`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add main window with navigation shell"
```

---

### Task 3: Inventory Module

**Files:**
- Create: `shop-manager/ui/inventory.py`

**Interfaces:**
- Consumes: `Product` model, `get_session()` from `database.db`, `TableWidget`, `BaseDialog` from `ui.widgets`
- Produces: `InventoryPage` class (QWidget subclass) with full CRUD, search, filter, alert highlighting, import/export/print buttons

- [ ] **Step 1: Create ui/inventory.py**

```python
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QTextEdit,
    QDoubleSpinBox, QSpinBox, QMenu, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QBrush, QFont
from database.db import get_session
from database.models import Product
from ui.widgets import TableWidget, BaseDialog
import pandas as pd


class ProductDialog(BaseDialog):
    def __init__(self, title="New Product", product: Product = None, parent=None):
        super().__init__(title, parent)
        self.product = product
        self.setMinimumWidth(450)

        form = QFormLayout()
        self.sku_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self._load_categories()
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setPrefix("$ ")
        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 999999)
        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 999999)
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)

        form.addRow("SKU *:", self.sku_edit)
        form.addRow("Name *:", self.name_edit)
        form.addRow("Category:", self.category_combo)
        form.addRow("Price *:", self.price_spin)
        form.addRow("Stock:", self.stock_spin)
        form.addRow("Min Stock Alert:", self.min_stock_spin)
        form.addRow("Description:", self.desc_edit)

        self.add_widget(form)

        if product:
            self.sku_edit.setText(product.sku)
            self.name_edit.setText(product.name)
            idx = self.category_combo.findText(product.category)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            else:
                self.category_combo.setCurrentText(product.category)
            self.price_spin.setValue(product.price)
            self.stock_spin.setValue(product.stock)
            self.min_stock_spin.setValue(product.min_stock)
            self.desc_edit.setPlainText(product.description or "")

        self.add_buttons()

    def _load_categories(self):
        session = get_session()
        categories = session.query(Product.category).distinct().order_by(Product.category).all()
        session.close()
        self.category_combo.addItems([c[0] for c in categories if c[0]])

    def get_data(self) -> dict:
        return {
            "sku": self.sku_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "category": self.category_combo.currentText().strip() or "Uncategorized",
            "price": self.price_spin.value(),
            "stock": self.stock_spin.value(),
            "min_stock": self.min_stock_spin.value(),
            "description": self.desc_edit.toPlainText().strip(),
        }

    def validate(self) -> bool:
        data = self.get_data()
        if not data["sku"]:
            QMessageBox.warning(self, "Validation Error", "SKU is required.")
            return False
        if not data["name"]:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return False
        if data["price"] <= 0:
            QMessageBox.warning(self, "Validation Error", "Price must be greater than 0.")
            return False
        # Check SKU uniqueness
        session = get_session()
        existing = session.query(Product).filter(Product.sku == data["sku"]).first()
        if existing and (not self.product or existing.id != self.product.id):
            session.close()
            QMessageBox.warning(self, "Validation Error", f"SKU '{data['sku']}' already exists.")
            return False
        session.close()
        return True


class InventoryPage(QWidget):
    alert_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by name or SKU...")
        self.search_edit.textChanged.connect(self.load_data)

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentIndexChanged.connect(self.load_data)

        self.alert_filter_btn = QPushButton("⚠️ Low Stock Only")
        self.alert_filter_btn.setCheckable(True)
        self.alert_filter_btn.toggled.connect(self.load_data)

        self.add_btn = QPushButton("➕ Add Product")
        self.add_btn.clicked.connect(self.add_product)

        self.import_btn = QPushButton("📥 Import")
        self.import_btn.clicked.connect(self.import_products)

        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self.export_products)

        self.print_btn = QPushButton("🖨️ Print")
        self.print_btn.clicked.connect(self.print_products)

        toolbar.addWidget(self.search_edit)
        toolbar.addWidget(self.category_filter)
        toolbar.addWidget(self.alert_filter_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.import_btn)
        toolbar.addWidget(self.export_btn)
        toolbar.addWidget(self.print_btn)
        layout.addLayout(toolbar)

        # Table
        headers = ["ID", "SKU", "Name", "Category", "Stock", "Price", "Min Stock", "Description"]
        self.table = TableWidget(headers)
        self.table.setColumnHidden(0, True)  # Hide ID column
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(self.edit_product)
        layout.addWidget(self.table)

        # Summary bar
        self.summary_label = QLabel("Total: 0 products | Value: $0.00 | Alerts: 0")
        layout.addWidget(self.summary_label)

    def load_data(self):
        session = get_session()
        query = session.query(Product)
        search_text = self.search_edit.text().strip()
        if search_text:
            like = f"%{search_text}%"
            query = query.filter(
                (Product.name.like(like)) | (Product.sku.like(like))
            )
        category = self.category_filter.currentText()
        if category and category != "All Categories":
            query = query.filter(Product.category == category)
        if self.alert_filter_btn.isChecked():
            query = query.filter(Product.stock <= Product.min_stock)
        products = query.order_by(Product.id.desc()).all()
        session.close()

        # Update category filter
        self._update_category_filter()

        self.table.setRowCount(0)
        total_value = 0
        alert_count = 0
        for p in products:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.table.setItem(row, 1, QTableWidgetItem(p.sku))
            self.table.setItem(row, 2, QTableWidgetItem(p.name))
            self.table.setItem(row, 3, QTableWidgetItem(p.category))
            self.table.setItem(row, 4, QTableWidgetItem(str(p.stock)))
            self.table.setItem(row, 5, QTableWidgetItem(f"${p.price:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(str(p.min_stock)))
            self.table.setItem(row, 7, QTableWidgetItem(p.description or ""))

            # Highlight low stock
            if p.stock <= p.min_stock:
                alert_count += 1
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setForeground(QBrush(QColor("#e74c3c")))
                        item.setFont(QFont("", -1, QFont.Bold))

            total_value += p.price * p.stock

        self.summary_label.setText(
            f"Total: {len(products)} products | Value: ${total_value:.2f} | Alerts: {alert_count}"
        )
        self.alert_updated.emit()

    def _update_category_filter(self):
        session = get_session()
        categories = session.query(Product.category).distinct().order_by(Product.category).all()
        session.close()
        current = self.category_filter.currentText()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")
        for (cat,) in categories:
            if cat:
                self.category_filter.addItem(cat)
        idx = self.category_filter.findText(current)
        if idx >= 0:
            self.category_filter.setCurrentIndex(idx)
        self.category_filter.blockSignals(False)

    def add_product(self):
        dialog = ProductDialog("New Product", parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.validate():
            data = dialog.get_data()
            session = get_session()
            product = Product(**data)
            session.add(product)
            session.commit()
            session.close()
            self.load_data()

    def edit_product(self):
        row = self.table.currentRow()
        if row < 0:
            return
        product_id = int(self.table.item(row, 0).text())
        session = get_session()
        product = session.query(Product).get(product_id)
        if not product:
            session.close()
            return
        dialog = ProductDialog("Edit Product", product=product, parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.validate():
            data = dialog.get_data()
            for key, value in data.items():
                setattr(product, key, value)
            product.updated_at = datetime.now()
            session.commit()
            session.close()
            self.load_data()
        else:
            session.close()

    def delete_product(self):
        row = self.table.currentRow()
        if row < 0:
            return
        product_id = int(self.table.item(row, 0).text())
        product_name = self.table.item(row, 2).text()
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{product_name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        session = get_session()
        product = session.query(Product).get(product_id)
        if product:
            # Check for active order references
            active_count = session.query(OrderItem).filter(
                OrderItem.product_id == product_id
            ).count()
            if active_count > 0:
                QMessageBox.warning(
                    self, "Cannot Delete",
                    f"'{product_name}' is referenced by {active_count} order item(s). Remove those orders first."
                )
                session.close()
                return
            session.delete(product)
            session.commit()
        session.close()
        self.load_data()

    def show_context_menu(self, pos):
        row = self.table.currentRow()
        if row < 0:
            return
        menu = QMenu()
        edit_action = menu.addAction("✏️ Edit")
        delete_action = menu.addAction("🗑️ Delete")
        copy_action = menu.addAction("📋 Copy SKU")
        action = menu.exec(self.table.mapToGlobal(pos))
        if action == edit_action:
            self.edit_product()
        elif action == delete_action:
            self.delete_product()
        elif action == copy_action:
            sku = self.table.item(row, 1).text()
            QApplication.clipboard().setText(sku)

    def import_products(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Products", "", "Excel/CSV (*.xlsx *.csv)"
        )
        if not file_path:
            return
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            required = {"sku", "name", "price"}
            if not required.issubset(df.columns):
                QMessageBox.warning(
                    self, "Import Error",
                    f"File must contain columns: {', '.join(required)}"
                )
                return
            session = get_session()
            imported = 0
            skipped = 0
            for _, row_data in df.iterrows():
                existing = session.query(Product).filter(
                    Product.sku == str(row_data["sku"])
                ).first()
                if existing:
                    skipped += 1
                    continue
                product = Product(
                    sku=str(row_data["sku"]),
                    name=str(row_data["name"]),
                    category=str(row_data.get("category", "Uncategorized")),
                    price=float(row_data["price"]),
                    stock=int(row_data.get("stock", 0)),
                    min_stock=int(row_data.get("min_stock", 10)),
                    description=str(row_data.get("description", "")),
                )
                session.add(product)
                imported += 1
            session.commit()
            session.close()
            QMessageBox.information(
                self, "Import Complete",
                f"Imported: {imported} products\nSkipped (duplicate SKU): {skipped}"
            )
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import: {str(e)}")

    def export_products(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Products", "products_export.xlsx", "Excel (*.xlsx);;CSV (*.csv)"
        )
        if not file_path:
            return
        session = get_session()
        products = session.query(Product).order_by(Product.id).all()
        session.close()
        data = [
            {
                "sku": p.sku, "name": p.name, "category": p.category,
                "price": p.price, "stock": p.stock, "min_stock": p.min_stock,
                "description": p.description
            }
            for p in products
        ]
        df = pd.DataFrame(data)
        try:
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Export Complete", f"Exported {len(products)} products.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")

    def print_products(self):
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        from PySide6.QtGui import QTextDocument
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QDialog.Accepted:
            return
        session = get_session()
        products = session.query(Product).order_by(Product.category, Product.name).all()
        session.close()
        html = """
        <h1 style="text-align:center;">Product List</h1>
        <table border="1" cellpadding="5" style="width:100%; border-collapse:collapse;">
        <tr style="background:#2c3e50; color:white;">
            <th>SKU</th><th>Name</th><th>Category</th><th>Stock</th><th>Price</th>
        </tr>
        """
        for p in products:
            html += f"<tr><td>{p.sku}</td><td>{p.name}</td><td>{p.category}</td><td>{p.stock}</td><td>${p.price:.2f}</td></tr>"
        html += "</table>"
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)
```

- [ ] **Step 2: Verify inventory module imports**

Run: `python -c "from ui.inventory import InventoryPage; print('InventoryPage OK')"`
Expected: `InventoryPage OK`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: add inventory module with CRUD, search, filter, import/export"
```

---

### Task 4: Order Module

**Files:**
- Create: `shop-manager/ui/order.py`

**Interfaces:**
- Consumes: `Order`, `OrderItem`, `Product` models, `get_session()`, `TableWidget`, `BaseDialog`
- Produces: `OrderPage` class (QWidget subclass) with order creation, status management, stock deduction/restoration, search/filter, export/print

- [ ] **Step 1: Create ui/order.py**

```python
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QTextEdit,
    QSpinBox, QDoubleSpinBox, QDateEdit, QGroupBox, QMenu,
    QAbstractItemView, QApplication
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QAction, QColor, QBrush, QFont
from database.db import get_session
from database.models import Order, OrderItem, Product
from ui.widgets import TableWidget, BaseDialog
import pandas as pd


class OrderItemRow(QWidget):
    """A single row in the order items list within the new order dialog."""
    removed = Signal()

    def __init__(self, product: Product, parent=None):
        super().__init__(parent)
        self.product = product
        self.quantity = 1
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel(product.name)
        self.price_label = QLabel(f"${product.price:.2f}")
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.valueChanged.connect(self.update_subtotal)
        self.subtotal_label = QLabel(f"${product.price:.2f}")
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedWidth(30)
        self.remove_btn.clicked.connect(self.removed.emit)

        layout.addWidget(self.name_label, 2)
        layout.addWidget(self.price_label, 1)
        layout.addWidget(QLabel("Qty:"))
        layout.addWidget(self.qty_spin)
        layout.addWidget(self.subtotal_label, 1)
        layout.addWidget(self.remove_btn)

    def update_subtotal(self):
        self.quantity = self.qty_spin.value()
        self.subtotal_label.setText(f"${self.product.price * self.quantity:.2f}")

    def get_subtotal(self) -> float:
        return self.product.price * self.quantity


class NewOrderDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__("New Order", parent)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.item_rows = []

        # Customer info
        customer_group = QGroupBox("Customer Information")
        customer_layout = QFormLayout(customer_group)
        self.customer_name_edit = QLineEdit()
        self.customer_contact_edit = QLineEdit()
        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(60)
        customer_layout.addRow("Name *:", self.customer_name_edit)
        customer_layout.addRow("Contact:", self.customer_contact_edit)
        customer_layout.addRow("Note:", self.note_edit)
        self.add_widget(customer_group)

        # Product selection
        product_group = QGroupBox("Order Items")
        product_layout = QVBoxLayout(product_group)
        product_search_layout = QHBoxLayout()
        self.product_search_edit = QLineEdit()
        self.product_search_edit.setPlaceholderText("Search products...")
        self.product_search_edit.textChanged.connect(self.search_products)
        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(300)
        self.add_product_btn = QPushButton("➕ Add")
        self.add_product_btn.clicked.connect(self.add_product_row)
        product_search_layout.addWidget(self.product_search_edit)
        product_search_layout.addWidget(self.product_combo)
        product_search_layout.addWidget(self.add_product_btn)
        product_layout.addLayout(product_search_layout)

        self.items_container = QVBoxLayout()
        product_layout.addLayout(self.items_container)
        self.add_widget(product_group)

        # Total
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setFont(QFont("", 14, QFont.Bold))
        self.add_widget(self.total_label)

        self.add_buttons()
        self.load_products()

    def load_products(self, search=""):
        session = get_session()
        query = session.query(Product)
        if search:
            like = f"%{search}%"
            query = query.filter(
                (Product.name.like(like)) | (Product.sku.like(like))
            )
        products = query.order_by(Product.name).all()
        session.close()
        self.product_combo.clear()
        self.product_combo.addItem("-- Select Product --", None)
        for p in products:
            self.product_combo.addItem(f"{p.sku} - {p.name} (Stock: {p.stock})", p)

    def search_products(self, text):
        self.load_products(text)

    def add_product_row(self):
        product = self.product_combo.currentData()
        if not product:
            return
        # Check not already added
        for row in self.item_rows:
            if row.product.id == product.id:
                QMessageBox.information(self, "Already Added", f"'{product.name}' is already in the list.")
                return
        row = OrderItemRow(product)
        row.removed.connect(lambda: self.remove_product_row(row))
        self.item_rows.append(row)
        self.items_container.addWidget(row)
        self.update_total()

    def remove_product_row(self, row):
        self.item_rows.remove(row)
        self.items_container.removeWidget(row)
        row.deleteLater()
        self.update_total()

    def update_total(self):
        total = sum(r.get_subtotal() for r in self.item_rows)
        self.total_label.setText(f"Total: ${total:.2f}")

    def get_data(self) -> dict:
        return {
            "customer_name": self.customer_name_edit.text().strip(),
            "customer_contact": self.customer_contact_edit.text().strip(),
            "note": self.note_edit.toPlainText().strip(),
            "items": [
                {
                    "product": r.product,
                    "quantity": r.quantity,
                }
                for r in self.item_rows
            ],
        }

    def validate(self) -> bool:
        data = self.get_data()
        if not data["customer_name"]:
            QMessageBox.warning(self, "Validation Error", "Customer name is required.")
            return False
        if not data["items"]:
            QMessageBox.warning(self, "Validation Error", "At least one product is required.")
            return False
        # Check stock
        session = get_session()
        for item in data["items"]:
            product = session.query(Product).get(item["product"].id)
            if product and product.stock < item["quantity"]:
                session.close()
                QMessageBox.warning(
                    self, "Insufficient Stock",
                    f"'{product.name}' only has {product.stock} in stock, but {item['quantity']} requested."
                )
                return False
        session.close()
        return True


class OrderPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by order no. or customer...")
        self.search_edit.textChanged.connect(self.load_data)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Pending", "Shipped", "Completed", "Cancelled"])
        self.status_filter.currentIndexChanged.connect(self.load_data)

        self.date_filter = QComboBox()
        self.date_filter.addItems(["All Time", "Today", "This Week", "This Month"])
        self.date_filter.currentIndexChanged.connect(self.load_data)

        self.new_order_btn = QPushButton("➕ New Order")
        self.new_order_btn.clicked.connect(self.new_order)

        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self.export_orders)

        toolbar.addWidget(self.search_edit)
        toolbar.addWidget(self.status_filter)
        toolbar.addWidget(self.date_filter)
        toolbar.addStretch()
        toolbar.addWidget(self.new_order_btn)
        toolbar.addWidget(self.export_btn)
        layout.addLayout(toolbar)

        # Table
        headers = ["ID", "Order No.", "Customer", "Contact", "Amount", "Items", "Status", "Date", "Note"]
        self.table = TableWidget(headers)
        self.table.setColumnHidden(0, True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(self.show_order_detail)
        layout.addWidget(self.table)

        # Summary
        self.summary_label = QLabel("Total: 0 orders | Revenue: $0.00")
        layout.addWidget(self.summary_label)

    def load_data(self):
        session = get_session()
        query = session.query(Order)
        search_text = self.search_edit.text().strip()
        if search_text:
            like = f"%{search_text}%"
            query = query.filter(
                (Order.order_no.like(like)) | (Order.customer_name.like(like))
            )
        status = self.status_filter.currentText()
        if status and status != "All Status":
            query = query.filter(Order.status == status)

        date_range = self.date_filter.currentText()
        now = datetime.now()
        if date_range == "Today":
            start = datetime(now.year, now.month, now.day)
            query = query.filter(Order.created_at >= start)
        elif date_range == "This Week":
            start = now - __import__("datetime").timedelta(days=now.weekday())
            start = datetime(start.year, start.month, start.day)
            query = query.filter(Order.created_at >= start)
        elif date_range == "This Month":
            start = datetime(now.year, now.month, 1)
            query = query.filter(Order.created_at >= start)

        orders = query.order_by(Order.id.desc()).all()
        session.close()

        self.table.setRowCount(0)
        total_revenue = 0
        status_colors = {
            "Pending": "#f39c12",
            "Shipped": "#3498db",
            "Completed": "#27ae60",
            "Cancelled": "#e74c3c",
        }
        for o in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(o.id)))
            self.table.setItem(row, 1, QTableWidgetItem(o.order_no))
            self.table.setItem(row, 2, QTableWidgetItem(o.customer_name))
            self.table.setItem(row, 3, QTableWidgetItem(o.customer_contact))
            self.table.setItem(row, 4, QTableWidgetItem(f"${o.total_amount:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{len(o.items)} item(s)"))
            status_item = QTableWidgetItem(o.status)
            color = status_colors.get(o.status, "#000000")
            status_item.setForeground(QBrush(QColor(color)))
            status_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(row, 6, status_item)
            self.table.setItem(row, 7, QTableWidgetItem(o.created_at.strftime("%Y-%m-%d %H:%M")))
            self.table.setItem(row, 8, QTableWidgetItem(o.note or ""))
            total_revenue += o.total_amount

        self.summary_label.setText(
            f"Total: {len(orders)} orders | Revenue: ${total_revenue:.2f}"
        )

    def new_order(self):
        dialog = NewOrderDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.validate():
            data = dialog.get_data()
            session = get_session()

            # Generate order number
            today = datetime.now().strftime("%Y%m%d")
            count = session.query(Order).filter(
                Order.order_no.like(f"ORD{today}%")
            ).count()
            order_no = f"ORD{today}{count + 1:04d}"

            order = Order(
                order_no=order_no,
                customer_name=data["customer_name"],
                customer_contact=data["customer_contact"],
                note=data["note"],
                status="Pending",
            )
            session.add(order)
            session.flush()

            total = 0
            for item in data["items"]:
                product = session.query(Product).get(item["product"].id)
                subtotal = product.price * item["quantity"]
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name=product.name,
                    price=product.price,
                    quantity=item["quantity"],
                    subtotal=subtotal,
                )
                session.add(order_item)
                # Deduct stock
                product.stock -= item["quantity"]
                total += subtotal

            order.total_amount = total
            session.commit()
            session.close()
            self.load_data()

    def show_order_detail(self):
        row = self.table.currentRow()
        if row < 0:
            return
        order_id = int(self.table.item(row, 0).text())
        session = get_session()
        order = session.query(Order).get(order_id)
        if not order:
            session.close()
            return

        detail_dialog = BaseDialog(f"Order Detail - {order.order_no}", self)
        detail_dialog.setMinimumWidth(600)

        info = QLabel(
            f"<b>Order No:</b> {order.order_no}<br>"
            f"<b>Customer:</b> {order.customer_name} ({order.customer_contact})<br>"
            f"<b>Status:</b> {order.status}<br>"
            f"<b>Date:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}<br>"
            f"<b>Note:</b> {order.note or 'N/A'}"
        )
        info.setWordWrap(True)
        detail_dialog.add_widget(info)

        items_table = TableWidget(["Product", "Price", "Qty", "Subtotal"])
        for item in order.items:
            r = items_table.rowCount()
            items_table.insertRow(r)
            items_table.setItem(r, 0, QTableWidgetItem(item.product_name))
            items_table.setItem(r, 1, QTableWidgetItem(f"${item.price:.2f}"))
            items_table.setItem(r, 2, QTableWidgetItem(str(item.quantity)))
            items_table.setItem(r, 3, QTableWidgetItem(f"${item.subtotal:.2f}"))
        detail_dialog.add_widget(items_table)

        total_label = QLabel(f"<b>Total: ${order.total_amount:.2f}</b>")
        total_label.setFont(QFont("", 12, QFont.Bold))
        detail_dialog.add_widget(total_label)

        # Status change buttons
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        if order.status == "Pending":
            ship_btn = QPushButton("🚚 Mark Shipped")
            ship_btn.clicked.connect(lambda: self.change_status(order.id, "Shipped", detail_dialog))
            cancel_btn = QPushButton("❌ Cancel Order")
            cancel_btn.clicked.connect(lambda: self.change_status(order.id, "Cancelled", detail_dialog))
            status_layout.addWidget(ship_btn)
            status_layout.addWidget(cancel_btn)
        elif order.status == "Shipped":
            complete_btn = QPushButton("✅ Mark Completed")
            complete_btn.clicked.connect(lambda: self.change_status(order.id, "Completed", detail_dialog))
            status_layout.addWidget(complete_btn)
        detail_dialog.layout.addLayout(status_layout)

        detail_dialog.save_btn.setText("Close")
        detail_dialog.save_btn.clicked.disconnect()
        detail_dialog.save_btn.clicked.connect(detail_dialog.accept)
        detail_dialog.cancel_btn.setVisible(False)
        detail_dialog.exec()
        session.close()

    def change_status(self, order_id: int, new_status: str, dialog: QDialog):
        session = get_session()
        order = session.query(Order).get(order_id)
        if not order:
            session.close()
            return

        if new_status == "Cancelled" and order.status != "Cancelled":
            reply = QMessageBox.question(
                dialog, "Confirm Cancel",
                "Cancel this order? Stock will be restored.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                session.close()
                return
            # Restore stock
            for item in order.items:
                product = session.query(Product).get(item.product_id)
                if product:
                    product.stock += item.quantity

        order.status = new_status
        order.updated_at = datetime.now()
        session.commit()
        session.close()
        dialog.accept()
        self.load_data()

    def show_context_menu(self, pos):
        row = self.table.currentRow()
        if row < 0:
            return
        menu = QMenu()
        detail_action = menu.addAction("👁️ View Detail")
        print_action = menu.addAction("🖨️ Print")
        action = menu.exec(self.table.mapToGlobal(pos))
        if action == detail_action:
            self.show_order_detail()
        elif action == print_action:
            self.print_order()

    def print_order(self):
        row = self.table.currentRow()
        if row < 0:
            return
        order_id = int(self.table.item(row, 0).text())
        session = get_session()
        order = session.query(Order).get(order_id)
        if not order:
            session.close()
            return
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        from PySide6.QtGui import QTextDocument
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QDialog.Accepted:
            session.close()
            return
        items_html = ""
        for item in order.items:
            items_html += f"<tr><td>{item.product_name}</td><td>${item.price:.2f}</td><td>{item.quantity}</td><td>${item.subtotal:.2f}</td></tr>"
        html = f"""
        <h1 style="text-align:center;">Order #{order.order_no}</h1>
        <p><b>Customer:</b> {order.customer_name} | {order.customer_contact}</p>
        <p><b>Status:</b> {order.status} | <b>Date:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}</p>
        <table border="1" cellpadding="5" style="width:100%; border-collapse:collapse;">
        <tr style="background:#2c3e50; color:white;"><th>Product</th><th>Price</th><th>Qty</th><th>Subtotal</th></tr>
        {items_html}
        <tr><td colspan="3" style="text-align:right;"><b>Total</b></td><td><b>${order.total_amount:.2f}</b></td></tr>
        </table>
        """
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)
        session.close()

    def export_orders(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Orders", "orders_export.xlsx", "Excel (*.xlsx);;CSV (*.csv)"
        )
        if not file_path:
            return
        session = get_session()
        orders = session.query(Order).order_by(Order.id.desc()).all()
        session.close()
        data = []
        for o in orders:
            data.append({
                "order_no": o.order_no, "customer": o.customer_name,
                "contact": o.customer_contact, "amount": o.total_amount,
                "status": o.status, "date": o.created_at.strftime("%Y-%m-%d %H:%M"),
                "items": len(o.items), "note": o.note or ""
            })
        df = pd.DataFrame(data)
        try:
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Export Complete", f"Exported {len(orders)} orders.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
```

- [ ] **Step 2: Verify order module imports**

Run: `python -c "from ui.order import OrderPage; print('OrderPage OK')"`
Expected: `OrderPage OK`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: add order module with creation, status management, stock sync"
```

---

### Task 5: Service (Customer Service) Module

**Files:**
- Create: `shop-manager/ui/service.py`

**Interfaces:**
- Consumes: `Ticket`, `TicketLog`, `Order` models, `get_session()`, `TableWidget`, `BaseDialog`
- Produces: `ServicePage` class (QWidget subclass) with ticket CRUD, status management, processing logs, order linking, search/filter, export

- [ ] **Step 1: Create ui/service.py**

```python
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QTextEdit,
    QGroupBox, QMenu, QAbstractItemView, QApplication, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QBrush, QFont
from database.db import get_session
from database.models import Ticket, TicketLog, Order
from ui.widgets import TableWidget, BaseDialog
import pandas as pd


class TicketDialog(BaseDialog):
    def __init__(self, title="New Ticket", ticket: Ticket = None, parent=None):
        super().__init__(title, parent)
        self.ticket = ticket
        self.setMinimumWidth(550)

        form = QFormLayout()
        self.customer_name_edit = QLineEdit()
        self.customer_contact_edit = QLineEdit()
        self.order_combo = QComboBox()
        self.order_combo.addItem("-- None --", None)
        self._load_orders()
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        self.subject_edit = QLineEdit()
        self.desc_edit = QTextEdit()

        form.addRow("Customer Name *:", self.customer_name_edit)
        form.addRow("Contact:", self.customer_contact_edit)
        form.addRow("Linked Order:", self.order_combo)
        form.addRow("Priority:", self.priority_combo)
        form.addRow("Subject *:", self.subject_edit)
        form.addRow("Description:", self.desc_edit)

        self.add_widget(form)

        if ticket:
            self.customer_name_edit.setText(ticket.customer_name)
            self.customer_contact_edit.setText(ticket.customer_contact)
            if ticket.order_id:
                idx = self.order_combo.findData(ticket.order_id)
                if idx >= 0:
                    self.order_combo.setCurrentIndex(idx)
            self.priority_combo.setCurrentText(ticket.priority)
            self.subject_edit.setText(ticket.subject)
            self.desc_edit.setPlainText(ticket.description or "")

        self.add_buttons()

    def _load_orders(self):
        session = get_session()
        orders = session.query(Order).order_by(Order.id.desc()).limit(100).all()
        session.close()
        for o in orders:
            self.order_combo.addItem(f"{o.order_no} - {o.customer_name}", o.id)

    def get_data(self) -> dict:
        return {
            "customer_name": self.customer_name_edit.text().strip(),
            "customer_contact": self.customer_contact_edit.text().strip(),
            "order_id": self.order_combo.currentData(),
            "priority": self.priority_combo.currentText(),
            "subject": self.subject_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
        }

    def validate(self) -> bool:
        data = self.get_data()
        if not data["customer_name"]:
            QMessageBox.warning(self, "Validation Error", "Customer name is required.")
            return False
        if not data["subject"]:
            QMessageBox.warning(self, "Validation Error", "Subject is required.")
            return False
        return True


class ServicePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by ticket no., customer, or subject...")
        self.search_edit.textChanged.connect(self.load_data)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Open", "In Progress", "Resolved", "Closed"])
        self.status_filter.currentIndexChanged.connect(self.load_data)

        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All Priority", "Low", "Medium", "High"])
        self.priority_filter.currentIndexChanged.connect(self.load_data)

        self.new_ticket_btn = QPushButton("➕ New Ticket")
        self.new_ticket_btn.clicked.connect(self.new_ticket)

        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self.export_tickets)

        toolbar.addWidget(self.search_edit)
        toolbar.addWidget(self.status_filter)
        toolbar.addWidget(self.priority_filter)
        toolbar.addStretch()
        toolbar.addWidget(self.new_ticket_btn)
        toolbar.addWidget(self.export_btn)
        layout.addLayout(toolbar)

        # Table
        headers = ["ID", "Ticket No.", "Customer", "Subject", "Priority", "Status", "Order", "Date"]
        self.table = TableWidget(headers)
        self.table.setColumnHidden(0, True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(self.show_ticket_detail)
        layout.addWidget(self.table)

        # Summary
        self.summary_label = QLabel("Total: 0 tickets | Open: 0")
        layout.addWidget(self.summary_label)

    def load_data(self):
        session = get_session()
        query = session.query(Ticket)
        search_text = self.search_edit.text().strip()
        if search_text:
            like = f"%{search_text}%"
            query = query.filter(
                (Ticket.ticket_no.like(like)) |
                (Ticket.customer_name.like(like)) |
                (Ticket.subject.like(like))
            )
        status = self.status_filter.currentText()
        if status and status != "All Status":
            query = query.filter(Ticket.status == status)
        priority = self.priority_filter.currentText()
        if priority and priority != "All Priority":
            query = query.filter(Ticket.priority == priority)

        tickets = query.order_by(Ticket.id.desc()).all()
        session.close()

        self.table.setRowCount(0)
        open_count = 0
        priority_colors = {"High": "#e74c3c", "Medium": "#f39c12", "Low": "#27ae60"}
        status_colors = {"Open": "#e74c3c", "In Progress": "#3498db", "Resolved": "#27ae60", "Closed": "#95a5a6"}

        for t in tickets:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(t.id)))
            self.table.setItem(row, 1, QTableWidgetItem(t.ticket_no))
            self.table.setItem(row, 2, QTableWidgetItem(t.customer_name))
            self.table.setItem(row, 3, QTableWidgetItem(t.subject))

            priority_item = QTableWidgetItem(t.priority)
            p_color = priority_colors.get(t.priority, "#000000")
            priority_item.setForeground(QBrush(QColor(p_color)))
            priority_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(row, 4, priority_item)

            status_item = QTableWidgetItem(t.status)
            s_color = status_colors.get(t.status, "#000000")
            status_item.setForeground(QBrush(QColor(s_color)))
            status_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(row, 5, status_item)

            order_text = t.order.order_no if t.order else "-"
            self.table.setItem(row, 6, QTableWidgetItem(order_text))
            self.table.setItem(row, 7, QTableWidgetItem(t.created_at.strftime("%Y-%m-%d %H:%M")))

            if t.status in ("Open", "In Progress"):
                open_count += 1

        self.summary_label.setText(
            f"Total: {len(tickets)} tickets | Open/In Progress: {open_count}"
        )

    def new_ticket(self):
        dialog = TicketDialog("New Ticket", parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.validate():
            data = dialog.get_data()
            session = get_session()

            today = datetime.now().strftime("%Y%m%d")
            count = session.query(Ticket).filter(
                Ticket.ticket_no.like(f"TKT{today}%")
            ).count()
            ticket_no = f"TKT{today}{count + 1:04d}"

            ticket = Ticket(
                ticket_no=ticket_no,
                customer_name=data["customer_name"],
                customer_contact=data["customer_contact"],
                order_id=data["order_id"],
                priority=data["priority"],
                subject=data["subject"],
                description=data["description"],
                status="Open",
            )
            session.add(ticket)
            session.commit()
            session.close()
            self.load_data()

    def show_ticket_detail(self):
        row = self.table.currentRow()
        if row < 0:
            return
        ticket_id = int(self.table.item(row, 0).text())
        session = get_session()
        ticket = session.query(Ticket).get(ticket_id)
        if not ticket:
            session.close()
            return

        detail_dialog = BaseDialog(f"Ticket Detail - {ticket.ticket_no}", self)
        detail_dialog.setMinimumWidth(650)
        detail_dialog.setMinimumHeight(500)

        # Info
        order_link = ticket.order.order_no if ticket.order else "N/A"
        info = QLabel(
            f"<b>Ticket No:</b> {ticket.ticket_no}<br>"
            f"<b>Customer:</b> {ticket.customer_name} ({ticket.customer_contact})<br>"
            f"<b>Subject:</b> {ticket.subject}<br>"
            f"<b>Priority:</b> {ticket.priority} | <b>Status:</b> {ticket.status}<br>"
            f"<b>Linked Order:</b> {order_link}<br>"
            f"<b>Date:</b> {ticket.created_at.strftime('%Y-%m-%d %H:%M')}<br>"
            f"<b>Description:</b><br>{ticket.description or 'N/A'}"
        )
        info.setWordWrap(True)
        detail_dialog.add_widget(info)

        # Processing logs
        logs_group = QGroupBox("Processing Logs")
        logs_layout = QVBoxLayout(logs_group)
        self.logs_table = TableWidget(["Date", "Operator", "Content"])
        for log in ticket.logs:
            r = self.logs_table.rowCount()
            self.logs_table.insertRow(r)
            self.logs_table.setItem(r, 0, QTableWidgetItem(log.created_at.strftime("%Y-%m-%d %H:%M")))
            self.logs_table.setItem(r, 1, QTableWidgetItem(log.operator or "-"))
            self.logs_table.setItem(r, 2, QTableWidgetItem(log.content))
        logs_layout.addWidget(self.logs_table)

        # Add log input
        log_input_layout = QHBoxLayout()
        self.log_operator_edit = QLineEdit()
        self.log_operator_edit.setPlaceholderText("Operator")
        self.log_content_edit = QLineEdit()
        self.log_content_edit.setPlaceholderText("Add a processing note...")
        self.add_log_btn = QPushButton("Add Log")
        self.add_log_btn.clicked.connect(
            lambda: self.add_ticket_log(ticket.id, detail_dialog)
        )
        log_input_layout.addWidget(self.log_operator_edit)
        log_input_layout.addWidget(self.log_content_edit, 1)
        log_input_layout.addWidget(self.add_log_btn)
        logs_layout.addLayout(log_input_layout)
        detail_dialog.add_widget(logs_group)

        # Status change buttons
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        if ticket.status == "Open":
            progress_btn = QPushButton("▶️ Start Processing")
            progress_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "In Progress", detail_dialog))
            status_layout.addWidget(progress_btn)
        elif ticket.status == "In Progress":
            resolve_btn = QPushButton("✅ Mark Resolved")
            resolve_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "Resolved", detail_dialog))
            status_layout.addWidget(resolve_btn)
        elif ticket.status == "Resolved":
            close_btn = QPushButton("🔒 Close Ticket")
            close_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "Closed", detail_dialog))
            reopen_btn = QPushButton("🔄 Reopen")
            reopen_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "Open", detail_dialog))
            status_layout.addWidget(close_btn)
            status_layout.addWidget(reopen_btn)
        elif ticket.status == "Closed":
            reopen_btn = QPushButton("🔄 Reopen")
            reopen_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "Open", detail_dialog))
            status_layout.addWidget(reopen_btn)
        detail_dialog.layout.addLayout(status_layout)

        detail_dialog.save_btn.setText("Close")
        detail_dialog.save_btn.clicked.disconnect()
        detail_dialog.save_btn.clicked.connect(detail_dialog.accept)
        detail_dialog.cancel_btn.setVisible(False)
        detail_dialog.exec()
        session.close()

    def add_ticket_log(self, ticket_id: int, dialog: QDialog):
        content = self.log_content_edit.text().strip()
        operator = self.log_operator_edit.text().strip()
        if not content:
            return
        session = get_session()
        log = TicketLog(
            ticket_id=ticket_id,
            content=content,
            operator=operator or "Unknown",
        )
        session.add(log)
        session.commit()
        session.close()
        self.log_content_edit.clear()
        dialog.accept()
        self.show_ticket_detail()

    def change_ticket_status(self, ticket_id: int, new_status: str, dialog: QDialog):
        session = get_session()
        ticket = session.query(Ticket).get(ticket_id)
        if ticket:
            ticket.status = new_status
            ticket.updated_at = datetime.now()
            session.commit()
        session.close()
        dialog.accept()
        self.load_data()

    def show_context_menu(self, pos):
        row = self.table.currentRow()
        if row < 0:
            return
        menu = QMenu()
        detail_action = menu.addAction("👁️ View Detail")
        action = menu.exec(self.table.mapToGlobal(pos))
        if action == detail_action:
            self.show_ticket_detail()

    def export_tickets(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Tickets", "tickets_export.xlsx", "Excel (*.xlsx);;CSV (*.csv)"
        )
        if not file_path:
            return
        session = get_session()
        tickets = session.query(Ticket).order_by(Ticket.id.desc()).all()
        session.close()
        data = []
        for t in tickets:
            data.append({
                "ticket_no": t.ticket_no, "customer": t.customer_name,
                "contact": t.customer_contact, "subject": t.subject,
                "priority": t.priority, "status": t.status,
                "order": t.order.order_no if t.order else "",
                "date": t.created_at.strftime("%Y-%m-%d %H:%M"),
            })
        df = pd.DataFrame(data)
        try:
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Export Complete", f"Exported {len(tickets)} tickets.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
```

- [ ] **Step 2: Verify service module imports**

Run: `python -c "from ui.service import ServicePage; print('ServicePage OK')"`
Expected: `ServicePage OK`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: add customer service ticket module"
```

---

### Task 6: Main Entry Point + Integration

**Files:**
- Create: `shop-manager/main.py`

**Interfaces:**
- Consumes: `MainWindow` from `ui.main_window`, `init_db()` from `database.db`
- Produces: Runnable application

- [ ] **Step 1: Create main.py**

```python
import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from database.db import init_db
from ui.main_window import MainWindow


def main():
    # Initialize database
    try:
        init_db()
    except Exception as e:
        QMessageBox.critical(
            None, "Database Error",
            f"Failed to initialize database: {str(e)}\n\n"
            "Please check that the data directory is writable."
        )
        sys.exit(1)

    # Create application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set global stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f6fa;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #dcdde1;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QPushButton {
            padding: 6px 14px;
            border-radius: 4px;
            border: 1px solid #bdc3c7;
            background-color: #ecf0f1;
        }
        QPushButton:hover {
            background-color: #dfe6e9;
        }
        QPushButton:pressed {
            background-color: #b2bec3;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            padding: 4px 8px;
            border: 1px solid #dcdde1;
            border-radius: 3px;
        }
        QTableWidget {
            border: 1px solid #dcdde1;
            gridline-color: #ecf0f1;
        }
        QHeaderView::section {
            background-color: #2c3e50;
            color: white;
            padding: 6px;
            border: none;
            font-weight: bold;
        }
    """)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the application to verify it starts**

Run: `cd /d C:\Users\fanwu\OneDrive\Documents\PythonProjects\shop-manager && python main.py`
Expected: Application window opens with navigation panel and inventory page. Close the window manually.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: add main entry point and application integration"
```

---

### Task 7: Final Verification

- [ ] **Step 1: Verify all imports work**

Run: `python -c "from database.models import Product, Order, OrderItem, Ticket, TicketLog; from database.db import get_session; from ui.main_window import MainWindow; from ui.inventory import InventoryPage; from ui.order import OrderPage; from ui.service import ServicePage; print('All imports OK')"`
Expected: `All imports OK`

- [ ] **Step 2: Verify database initialization**

Run: `python -c "from database.db import init_db; init_db(); print('DB init OK')"`
Expected: `DB init OK`

- [ ] **Step 3: Verify data/shop.db was created**

Run: `dir data\shop.db`
Expected: File exists

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: finalize project setup"