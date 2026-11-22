"""
ui/users_widget.py
Module « Gestion des utilisateurs » (Admin) : créer/désactiver les comptes
secrétaire, et consulter l'historique des actions importantes.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QTabWidget, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt

from database import get_connection, log_action
from auth import create_user, set_user_active, change_password, list_secretaries
from utils import show_error, show_info, confirm_delete


class NewUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Créer un compte secrétaire")
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.full_name = QLineEdit()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        form.addRow("Nom complet *", self.full_name)
        form.addRow("Identifiant *", self.username)
        form.addRow("Mot de passe *", self.password)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Créer")
        buttons.button(QDialogButtonBox.Save).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self):
        if not self.full_name.text().strip() or not self.username.text().strip() or not self.password.text():
            show_error(self, "Tous les champs sont obligatoires.")
            return
        if len(self.password.text()) < 6:
            show_error(self, "Le mot de passe doit contenir au moins 6 caractères.")
            return
        self.accept()


class UsersWidget(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Gestion des utilisateurs")
        title.setProperty("role", "title")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_users_tab(), "Comptes secrétaire")
        tabs.addTab(self._build_history_tab(), "Historique des actions")
        layout.addWidget(tabs)
        self.tabs = tabs

    def _build_users_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        add_btn = QPushButton("+ Créer un compte secrétaire")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_user)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        self.users_table = QTableWidget(0, 3)
        self.users_table.setHorizontalHeaderLabels(["Nom complet", "Identifiant", "Statut"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.users_table)

        action_row = QHBoxLayout()
        toggle_btn = QPushButton("Activer / Désactiver")
        toggle_btn.setProperty("variant", "secondary")
        toggle_btn.clicked.connect(self.toggle_user)
        reset_btn = QPushButton("Réinitialiser le mot de passe")
        reset_btn.setProperty("variant", "secondary")
        reset_btn.clicked.connect(self.reset_password)
        action_row.addWidget(toggle_btn)
        action_row.addWidget(reset_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

        return w

    def _build_history_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["Date/Heure", "Utilisateur", "Action", "Détails"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)
        return w

    def refresh(self):
        rows = list_secretaries()
        self.users_table.setRowCount(0)
        for r in rows:
            idx = self.users_table.rowCount()
            self.users_table.insertRow(idx)
            self.users_table.setItem(idx, 0, QTableWidgetItem(r["full_name"]))
            self.users_table.setItem(idx, 1, QTableWidgetItem(r["username"]))
            self.users_table.setItem(idx, 2, QTableWidgetItem("Actif" if r["active"] else "Désactivé"))
            self.users_table.item(idx, 0).setData(Qt.UserRole, r["id"])

        conn = get_connection()
        logs = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT 200"
        ).fetchall()
        self.history_table.setRowCount(0)
        for r in logs:
            idx = self.history_table.rowCount()
            self.history_table.insertRow(idx)
            self.history_table.setItem(idx, 0, QTableWidgetItem(r["timestamp"]))
            self.history_table.setItem(idx, 1, QTableWidgetItem(r["username"] or "-"))
            self.history_table.setItem(idx, 2, QTableWidgetItem(r["action"]))
            self.history_table.setItem(idx, 3, QTableWidgetItem(r["details"] or ""))

    def _selected_user_id(self):
        row = self.users_table.currentRow()
        if row < 0:
            return None
        return self.users_table.item(row, 0).data(Qt.UserRole)

    def add_user(self):
        dlg = NewUserDialog(self)
        if dlg.exec():
            ok = create_user(dlg.username.text().strip(), dlg.password.text(), "secretaire", dlg.full_name.text().strip())
            if not ok:
                show_error(self, "Cet identifiant existe déjà.")
                return
            log_action(self.user, "Compte secrétaire créé", dlg.username.text())
            self.refresh()

    def toggle_user(self):
        user_id = self._selected_user_id()
        if user_id is None:
            show_error(self, "Veuillez sélectionner un compte.")
            return
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        new_state = not row["active"]
        if confirm_delete(self, f"{'activer' if new_state else 'désactiver'} le compte {row['username']}") if not new_state else True:
            set_user_active(user_id, new_state)
            log_action(self.user, "Statut de compte modifié", f"{row['username']} → {'actif' if new_state else 'désactivé'}")
            self.refresh()

    def reset_password(self):
        user_id = self._selected_user_id()
        if user_id is None:
            show_error(self, "Veuillez sélectionner un compte.")
            return
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Réinitialiser le mot de passe — {row['username']}")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        new_pass = QLineEdit()
        new_pass.setEchoMode(QLineEdit.Password)
        form.addRow("Nouveau mot de passe", new_pass)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Save).setProperty("variant", "primary")
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec():
            if len(new_pass.text()) < 6:
                show_error(self, "Le mot de passe doit contenir au moins 6 caractères.")
                return
            change_password(user_id, new_pass.text())
            log_action(self.user, "Mot de passe réinitialisé", row["username"])
            show_info(self, "Mot de passe mis à jour avec succès.")
