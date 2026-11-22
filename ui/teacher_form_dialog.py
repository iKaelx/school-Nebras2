"""
ui/teacher_form_dialog.py
Boîte de dialogue d'ajout / modification d'une fiche enseignant.
Le salaire n'est visible/modifiable que par l'Admin.
"""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDateEdit, QDialogButtonBox, QVBoxLayout,
    QDoubleSpinBox, QListWidget, QListWidgetItem, QLabel
)
from PySide6.QtCore import QDate, Qt

from database import get_connection
from utils import validate_phone, show_error


class TeacherFormDialog(QDialog):
    def __init__(self, parent=None, user=None, teacher=None):
        super().__init__(parent)
        self.user = user
        self.teacher = teacher
        self.setWindowTitle("Modifier l'enseignant" if teacher else "Ajouter un enseignant")
        self.setMinimumWidth(420)
        self._build_ui()
        if teacher:
            self._load_teacher(teacher)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.phone = QLineEdit()
        self.address = QLineEdit()
        self.email = QLineEdit()
        self.subjects = QLineEdit()
        self.subjects.setPlaceholderText("ex. Mathématiques, Physique")

        self.hire_date = QDateEdit()
        self.hire_date.setCalendarPopup(True)
        self.hire_date.setDisplayFormat("yyyy-MM-dd")
        self.hire_date.setDate(QDate.currentDate())

        self.classes_list = QListWidget()
        self.classes_list.setSelectionMode(QListWidget.MultiSelection)
        conn = get_connection()
        for row in conn.execute("SELECT id, name FROM classes ORDER BY name"):
            item = QListWidgetItem(row["name"])
            item.setData(Qt.UserRole, row["id"])
            self.classes_list.addItem(item)

        form.addRow("Prénom *", self.first_name)
        form.addRow("Nom *", self.last_name)
        form.addRow("Téléphone", self.phone)
        form.addRow("Adresse", self.address)
        form.addRow("Email", self.email)
        form.addRow("Matière(s)", self.subjects)
        form.addRow("Date d'embauche", self.hire_date)
        form.addRow("Classe(s) assignée(s)", self.classes_list)

        if self.user and self.user["role"] == "admin":
            self.salary = QDoubleSpinBox()
            self.salary.setRange(0, 10_000_000)
            self.salary.setSuffix(" DA")
            form.addRow("Salaire (visible Admin)", self.salary)
        else:
            self.salary = None
            form.addRow(QLabel("<i>Le salaire est visible uniquement par l'administrateur.</i>"))

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Save).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_teacher(self, teacher):
        self.first_name.setText(teacher["first_name"])
        self.last_name.setText(teacher["last_name"])
        self.phone.setText(teacher["phone"] or "")
        self.address.setText(teacher["address"] or "")
        self.email.setText(teacher["email"] or "")
        self.subjects.setText(teacher["subjects"] or "")
        if teacher["hire_date"]:
            self.hire_date.setDate(QDate.fromString(teacher["hire_date"], "yyyy-MM-dd"))
        if self.salary is not None:
            self.salary.setValue(teacher["salary"] or 0)

        conn = get_connection()
        assigned = {r["class_id"] for r in conn.execute(
            "SELECT class_id FROM teacher_classes WHERE teacher_id=?", (teacher["id"],)
        )}
        for i in range(self.classes_list.count()):
            item = self.classes_list.item(i)
            if item.data(Qt.UserRole) in assigned:
                item.setSelected(True)

    def _on_save(self):
        if not self.first_name.text().strip() or not self.last_name.text().strip():
            show_error(self, "Le prénom et le nom sont obligatoires.")
            return
        if not validate_phone(self.phone.text().strip()):
            show_error(self, "Le numéro de téléphone est invalide.")
            return

        conn = get_connection()
        salary_value = self.salary.value() if self.salary is not None else (
            self.teacher["salary"] if self.teacher else 0
        )
        data = (
            self.first_name.text().strip(), self.last_name.text().strip(),
            self.phone.text().strip(), self.address.text().strip(),
            self.email.text().strip(), self.subjects.text().strip(),
            self.hire_date.date().toString("yyyy-MM-dd"), salary_value,
        )

        if self.teacher:
            conn.execute(
                """UPDATE teachers SET first_name=?, last_name=?, phone=?, address=?, email=?,
                   subjects=?, hire_date=?, salary=? WHERE id=?""",
                data + (self.teacher["id"],),
            )
            teacher_id = self.teacher["id"]
        else:
            cur = conn.execute(
                """INSERT INTO teachers (first_name, last_name, phone, address, email, subjects,
                   hire_date, salary) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                data,
            )
            teacher_id = cur.lastrowid

        conn.execute("DELETE FROM teacher_classes WHERE teacher_id=?", (teacher_id,))
        for item in self.classes_list.selectedItems():
            conn.execute(
                "INSERT OR IGNORE INTO teacher_classes (teacher_id, class_id) VALUES (?, ?)",
                (teacher_id, item.data(Qt.UserRole)),
            )
        conn.commit()
        self.accept()
