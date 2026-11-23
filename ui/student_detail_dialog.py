"""
ui/student_detail_dialog.py
Fiche consultable d'un élève : informations, suivi des paiements (avec reçu),
et suivi des paiements.
"""
import uuid
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QDialogButtonBox, QHeaderView, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QDate

from database import get_connection, log_action
from utils import (
    format_currency, confirm_delete, show_error, build_receipt_html,
    print_html_document, export_html_to_pdf, MOIS_FR
)

MONTHS_ORDER = list(range(1, 13))


class PaymentFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enregistrer un paiement")
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.month = QComboBox()
        for i, m in enumerate(MOIS_FR, start=1):
            self.month.addItem(m, i)
        self.month.setCurrentIndex(datetime.now().month - 1)

        self.year = QSpinBox()
        self.year.setRange(2000, 2100)
        self.year.setValue(datetime.now().year)

        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 10_000_000)
        self.amount.setSuffix(" DA")
        self.amount.setDecimals(2)

        self.payment_date = QDateEdit()
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDisplayFormat("yyyy-MM-dd")
        self.payment_date.setDate(QDate.currentDate())

        self.method = QComboBox()
        self.method.addItems(["Espèces", "Virement", "Chèque", "Autre"])

        form.addRow("Mois", self.month)
        form.addRow("Année", self.year)
        form.addRow("Montant", self.amount)
        form.addRow("Date de paiement", self.payment_date)
        form.addRow("Méthode", self.method)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Save).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class StudentDetailDialog(QDialog):
    def __init__(self, parent, user, student_row, school_name="Alkaouther Academy"):
        super().__init__(parent)
        self.user = user
        self.student = student_row
        self.school_name = school_name
        self.setWindowTitle(f"Fiche — {student_row['first_name']} {student_row['last_name']}")
        self.resize(680, 560)
        self._build_ui()
        self.refresh_payments()
        self.refresh_attendance()

    # ------------------------------------------------------------- helpers
    def _class_name(self):
        conn = get_connection()
        names = [
            row["name"] for row in conn.execute(
                """SELECT cl.name FROM classes cl
                   JOIN student_classes sc ON sc.class_id=cl.id
                   WHERE sc.student_id=? ORDER BY cl.name""",
                (self.student["id"],),
            )
        ]
        if not names and self.student["class_id"]:
            row = conn.execute("SELECT name FROM classes WHERE id=?", (self.student["class_id"],)).fetchone()
            if row:
                names = [row["name"]]
        return ", ".join(names) if names else "-"

    def _build_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel(f"<b>{self.student['first_name']} {self.student['last_name']}</b> — "
                         f"Classe : {self._class_name()} — Statut : {self.student['status']}")
        header.setStyleSheet("font-size:15px; padding:6px;")
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(self._build_info_tab(), "Informations")
        tabs.addTab(self._build_payments_tab(), "Paiements")
        tabs.addTab(self._build_attendance_tab(), "Présences")
        layout.addWidget(tabs)

        close_btn = QPushButton("Fermer")
        close_btn.setProperty("variant", "secondary")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _build_info_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        s = self.student
        form.addRow("Prénom", QLabel(s["first_name"]))
        form.addRow("Nom", QLabel(s["last_name"]))
        form.addRow("Date de naissance", QLabel(s["birth_date"] or "-"))
        form.addRow("Sexe", QLabel(s["sex"] or "-"))
        form.addRow("Classe", QLabel(self._class_name()))
        form.addRow("Parent / tuteur", QLabel(s["parent_name"] or "-"))
        form.addRow("Téléphone parent", QLabel(s["parent_phone"] or "-"))
        form.addRow("Adresse", QLabel(s["parent_address"] or "-"))
        form.addRow("Date d'inscription", QLabel(s["registration_date"] or "-"))
        form.addRow("Année scolaire", QLabel(s["school_year"] or "-"))
        return w

    # ------------------------------------------------------------- présences
    def _build_attendance_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        controls = QHBoxLayout()
        self.attendance_class = QComboBox()
        conn = get_connection()
        class_rows = conn.execute(
            """SELECT cl.id, cl.name FROM classes cl
               JOIN student_classes sc ON sc.class_id=cl.id
               WHERE sc.student_id=? ORDER BY cl.name""",
            (self.student["id"],),
        ).fetchall()
        if not class_rows and self.student["class_id"]:
            class_rows = conn.execute(
                "SELECT id, name FROM classes WHERE id=?", (self.student["class_id"],)
            ).fetchall()
        for row in class_rows:
            self.attendance_class.addItem(row["name"], row["id"])

        self.attendance_month = QComboBox()
        for i, name in enumerate(MOIS_FR, start=1):
            self.attendance_month.addItem(name, i)
        self.attendance_month.setCurrentIndex(datetime.now().month - 1)

        self.attendance_year = QSpinBox()
        self.attendance_year.setRange(2000, 2100)
        self.attendance_year.setValue(datetime.now().year)

        self.session_count = QSpinBox()
        self.session_count.setRange(0, 31)
        self.session_count.setSuffix(" séances")

        save_sessions = QPushButton("Enregistrer les séances")
        save_sessions.setProperty("variant", "primary")
        save_sessions.clicked.connect(self._save_session_count)

        controls.addWidget(QLabel("Classe"))
        controls.addWidget(self.attendance_class)
        controls.addWidget(QLabel("Mois"))
        controls.addWidget(self.attendance_month)
        controls.addWidget(QLabel("Année"))
        controls.addWidget(self.attendance_year)
        controls.addWidget(QLabel("Séances pour cet élève"))
        controls.addWidget(self.session_count)
        controls.addWidget(save_sessions)
        layout.addLayout(controls)

        self.attendance_summary = QLabel("")
        layout.addWidget(self.attendance_summary)

        self.attendance_grid = QGridLayout()
        layout.addLayout(self.attendance_grid)
        layout.addStretch()

        self.attendance_class.currentIndexChanged.connect(self.refresh_attendance)
        self.attendance_month.currentIndexChanged.connect(self.refresh_attendance)
        self.attendance_year.valueChanged.connect(self.refresh_attendance)

        return w

    def refresh_attendance(self):
        if not hasattr(self, "attendance_grid"):
            return
        while self.attendance_grid.count():
            item = self.attendance_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if self.attendance_class.count() == 0:
            self.attendance_summary.setText("Cet élève n'est inscrit à aucune classe.")
            self.session_count.setValue(0)
            return

        conn = get_connection()
        class_id = self.attendance_class.currentData()
        month = self.attendance_month.currentData()
        year = self.attendance_year.value()
        row = conn.execute(
            """SELECT session_count FROM student_month_sessions
               WHERE student_id=? AND class_id=? AND month=? AND year=?""",
            (self.student["id"], class_id, month, year),
        ).fetchone()
        count = row["session_count"] if row else 0
        self.session_count.blockSignals(True)
        self.session_count.setValue(count)
        self.session_count.blockSignals(False)

        checked = {
            r["session_number"] for r in conn.execute(
                """SELECT session_number FROM student_attendance
                   WHERE student_id=? AND class_id=? AND month=? AND year=?""",
                (self.student["id"], class_id, month, year),
            )
        }
        checked_count = 0
        for number in range(1, count + 1):
            checkbox = QCheckBox(f"Séance {number}")
            checkbox.setChecked(number in checked)
            if checkbox.isChecked():
                checked_count += 1
            checkbox.toggled.connect(
                lambda checked, n=number: self._set_attendance(n, checked)
            )
            self.attendance_grid.addWidget(checkbox, (number - 1) // 4, (number - 1) % 4)

        self.attendance_summary.setText(
            f"<b>Présences :</b> {checked_count} sur {count} séance(s)"
        )

    def _save_session_count(self):
        if self.attendance_class.count() == 0:
            show_error(self, "Veuillez inscrire l'élève à une classe.")
            return
        conn = get_connection()
        conn.execute(
            """INSERT INTO student_month_sessions
               (student_id, class_id, month, year, session_count)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(student_id, class_id, month, year)
               DO UPDATE SET session_count=excluded.session_count""",
            (
                self.student["id"],
                self.attendance_class.currentData(),
                self.attendance_month.currentData(),
                self.attendance_year.value(),
                self.session_count.value(),
            ),
        )
        conn.execute(
            """DELETE FROM student_attendance
               WHERE student_id=? AND class_id=? AND month=? AND year=?
                 AND session_number>?""",
            (
                self.student["id"],
                self.attendance_class.currentData(),
                self.attendance_month.currentData(),
                self.attendance_year.value(),
                self.session_count.value(),
            ),
        )
        conn.commit()
        log_action(
            self.user,
            "Séances mensuelles définies",
            f"{self.attendance_class.currentText()} — {self.attendance_month.currentText()} {self.attendance_year.value()}",
        )
        self.refresh_attendance()

    def _set_attendance(self, session_number, checked):
        if self.attendance_class.count() == 0:
            return
        conn = get_connection()
        class_id = self.attendance_class.currentData()
        month = self.attendance_month.currentData()
        year = self.attendance_year.value()
        if checked:
            conn.execute(
                """INSERT OR IGNORE INTO student_attendance
                   (student_id, class_id, month, year, session_number, checked_in_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    self.student["id"], class_id, month, year, session_number,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        else:
            conn.execute(
                """DELETE FROM student_attendance
                   WHERE student_id=? AND class_id=? AND month=? AND year=? AND session_number=?""",
                (self.student["id"], class_id, month, year, session_number),
            )
        conn.commit()
        self.refresh_attendance()

    # ------------------------------------------------------------ paiements
    def _build_payments_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Enregistrer un paiement")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self._add_payment)
        receipt_btn = QPushButton("Imprimer le reçu")
        receipt_btn.setProperty("variant", "secondary")
        receipt_btn.clicked.connect(self._print_receipt)
        pdf_btn = QPushButton("Exporter le reçu en PDF")
        pdf_btn.setProperty("variant", "secondary")
        pdf_btn.clicked.connect(self._export_receipt_pdf)
        del_btn = QPushButton("Supprimer")
        del_btn.setProperty("variant", "danger")
        del_btn.clicked.connect(self._delete_payment)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(receipt_btn)
        btn_row.addWidget(pdf_btn)
        btn_row.addStretch()
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

        self.months_summary = QLabel("")
        layout.addWidget(self.months_summary)

        self.payments_table = QTableWidget(0, 5)
        self.payments_table.setHorizontalHeaderLabels(["Mois", "Année", "Montant", "Date", "Méthode"])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.payments_table)

        return w

    def refresh_payments(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM payments WHERE student_id=? ORDER BY year DESC, month DESC",
            (self.student["id"],),
        ).fetchall()
        self.payments_table.setRowCount(0)
        for r in rows:
            row_idx = self.payments_table.rowCount()
            self.payments_table.insertRow(row_idx)
            self.payments_table.setItem(row_idx, 0, QTableWidgetItem(MOIS_FR[r["month"] - 1]))
            self.payments_table.setItem(row_idx, 1, QTableWidgetItem(str(r["year"])))
            self.payments_table.setItem(row_idx, 2, QTableWidgetItem(format_currency(r["amount"])))
            self.payments_table.setItem(row_idx, 3, QTableWidgetItem(r["payment_date"]))
            self.payments_table.setItem(row_idx, 4, QTableWidgetItem(r["method"] or "-"))
            self.payments_table.item(row_idx, 0).setData(Qt.UserRole, r["id"])

        paid_months = {(r["month"], r["year"]) for r in rows}
        current_year = datetime.now().year
        paid_this_year = sorted(m for (m, y) in paid_months if y == current_year)
        unpaid_this_year = [m for m in MONTHS_ORDER if m not in paid_this_year]
        self.months_summary.setText(
            f"<b>{current_year} — Mois payés :</b> {', '.join(MOIS_FR[m-1] for m in paid_this_year) or 'aucun'}<br>"
            f"<b>Mois non payés :</b> <span style='color:#C0392B'>"
            f"{', '.join(MOIS_FR[m-1] for m in unpaid_this_year) or 'aucun'}</span>"
        )

    def _add_payment(self):
        dlg = PaymentFormDialog(self)
        if dlg.exec():
            conn = get_connection()
            receipt_number = f"RCT-{self.student['id']}-{uuid.uuid4().hex[:6].upper()}"
            conn.execute(
                """INSERT INTO payments (student_id, month, year, amount, payment_date, method, receipt_number)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.student["id"], dlg.month.currentData(), dlg.year.value(),
                    dlg.amount.value(), dlg.payment_date.date().toString("yyyy-MM-dd"),
                    dlg.method.currentText(), receipt_number,
                ),
            )
            conn.commit()
            log_action(self.user, "Paiement ajouté",
                       f"Élève #{self.student['id']} — {dlg.month.currentText()} {dlg.year.value()}")
            self.refresh_payments()

    def _selected_payment_id(self):
        row = self.payments_table.currentRow()
        if row < 0:
            return None
        return self.payments_table.item(row, 0).data(Qt.UserRole)

    def _delete_payment(self):
        pid = self._selected_payment_id()
        if pid is None:
            show_error(self, "Veuillez sélectionner un paiement à supprimer.")
            return
        if confirm_delete(self, "ce paiement"):
            conn = get_connection()
            conn.execute("DELETE FROM payments WHERE id=?", (pid,))
            conn.commit()
            log_action(self.user, "Paiement supprimé", f"Paiement #{pid}")
            self.refresh_payments()

    def _get_selected_payment_row(self):
        pid = self._selected_payment_id()
        if pid is None:
            return None
        conn = get_connection()
        return conn.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()

    def _print_receipt(self):
        payment = self._get_selected_payment_row()
        if not payment:
            show_error(self, "Veuillez sélectionner un paiement pour générer le reçu.")
            return
        student = dict(self.student)
        student["class_name"] = self._class_name()
        html = build_receipt_html(self.school_name, student, payment)
        print_html_document(self, html)

    def _export_receipt_pdf(self):
        payment = self._get_selected_payment_row()
        if not payment:
            show_error(self, "Veuillez sélectionner un paiement pour générer le reçu.")
            return
        student = dict(self.student)
        student["class_name"] = self._class_name()
        html = build_receipt_html(self.school_name, student, payment)
        export_html_to_pdf(self, html, default_name=f"recu_{payment['receipt_number']}.pdf")

