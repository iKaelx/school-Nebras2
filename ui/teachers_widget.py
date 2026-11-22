"""
ui/teachers_widget.py
Module « Enseignants » : liste, recherche, ajout/modification/suppression.
Les enseignants n'ont pas de compte de connexion — simples fiches.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel
)
from PySide6.QtCore import Qt

from database import get_connection, log_action
from utils import confirm_delete, show_error, format_currency
from ui.teacher_form_dialog import TeacherFormDialog


class TeachersWidget(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Enseignants")
        title.setProperty("role", "title")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Rechercher par nom, matière…")
        self.search_edit.textChanged.connect(self.refresh)
        add_btn = QPushButton("+ Ajouter un enseignant")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_teacher)
        toolbar.addWidget(self.search_edit, stretch=1)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        columns = ["Nom", "Prénom", "Matière(s)", "Classes", "Téléphone", "Embauche"]
        if self.user["role"] == "admin":
            columns.append("Salaire")
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_teacher)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        edit_btn = QPushButton("Modifier")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.clicked.connect(self.edit_teacher)
        delete_btn = QPushButton("Supprimer")
        delete_btn.setProperty("variant", "danger")
        delete_btn.clicked.connect(self.delete_teacher)
        action_row.addWidget(edit_btn)
        action_row.addStretch()
        action_row.addWidget(delete_btn)
        layout.addLayout(action_row)

    def refresh(self):
        conn = get_connection()
        search = self.search_edit.text().strip()
        query = "SELECT * FROM teachers WHERE 1=1"
        params = []
        if search:
            query += " AND (first_name LIKE ? OR last_name LIKE ? OR subjects LIKE ?)"
            params += [f"%{search}%"] * 3
        query += " ORDER BY last_name, first_name"

        rows = conn.execute(query, params).fetchall()
        self.table.setRowCount(0)
        for r in rows:
            classes = [c["name"] for c in conn.execute(
                """SELECT cl.name FROM classes cl
                   JOIN teacher_classes tc ON tc.class_id = cl.id
                   WHERE tc.teacher_id = ?""", (r["id"],)
            )]
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(r["last_name"]))
            self.table.setItem(idx, 1, QTableWidgetItem(r["first_name"]))
            self.table.setItem(idx, 2, QTableWidgetItem(r["subjects"] or "-"))
            self.table.setItem(idx, 3, QTableWidgetItem(", ".join(classes) or "-"))
            self.table.setItem(idx, 4, QTableWidgetItem(r["phone"] or "-"))
            self.table.setItem(idx, 5, QTableWidgetItem(r["hire_date"] or "-"))
            if self.user["role"] == "admin":
                self.table.setItem(idx, 6, QTableWidgetItem(format_currency(r["salary"])))
            self.table.item(idx, 0).setData(Qt.UserRole, r["id"])

    def _selected_teacher(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        teacher_id = self.table.item(row, 0).data(Qt.UserRole)
        conn = get_connection()
        return conn.execute("SELECT * FROM teachers WHERE id=?", (teacher_id,)).fetchone()

    def add_teacher(self):
        dlg = TeacherFormDialog(self, self.user)
        if dlg.exec():
            log_action(self.user, "Enseignant ajouté", f"{dlg.first_name.text()} {dlg.last_name.text()}")
            self.refresh()

    def edit_teacher(self):
        teacher = self._selected_teacher()
        if not teacher:
            show_error(self, "Veuillez sélectionner un enseignant.")
            return
        dlg = TeacherFormDialog(self, self.user, teacher)
        if dlg.exec():
            log_action(self.user, "Enseignant modifié", f"#{teacher['id']}")
            self.refresh()

    def delete_teacher(self):
        teacher = self._selected_teacher()
        if not teacher:
            show_error(self, "Veuillez sélectionner un enseignant.")
            return
        if confirm_delete(self, f"l'enseignant {teacher['first_name']} {teacher['last_name']}"):
            conn = get_connection()
            conn.execute("DELETE FROM teachers WHERE id=?", (teacher["id"],))
            conn.commit()
            log_action(self.user, "Enseignant supprimé", f"{teacher['first_name']} {teacher['last_name']}")
            self.refresh()
