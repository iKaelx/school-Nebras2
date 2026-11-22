"""
ui/students_widget.py
Module « Élèves » : liste, recherche/filtres, ajout/modification/suppression,
accès à la fiche détaillée (paiements, absences).
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel
)
from PySide6.QtCore import Qt

from database import get_connection, log_action
from utils import confirm_delete, show_error
from ui.student_form_dialog import StudentFormDialog
from ui.student_detail_dialog import StudentDetailDialog

STATUS_LABELS = {"actif": "Actif", "inactif": "Inactif", "a_quitte": "A quitté"}


class StudentsWidget(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Élèves")
        title.setProperty("role", "title")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Rechercher par nom ou prénom…")
        self.search_edit.textChanged.connect(self.refresh)

        self.class_filter = QComboBox()
        self.class_filter.currentIndexChanged.connect(self.refresh)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Tous les statuts", None)
        for key, label in STATUS_LABELS.items():
            self.status_filter.addItem(label, key)
        self.status_filter.currentIndexChanged.connect(self.refresh)

        add_btn = QPushButton("+ Ajouter un élève")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_student)

        toolbar.addWidget(self.search_edit, stretch=2)
        toolbar.addWidget(self.class_filter, stretch=1)
        toolbar.addWidget(self.status_filter, stretch=1)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Nom", "Prénom", "Classe", "Statut", "Inscription", "Contact parent"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.open_detail)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        detail_btn = QPushButton("Voir la fiche")
        detail_btn.setProperty("variant", "secondary")
        detail_btn.clicked.connect(self.open_detail)
        edit_btn = QPushButton("Modifier")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.clicked.connect(self.edit_student)
        delete_btn = QPushButton("Supprimer")
        delete_btn.setProperty("variant", "danger")
        delete_btn.clicked.connect(self.delete_student)
        action_row.addWidget(detail_btn)
        action_row.addWidget(edit_btn)
        action_row.addStretch()
        action_row.addWidget(delete_btn)
        layout.addLayout(action_row)

    # --------------------------------------------------------------- data
    def _load_class_filter(self):
        current = self.class_filter.currentData()
        self.class_filter.blockSignals(True)
        self.class_filter.clear()
        self.class_filter.addItem("Toutes les classes", None)
        conn = get_connection()
        for row in conn.execute("SELECT id, name FROM classes ORDER BY name"):
            self.class_filter.addItem(row["name"], row["id"])
        idx = self.class_filter.findData(current)
        self.class_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.class_filter.blockSignals(False)

    def refresh(self):
        self._load_class_filter()
        conn = get_connection()
        query = """
            SELECT s.*, c.name AS class_name
            FROM students s LEFT JOIN classes c ON s.class_id = c.id
            WHERE 1=1
        """
        params = []
        search = self.search_edit.text().strip()
        if search:
            query += " AND (s.first_name LIKE ? OR s.last_name LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        class_id = self.class_filter.currentData()
        if class_id:
            query += " AND s.class_id = ?"
            params.append(class_id)
        status = self.status_filter.currentData()
        if status:
            query += " AND s.status = ?"
            params.append(status)
        query += " ORDER BY s.last_name, s.first_name"

        rows = conn.execute(query, params).fetchall()
        self.table.setRowCount(0)
        for r in rows:
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(r["last_name"]))
            self.table.setItem(idx, 1, QTableWidgetItem(r["first_name"]))
            self.table.setItem(idx, 2, QTableWidgetItem(r["class_name"] or "-"))
            self.table.setItem(idx, 3, QTableWidgetItem(STATUS_LABELS.get(r["status"], r["status"])))
            self.table.setItem(idx, 4, QTableWidgetItem(r["registration_date"] or "-"))
            contact = f"{r['parent_name'] or ''} ({r['parent_phone'] or '-'})"
            self.table.setItem(idx, 5, QTableWidgetItem(contact))
            self.table.item(idx, 0).setData(Qt.UserRole, r["id"])

    def _selected_student(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        student_id = self.table.item(row, 0).data(Qt.UserRole)
        conn = get_connection()
        return conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()

    # ------------------------------------------------------------ actions
    def add_student(self):
        dlg = StudentFormDialog(self)
        if dlg.exec():
            log_action(self.user, "Élève ajouté", f"{dlg.first_name.text()} {dlg.last_name.text()}")
            self.refresh()

    def edit_student(self):
        student = self._selected_student()
        if not student:
            show_error(self, "Veuillez sélectionner un élève.")
            return
        dlg = StudentFormDialog(self, student)
        if dlg.exec():
            log_action(self.user, "Élève modifié", f"#{student['id']}")
            self.refresh()

    def delete_student(self):
        student = self._selected_student()
        if not student:
            show_error(self, "Veuillez sélectionner un élève.")
            return
        if confirm_delete(self, f"l'élève {student['first_name']} {student['last_name']}"):
            conn = get_connection()
            conn.execute("DELETE FROM students WHERE id=?", (student["id"],))
            conn.commit()
            log_action(self.user, "Élève supprimé", f"{student['first_name']} {student['last_name']}")
            self.refresh()

    def open_detail(self):
        student = self._selected_student()
        if not student:
            show_error(self, "Veuillez sélectionner un élève.")
            return
        dlg = StudentDetailDialog(self, self.user, student)
        dlg.exec()
        self.refresh()
