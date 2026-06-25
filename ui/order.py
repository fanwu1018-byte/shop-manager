from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QTextEdit,
    QSpinBox, QGroupBox, QMenu, QAbstractItemView, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QBrush, QFont
from sqlalchemy.orm import selectinload
from database.db import get_session
from database.models import Order, OrderItem, Product
from ui.widgets import TableWidget, BaseDialog
import pandas as pd


class OrderItemRow(QWidget):
    """A single row in the order items list within the new order dialog."""
    removed = Signal()

    def __init__(self, product: Product, quantity: int = 1, parent=None):
        super().__init__(parent)
        self.product = product
        self.quantity = quantity
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel(product.name)
        self.price_label = QLabel(f"${product.price:.2f}")
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setValue(quantity)
        self.qty_spin.valueChanged.connect(self.update_subtotal)
        self.subtotal_label = QLabel(f"${product.price * quantity:.2f}")
        self.remove_btn = QPushButton("\u2715")
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
    def __init__(self, parent=None, order: Order = None):
        super().__init__("Edit Order" if order else "New Order", parent)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.order = order
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
        self.add_product_btn = QPushButton("\u2795 Add")
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
        if order:
            self._load_order(order)

    def _load_order(self, order: Order):
        self.customer_name_edit.setText(order.customer_name)
        self.customer_contact_edit.setText(order.customer_contact or "")
        self.note_edit.setPlainText(order.note or "")
        for item in order.items:
            if item.product:
                product = item.product
            else:
                product = Product(
                    id=item.product_id,
                    sku="",
                    name=item.product_name,
                    price=item.price,
                    stock=0,
                    min_stock=0,
                )
            row = OrderItemRow(product, quantity=item.quantity)
            row.removed.connect(lambda r=row: self.remove_product_row(r))
            self.item_rows.append(row)
            self.items_container.addWidget(row)
        self.update_total()

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
        row.removed.connect(lambda r=row: self.remove_product_row(r))
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

    def validate_with_available_stock(self, available_by_product_id: dict) -> bool:
        data = self.get_data()
        if not data["customer_name"]:
            QMessageBox.warning(self, "Validation Error", "Customer name is required.")
            return False
        if not data["items"]:
            QMessageBox.warning(self, "Validation Error", "At least one product is required.")
            return False
        requested = {}
        for item in data["items"]:
            product_id = item["product"].id
            requested[product_id] = requested.get(product_id, 0) + item["quantity"]
        for product_id, quantity in requested.items():
            available = available_by_product_id.get(product_id, 0)
            if quantity > available:
                QMessageBox.warning(
                    self,
                    "Insufficient Stock",
                    f"Product ID {product_id} has {available} available after restoring the old order, but {quantity} requested."
                )
                return False
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

        self.new_order_btn = QPushButton("\u2795 New Order")
        self.new_order_btn.clicked.connect(self.new_order)

        self.export_btn = QPushButton("\U0001f4e4 Export")
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
            start = now - timedelta(days=now.weekday())
            start = datetime(start.year, start.month, start.day)
            query = query.filter(Order.created_at >= start)
        elif date_range == "This Month":
            start = datetime(now.year, now.month, 1)
            query = query.filter(Order.created_at >= start)

        orders = query.options(selectinload(Order.items)).order_by(Order.id.desc()).all()

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
        session.close()

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

    def edit_order(self):
        row = self.table.currentRow()
        if row < 0:
            return
        order_id = int(self.table.item(row, 0).text())
        session = get_session()
        order = session.query(Order).options(
            selectinload(Order.items).selectinload(OrderItem.product)
        ).get(order_id)
        if not order:
            session.close()
            return
        if order.status == "Completed":
            reply = QMessageBox.question(
                self,
                "Edit Completed Order",
                "This order is completed. Editing it will update item details and inventory. Continue?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                session.close()
                return

        dialog = NewOrderDialog(self, order=order)
        if dialog.exec() == QDialog.Accepted:
            # Restore stock from the old order first if this order currently reserves/deducts stock.
            stock_was_deducted = order.status != "Cancelled"
            if stock_was_deducted:
                for old_item in order.items:
                    product = session.query(Product).get(old_item.product_id)
                    if product:
                        product.stock += old_item.quantity
                session.flush()

            data = dialog.get_data()
            available_by_product_id = {
                p.id: p.stock
                for p in session.query(Product).filter(
                    Product.id.in_([item["product"].id for item in data["items"]])
                ).all()
            }
            if not dialog.validate_with_available_stock(available_by_product_id):
                session.rollback()
                session.close()
                return

            order.customer_name = data["customer_name"]
            order.customer_contact = data["customer_contact"]
            order.note = data["note"]
            order.updated_at = datetime.now()
            order.items.clear()
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
                order.items.append(order_item)
                if stock_was_deducted:
                    product.stock -= item["quantity"]
                total += subtotal

            order.total_amount = total
            session.commit()
            session.close()
            self.load_data()
        else:
            session.close()

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
        edit_btn = QPushButton("✏️ Edit Order")
        edit_btn.clicked.connect(lambda: (detail_dialog.accept(), self.edit_order()))
        status_layout.addWidget(edit_btn)
        if order.status == "Pending":
            ship_btn = QPushButton("\U0001f69a Mark Shipped")
            ship_btn.clicked.connect(lambda: self.change_status(order.id, "Shipped", detail_dialog))
            cancel_btn = QPushButton("\u274c Cancel Order")
            cancel_btn.clicked.connect(lambda: self.change_status(order.id, "Cancelled", detail_dialog))
            status_layout.addWidget(ship_btn)
            status_layout.addWidget(cancel_btn)
        elif order.status == "Shipped":
            complete_btn = QPushButton("\u2705 Mark Completed")
            complete_btn.clicked.connect(lambda: self.change_status(order.id, "Completed", detail_dialog))
            status_layout.addWidget(complete_btn)
        detail_dialog.layout.addLayout(status_layout)

        detail_dialog.add_buttons()
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
        detail_action = menu.addAction("\U0001f441\ufe0f View Detail")
        edit_action = menu.addAction("✏️ Edit Order")
        print_action = menu.addAction("\U0001f5a8\ufe0f Print")
        action = menu.exec(self.table.mapToGlobal(pos))
        if action == detail_action:
            self.show_order_detail()
        elif action == edit_action:
            self.edit_order()
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
        orders = session.query(Order).options(selectinload(Order.items)).order_by(Order.id.desc()).all()
        data = []
        for o in orders:
            data.append({
                "order_no": o.order_no, "customer": o.customer_name,
                "contact": o.customer_contact, "amount": o.total_amount,
                "status": o.status, "date": o.created_at.strftime("%Y-%m-%d %H:%M"),
                "items": len(o.items), "note": o.note or ""
            })
        session.close()
        df = pd.DataFrame(data)
        try:
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Export Complete", f"Exported {len(orders)} orders.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")