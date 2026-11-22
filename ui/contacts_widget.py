"""
ui/contacts_widget.py
Module « Contacts » (Admin) : carnet centralisé — parents, fournisseurs,
partenaires, autorités scolaires.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QDialog, QFormLayout,
    QTextEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt

from database import get_connection, log_action
from utils import confirm_delete, show_error, validate_phone

CATEGORIES = ["Parent", "Fournisseur", "Partenaire", "Autorité scolaire", "Autre"]


class ContactFormDialog(QDialog):
    def __init__(self, parent=None, contact=None):
        super().__init__(parent)
        self.contact = contact
        self.setWindowTitle("Modifier le contact" if contact else "Ajouter un contact")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name = QLineEdit()
        self.category = QComboBox()
        self.category.addItems(CATEGORIES)
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.address = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(60)

        form.addRow("Nom *", self.name)
        form.addRow("Catégorie", self.category)
        form.addRow("Téléphone", self.phone)
        form.addRow("Email", self.email)
        form.addRow("Adresse", self.address)
        form.addRow("Notes", self.notes)
        layout.addLayout(form)

        if contact:
            self.name.setText(contact["name"])
            self.category.setCurrentText(contact["category"] or "Autre")
            self.phone.setText(contact["phone"] or "")
            self.email.setText(contact["email"] or "")
            self.address.setText(contact["address"] or "")
            self.notes.setPlainText(contact["notes"] or "")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Save).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self):
        if not self.name.text().strip():
            show_error(self, "Le nom du contact est obligatoire.")
            return
        if not validate_phone(self.phone.text().strip()):
            show_error(self, "Le numéro de téléphone est invalide.")
            return

        conn = get_connection()
        data = (
            self.name.text().strip(), self.category.currentText(), self.phone.text().strip(),
            self.email.text().strip(), self.address.text().strip(), self.notes.toPlainText().strip(),
        )
        if self.contact:
            conn.execute(
                "UPDATE contacts SET name=?, category=?, phone=?, email=?, address=?, notes=? WHERE id=?",
                data + (self.contact["id"],),
            )
        else:
            conn.execute(
                "INSERT INTO contacts (name, category, phone, email, address, notes) VALUES (?, ?, ?, ?, ?, ?)",
                data,
            )
        conn.commit()
        self.accept()


class ContactsWidget(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Carnet de contacts")
        title.setProperty("role", "title")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Rechercher un contact…")
        self.search_edit.textChanged.connect(self.refresh)
        self.category_filter = QComboBox()
        self.category_filter.addItem("Toutes les catégories", None)
        for c in CATEGORIES:
            self.category_filter.addItem(c, c)
        self.category_filter.currentIndexChanged.connect(self.refresh)
        add_btn = QPushButton("+ Ajouter un contact")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_contact)
        toolbar.addWidget(self.search_edit, stretch=1)
        toolbar.addWidget(self.category_filter)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nom", "Catégorie", "Téléphone", "Email", "Adresse"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_contact)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        edit_btn = QPushButton("Modifier")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.clicked.connect(self.edit_contact)
        delete_btn = QPushButton("Supprimer")
        delete_btn.setProperty("variant", "danger")
        delete_btn.clicked.connect(self.delete_contact)
        action_row.addWidget(edit_btn)
        action_row.addStretch()
        action_row.addWidget(delete_btn)
        layout.addLayout(action_row)

    def refresh(self):
        conn = get_connection()
        query = "SELECT * FROM contacts WHERE 1=1"
        params = []
        search = self.search_edit.text().strip()
        if search:
            query += " AND name LIKE ?"
            params.append(f"%{search}%")
        category = self.category_filter.currentData()
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY name"

        rows = conn.execute(query, params).fetchall()
        self.table.setRowCount(0)
        for r in rows:
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(r["name"]))
            self.table.setItem(idx, 1, QTableWidgetItem(r["category"] or "-"))
            self.table.setItem(idx, 2, QTableWidgetItem(r["phone"] or "-"))
            self.table.setItem(idx, 3, QTableWidgetItem(r["email"] or "-"))
            self.table.setItem(idx, 4, QTableWidgetItem(r["address"] or "-"))
            self.table.item(idx, 0).setData(Qt.UserRole, r["id"])

    def _selected_contact(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        contact_id = self.table.item(row, 0).data(Qt.UserRole)
        conn = get_connection()
        return conn.execute("SELECT * FROM contacts WHERE id=?", (contact_id,)).fetchone()

    def add_contact(self):
        dlg = ContactFormDialog(self)
        if dlg.exec():
            log_action(self.user, "Contact ajouté", dlg.name.text())
            self.refresh()

    def edit_contact(self):
        contact = self._selected_contact()
        if not contact:
            show_error(self, "Veuillez sélectionner un contact.")
            return
        dlg = ContactFormDialog(self, contact)
        if dlg.exec():
            log_action(self.user, "Contact modifié", contact["name"])
            self.refresh()

    def delete_contact(self):
        contact = self._selected_contact()
        if not contact:
            show_error(self, "Veuillez sélectionner un contact.")
            return
        if confirm_delete(self, f"le contact {contact['name']}"):
            conn = get_connection()
            conn.execute("DELETE FROM contacts WHERE id=?", (contact["id"],))
            conn.commit()
            log_action(self.user, "Contact supprimé", contact["name"])
            self.refresh()
