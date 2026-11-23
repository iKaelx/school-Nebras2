"""
ui/classes_widget.py
Module « Classes / Niveaux » : ajout/modification/suppression, capacité,
nombre d'élèves inscrits par classe.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QDialog, QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox
)
from PySide6.QtCore import Qt

from database import get_connection, log_action
from utils import confirm_delete, show_error


class ClassFormDialog(QDialog):
    def __init__(self, parent=None, class_row=None):
        super().__init__(parent)
        self.class_row = class_row
        self.setWindowTitle("Modifier la classe" if class_row else "Ajouter une classe")
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name = QLineEdit()
        self.name.setPlaceholderText("ex. 6ème A, CP, Terminale S…")
        self.level = QLineEdit()
        self.level.setPlaceholderText("ex. Collège, Primaire…")
        self.capacity = QSpinBox()
        self.capacity.setRange(0, 200)
        self.capacity.setSpecialValueText("Non définie")

        form.addRow("Nom de la classe *", self.name)
        form.addRow("Niveau", self.level)
        form.addRow("Capacité maximale", self.capacity)
        layout.addLayout(form)

        if class_row:
            self.name.setText(class_row["name"])
            self.level.setText(class_row["level"] or "")
            self.capacity.setValue(class_row["capacity"] or 0)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Save).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self):
        if not self.name.text().strip():
            show_error(self, "Le nom de la classe est obligatoire.")
            return
        conn = get_connection()
        try:
            if self.class_row:
                conn.execute(
                    "UPDATE classes SET name=?, level=?, capacity=? WHERE id=?",
                    (self.name.text().strip(), self.level.text().strip(),
                     self.capacity.value() or None, self.class_row["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO classes (name, level, capacity) VALUES (?, ?, ?)",
                    (self.name.text().strip(), self.level.text().strip(), self.capacity.value() or None),
                )
            conn.commit()
            self.accept()
        except Exception as e:
            show_error(self, f"Une classe avec ce nom existe peut-être déjà.\n{e}")


class ClassesWidget(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Classes / Niveaux")
        title.setProperty("role", "title")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        add_btn = QPushButton("+ Ajouter une classe")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_class)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nom", "Niveau", "Élèves inscrits", "Capacité"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_class)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        edit_btn = QPushButton("Modifier")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.clicked.connect(self.edit_class)
        delete_btn = QPushButton("Supprimer")
        delete_btn.setProperty("variant", "danger")
        delete_btn.clicked.connect(self.delete_class)
        action_row.addWidget(edit_btn)
        action_row.addStretch()
        action_row.addWidget(delete_btn)
        layout.addLayout(action_row)

    def refresh(self):
        conn = get_connection()
        rows = conn.execute("SELECT * FROM classes ORDER BY name").fetchall()
        self.table.setRowCount(0)
        for r in rows:
            count = conn.execute(
                """SELECT COUNT(*) AS c FROM student_classes sc
                   JOIN students s ON s.id=sc.student_id
                   WHERE sc.class_id=? AND s.status='actif'""",
                (r["id"],),
            ).fetchone()["c"]
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(r["name"]))
            self.table.setItem(idx, 1, QTableWidgetItem(r["level"] or "-"))
            self.table.setItem(idx, 2, QTableWidgetItem(str(count)))
            self.table.setItem(idx, 3, QTableWidgetItem(str(r["capacity"]) if r["capacity"] else "-"))
            self.table.item(idx, 0).setData(Qt.UserRole, r["id"])

    def _selected_class(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        class_id = self.table.item(row, 0).data(Qt.UserRole)
        conn = get_connection()
        return conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()

    def add_class(self):
        dlg = ClassFormDialog(self)
        if dlg.exec():
            log_action(self.user, "Classe ajoutée", dlg.name.text())
            self.refresh()

    def edit_class(self):
        cls = self._selected_class()
        if not cls:
            show_error(self, "Veuillez sélectionner une classe.")
            return
        dlg = ClassFormDialog(self, cls)
        if dlg.exec():
            log_action(self.user, "Classe modifiée", cls["name"])
            self.refresh()

    def delete_class(self):
        cls = self._selected_class()
        if not cls:
            show_error(self, "Veuillez sélectionner une classe.")
            return
        if confirm_delete(self, f"la classe {cls['name']}"):
            conn = get_connection()
            conn.execute("DELETE FROM classes WHERE id=?", (cls["id"],))
            conn.commit()
            log_action(self.user, "Classe supprimée", cls["name"])
            self.refresh()
