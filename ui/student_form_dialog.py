"""
ui/student_form_dialog.py
Boîte de dialogue d'ajout / modification d'une fiche élève.
"""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, QDialogButtonBox,
    QVBoxLayout, QLabel, QFileDialog, QHBoxLayout, QPushButton
)
from PySide6.QtCore import QDate

from database import get_connection, get_current_school_year
from utils import validate_phone, show_error


class StudentFormDialog(QDialog):
    def __init__(self, parent=None, student=None):
        super().__init__(parent)
        self.student = student  # sqlite3.Row ou None si création
        self.photo_path = student["photo_path"] if student else None
        self.setWindowTitle("Modifier l'élève" if student else "Ajouter un élève")
        self.setMinimumWidth(420)
        self._build_ui()
        if student:
            self._load_student(student)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDisplayFormat("yyyy-MM-dd")
        self.birth_date.setDate(QDate(2015, 1, 1))

        self.sex = QComboBox()
        self.sex.addItems(["", "M", "F"])

        self.class_combo = QComboBox()
        self._load_classes()

        self.parent_name = QLineEdit()
        self.parent_phone = QLineEdit()
        self.parent_address = QLineEdit()

        self.registration_date = QDateEdit()
        self.registration_date.setCalendarPopup(True)
        self.registration_date.setDisplayFormat("yyyy-MM-dd")
        self.registration_date.setDate(QDate.currentDate())

        self.status = QComboBox()
        self.status.addItems(["actif", "inactif", "a_quitte"])

        photo_row = QHBoxLayout()
        self.photo_label = QLabel("Aucune photo")
        photo_btn = QPushButton("Choisir une photo…")
        photo_btn.setProperty("variant", "secondary")
        photo_btn.clicked.connect(self._choose_photo)
        photo_row.addWidget(self.photo_label)
        photo_row.addWidget(photo_btn)

        form.addRow("Prénom *", self.first_name)
        form.addRow("Nom *", self.last_name)
        form.addRow("Date de naissance", self.birth_date)
        form.addRow("Sexe", self.sex)
        form.addRow("Classe", self.class_combo)
        form.addRow("Photo (optionnel)", photo_row)
        form.addRow(QLabel("<b>Parent / tuteur</b>"))
        form.addRow("Nom du parent", self.parent_name)
        form.addRow("Téléphone", self.parent_phone)
        form.addRow("Adresse", self.parent_address)
        form.addRow("Date d'inscription", self.registration_date)
        form.addRow("Statut", self.status)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Save).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_classes(self):
        conn = get_connection()
        self.class_combo.addItem("— Aucune —", None)
        for row in conn.execute("SELECT id, name FROM classes ORDER BY name"):
            self.class_combo.addItem(row["name"], row["id"])

    def _choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir une photo", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.photo_path = path
            self.photo_label.setText(path.split("/")[-1])

    def _load_student(self, student):
        self.first_name.setText(student["first_name"])
        self.last_name.setText(student["last_name"])
        if student["birth_date"]:
            self.birth_date.setDate(QDate.fromString(student["birth_date"], "yyyy-MM-dd"))
        self.sex.setCurrentText(student["sex"] or "")
        if student["class_id"]:
            idx = self.class_combo.findData(student["class_id"])
            if idx >= 0:
                self.class_combo.setCurrentIndex(idx)
        self.parent_name.setText(student["parent_name"] or "")
        self.parent_phone.setText(student["parent_phone"] or "")
        self.parent_address.setText(student["parent_address"] or "")
        if student["registration_date"]:
            self.registration_date.setDate(QDate.fromString(student["registration_date"], "yyyy-MM-dd"))
        self.status.setCurrentText(student["status"])
        if student["photo_path"]:
            self.photo_label.setText(student["photo_path"].split("/")[-1])

    def _on_save(self):
        if not self.first_name.text().strip() or not self.last_name.text().strip():
            show_error(self, "Le prénom et le nom sont obligatoires.")
            return
        if not validate_phone(self.parent_phone.text().strip()):
            show_error(self, "Le numéro de téléphone du parent est invalide.")
            return

        conn = get_connection()
        data = (
            self.first_name.text().strip(),
            self.last_name.text().strip(),
            self.birth_date.date().toString("yyyy-MM-dd"),
            self.sex.currentText(),
            self.photo_path,
            self.class_combo.currentData(),
            self.parent_name.text().strip(),
            self.parent_phone.text().strip(),
            self.parent_address.text().strip(),
            self.registration_date.date().toString("yyyy-MM-dd"),
            self.status.currentText(),
        )

        if self.student:
            conn.execute(
                """UPDATE students SET first_name=?, last_name=?, birth_date=?, sex=?, photo_path=?,
                   class_id=?, parent_name=?, parent_phone=?, parent_address=?, registration_date=?, status=?
                   WHERE id=?""",
                data + (self.student["id"],),
            )
        else:
            conn.execute(
                """INSERT INTO students (first_name, last_name, birth_date, sex, photo_path, class_id,
                   parent_name, parent_phone, parent_address, registration_date, status, school_year)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                data + (get_current_school_year(),),
            )
        conn.commit()
        self.accept()
