"""
ui/finances_widget.py
Module « Gestion financière » (Admin) : total des paiements, élèves en retard,
dépenses de l'école, bilan, export.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QComboBox, QSpinBox, QDialog, QFormLayout,
    QLineEdit, QDoubleSpinBox, QDateEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt, QDate

from database import get_connection, log_action
from utils import format_currency, confirm_delete, show_error, export_rows_to_csv

MOIS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
           "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]


class ExpenseFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter une dépense")
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.description = QLineEdit()
        self.category = QComboBox()
        self.category.setEditable(True)
        self.category.addItems(["Salaires", "Charges", "Fournitures", "Entretien", "Autre"])
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 100_000_000)
        self.amount.setSuffix(" DA")
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("yyyy-MM-dd")
        self.date.setDate(QDate.currentDate())

        form.addRow("Description *", self.description)
        form.addRow("Catégorie", self.category)
        form.addRow("Montant", self.amount)
        form.addRow("Date", self.date)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Save).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self):
        if not self.description.text().strip():
            show_error(self, "La description est obligatoire.")
            return
        self.accept()


class FinancesWidget(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Gestion financière")
        title.setProperty("role", "title")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_revenue_tab(), "Revenus & impayés")
        tabs.addTab(self._build_expenses_tab(), "Dépenses")
        layout.addWidget(tabs)
        self.tabs = tabs

    # ------------------------------------------------------------ revenus
    def _build_revenue_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        filter_row = QHBoxLayout()
        self.year_filter = QSpinBox()
        self.year_filter.setRange(2000, 2100)
        self.year_filter.setValue(datetime.now().year)
        self.year_filter.valueChanged.connect(self.refresh)
        filter_row.addWidget(QLabel("Année :"))
        filter_row.addWidget(self.year_filter)
        filter_row.addStretch()
        export_btn = QPushButton("Exporter les impayés (CSV)")
        export_btn.setProperty("variant", "secondary")
        export_btn.clicked.connect(self._export_unpaid)
        filter_row.addWidget(export_btn)
        layout.addLayout(filter_row)

        self.total_label = QLabel("")
        self.total_label.setStyleSheet("font-size:15px; font-weight:bold; padding:8px;")
        layout.addWidget(self.total_label)

        layout.addWidget(QLabel("<b>Élèves en retard de paiement (mois en cours)</b>"))
        self.unpaid_table = QTableWidget(0, 3)
        self.unpaid_table.setHorizontalHeaderLabels(["Élève", "Classe", "Contact parent"])
        self.unpaid_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.unpaid_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.unpaid_table.setAlternatingRowColors(True)
        layout.addWidget(self.unpaid_table)

        return w

    def _build_expenses_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        add_btn = QPushButton("+ Ajouter une dépense")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_expense)
        export_btn = QPushButton("Exporter (CSV)")
        export_btn.setProperty("variant", "secondary")
        export_btn.clicked.connect(self._export_expenses)
        del_btn = QPushButton("Supprimer")
        del_btn.setProperty("variant", "danger")
        del_btn.clicked.connect(self.delete_expense)
        toolbar.addWidget(export_btn)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(del_btn)
        layout.addLayout(toolbar)

        self.expenses_table = QTableWidget(0, 4)
        self.expenses_table.setHorizontalHeaderLabels(["Description", "Catégorie", "Montant", "Date"])
        self.expenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expenses_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.expenses_table.setAlternatingRowColors(True)
        layout.addWidget(self.expenses_table)

        self.expenses_total_label = QLabel("")
        self.expenses_total_label.setStyleSheet("font-weight:bold; padding:6px;")
        layout.addWidget(self.expenses_total_label)

        return w

    # -------------------------------------------------------------- data
    def refresh(self):
        conn = get_connection()
        year = self.year_filter.value()
        total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM payments WHERE year=?", (year,)
        ).fetchone()["s"]
        self.total_label.setText(f"Total des paiements reçus en {year} : {format_currency(total)}")

        now = datetime.now()
        current_month = now.month
        self.unpaid_table.setRowCount(0)
        for s in conn.execute("SELECT * FROM students WHERE status='actif' ORDER BY last_name"):
            paid = conn.execute(
                "SELECT COUNT(*) c FROM payments WHERE student_id=? AND month=? AND year=?",
                (s["id"], current_month, year),
            ).fetchone()["c"]
            if paid == 0:
                class_row = conn.execute("SELECT name FROM classes WHERE id=?", (s["class_id"],)).fetchone()
                idx = self.unpaid_table.rowCount()
                self.unpaid_table.insertRow(idx)
                self.unpaid_table.setItem(idx, 0, QTableWidgetItem(f"{s['first_name']} {s['last_name']}"))
                self.unpaid_table.setItem(idx, 1, QTableWidgetItem(class_row["name"] if class_row else "-"))
                self.unpaid_table.setItem(idx, 2, QTableWidgetItem(f"{s['parent_name'] or ''} ({s['parent_phone'] or '-'})"))

        # dépenses
        self.expenses_table.setRowCount(0)
        rows = conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
        total_expenses = 0
        for r in rows:
            idx = self.expenses_table.rowCount()
            self.expenses_table.insertRow(idx)
            self.expenses_table.setItem(idx, 0, QTableWidgetItem(r["description"]))
            self.expenses_table.setItem(idx, 1, QTableWidgetItem(r["category"] or "-"))
            self.expenses_table.setItem(idx, 2, QTableWidgetItem(format_currency(r["amount"])))
            self.expenses_table.setItem(idx, 3, QTableWidgetItem(r["date"]))
            self.expenses_table.item(idx, 0).setData(Qt.UserRole, r["id"])
            total_expenses += r["amount"]
        self.expenses_total_label.setText(f"Total des dépenses : {format_currency(total_expenses)}")

    def add_expense(self):
        dlg = ExpenseFormDialog(self)
        if dlg.exec():
            conn = get_connection()
            conn.execute(
                "INSERT INTO expenses (description, category, amount, date) VALUES (?, ?, ?, ?)",
                (dlg.description.text().strip(), dlg.category.currentText(),
                 dlg.amount.value(), dlg.date.date().toString("yyyy-MM-dd")),
            )
            conn.commit()
            log_action(self.user, "Dépense ajoutée", dlg.description.text())
            self.refresh()

    def delete_expense(self):
        row = self.expenses_table.currentRow()
        if row < 0:
            show_error(self, "Veuillez sélectionner une dépense.")
            return
        expense_id = self.expenses_table.item(row, 0).data(Qt.UserRole)
        if confirm_delete(self, "cette dépense"):
            conn = get_connection()
            conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
            conn.commit()
            log_action(self.user, "Dépense supprimée", f"#{expense_id}")
            self.refresh()

    def _export_unpaid(self):
        headers = ["Élève", "Classe", "Contact parent"]
        rows = []
        for r in range(self.unpaid_table.rowCount()):
            rows.append([self.unpaid_table.item(r, c).text() for c in range(3)])
        export_rows_to_csv(self, headers, rows, default_name="eleves_impayes.csv")

    def _export_expenses(self):
        headers = ["Description", "Catégorie", "Montant", "Date"]
        rows = []
        for r in range(self.expenses_table.rowCount()):
            rows.append([self.expenses_table.item(r, c).text() for c in range(4)])
        export_rows_to_csv(self, headers, rows, default_name="depenses.csv")
