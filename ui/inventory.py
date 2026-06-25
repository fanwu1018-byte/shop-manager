from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QTextEdit,
    QDoubleSpinBox, QSpinBox, QMenu, QAbstractItemView, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QBrush, QFont
from database.db import get_session
from database.models import Product, OrderItem
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

        self.alert_filter_btn = QPushButton("\u26a0\ufe0f Low Stock Only")
        self.alert_filter_btn.setCheckable(True)
        self.alert_filter_btn.toggled.connect(self.load_data)

        self.add_btn = QPushButton("\u2795 Add Product")
        self.add_btn.clicked.connect(self.add_product)

        self.import_btn = QPushButton("\U0001f4e5 Import")
        self.import_btn.clicked.connect(self.import_products)

        self.export_btn = QPushButton("\U0001f4e4 Export")
        self.export_btn.clicked.connect(self.export_products)

        self.print_btn = QPushButton("\U0001f5a8\ufe0f Print")
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
        edit_action = menu.addAction("\u270f\ufe0f Edit")
        delete_action = menu.addAction("\U0001f5d1\ufe0f Delete")
        copy_action = menu.addAction("\U0001f4cb Copy SKU")
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