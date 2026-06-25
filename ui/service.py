from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QTextEdit,
    QGroupBox, QMenu, QAbstractItemView, QApplication, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QBrush, QFont
from sqlalchemy.orm import selectinload
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

        self.new_ticket_btn = QPushButton("\u2795 New Ticket")
        self.new_ticket_btn.clicked.connect(self.new_ticket)

        self.export_btn = QPushButton("\U0001f4e4 Export")
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

        tickets = query.options(selectinload(Ticket.order)).order_by(Ticket.id.desc()).all()

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
        session.close()

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
            progress_btn = QPushButton("\u25b6\ufe0f Start Processing")
            progress_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "In Progress", detail_dialog))
            status_layout.addWidget(progress_btn)
        elif ticket.status == "In Progress":
            resolve_btn = QPushButton("\u2705 Mark Resolved")
            resolve_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "Resolved", detail_dialog))
            status_layout.addWidget(resolve_btn)
        elif ticket.status == "Resolved":
            close_btn = QPushButton("\U0001f512 Close Ticket")
            close_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "Closed", detail_dialog))
            reopen_btn = QPushButton("\U0001f504 Reopen")
            reopen_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "Open", detail_dialog))
            status_layout.addWidget(close_btn)
            status_layout.addWidget(reopen_btn)
        elif ticket.status == "Closed":
            reopen_btn = QPushButton("\U0001f504 Reopen")
            reopen_btn.clicked.connect(lambda: self.change_ticket_status(ticket.id, "Open", detail_dialog))
            status_layout.addWidget(reopen_btn)
        detail_dialog.layout.addLayout(status_layout)

        detail_dialog.add_buttons()
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
        detail_action = menu.addAction("\U0001f441\ufe0f View Detail")
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