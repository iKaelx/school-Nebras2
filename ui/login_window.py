"""
ui/login_window.py
Écran de connexion : logo centré, champs identifiant/mot de passe, bouton doré.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from auth import verify_login
from database import log_action
import styles


class LoginWindow(QDialog):
    def __init__(self, school_name="École Nebras"):
        super().__init__()
        self.school_name = school_name
        self.user = None
        self.setWindowTitle("Connexion — " + school_name)
        self.setFixedSize(420, 480)
        self.setStyleSheet(styles.APP_STYLESHEET)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(14)

        # Logo (badge stylisé en attendant le logo réel de l'école)
        logo = QFrame()
        logo.setFixedSize(96, 96)
        logo.setStyleSheet(
            f"background-color: {styles.NAVY}; border-radius: 48px; border: 3px solid {styles.GOLD};"
        )
        logo_layout = QVBoxLayout(logo)
        logo_label = QLabel("N")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f"color: {styles.GOLD}; font-size: 44px; font-weight: bold; border: none;")
        logo_layout.addWidget(logo_label)

        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        title = QLabel(self.school_name)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont(styles.FONT_FAMILY, 18, QFont.Bold))
        title.setStyleSheet(f"color: {styles.NAVY};")
        layout.addWidget(title)

        subtitle = QLabel("Gestion administrative")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6b7280;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Identifiant")
        layout.addWidget(self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Mot de passe")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self.try_login)
        layout.addWidget(self.password_edit)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {styles.RED};")
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label)

        login_btn = QPushButton("Se connecter")
        login_btn.setProperty("variant", "primary")
        login_btn.setMinimumHeight(38)
        login_btn.clicked.connect(self.try_login)
        layout.addWidget(login_btn)

        layout.addStretch()

        footer = QLabel("for bright future")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #9aa0aa; font-size: 10px;")
        layout.addWidget(footer)

    def try_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username or not password:
            self.error_label.setText("Veuillez remplir tous les champs.")
            return

        user = verify_login(username, password)
        if user:
            self.user = user
            log_action(user, "Connexion", f"Connexion réussie de {username}")
            self.accept()
        else:
            self.error_label.setText("Identifiant ou mot de passe incorrect.")
            self.password_edit.clear()
