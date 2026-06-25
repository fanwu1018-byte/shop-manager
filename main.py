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
        QLabel {
            color: #2c3e50;
        }
        QGroupBox {
            font-weight: bold;
            color: #2c3e50;
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #2c3e50;
        }
        QPushButton {
            padding: 6px 14px;
            border-radius: 4px;
            border: 1px solid #2980b9;
            background-color: #3498db;
            color: #ffffff;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #1e6fa0;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            padding: 4px 8px;
            border: 1px solid #bdc3c7;
            border-radius: 3px;
            background-color: #ffffff;
            color: #2c3e50;
        }
        QComboBox::drop-down {
            border: none;
        }
        QTableWidget {
            border: 1px solid #bdc3c7;
            gridline-color: #dfe6e9;
            background-color: #ffffff;
            color: #2c3e50;
        }
        QHeaderView::section {
            background-color: #2c3e50;
            color: #ffffff;
            padding: 6px;
            border: none;
            font-weight: bold;
        }
        QStatusBar {
            background-color: #2c3e50;
            color: #ffffff;
        }
        QMenu {
            background-color: #ffffff;
            color: #2c3e50;
            border: 1px solid #bdc3c7;
        }
        QMenu::item:selected {
            background-color: #3498db;
            color: #ffffff;
        }
        QTextEdit {
            border: 1px solid #bdc3c7;
            border-radius: 3px;
            background-color: #ffffff;
            color: #2c3e50;
        }
    """)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()