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

        self.order_page.inventory_changed.connect(self.inventory_page.load_data)

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