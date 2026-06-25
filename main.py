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