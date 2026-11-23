"""
ui/main_window.py
Fenêtre principale de l'application : sidebar (menu latéral), en-tête, zone de contenu
qui affiche le module actif selon le rôle de l'utilisateur connecté.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os

import styles
from database import log_action, DB_PATH
from utils import backup_database

from ui.students_widget import StudentsWidget
from ui.teachers_widget import TeachersWidget
from ui.classes_widget import ClassesWidget
from ui.events_widget import EventsWidget
from ui.dashboard_widget import DashboardWidget
from ui.finances_widget import FinancesWidget
from ui.contacts_widget import ContactsWidget
from ui.users_widget import UsersWidget


class MainWindow(QMainWindow):
    def __init__(self, user, school_name="Alkaouther Academy"):
        super().__init__()
        self.user = user
        self.school_name = school_name
        self.setWindowTitle(f"{school_name} — Gestion administrative")
        self.resize(1200, 760)
        self.setStyleSheet(styles.APP_STYLESHEET)
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._build_header())

        content_wrapper = QWidget()
        content_wrapper.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(28, 22, 28, 22)
        self.stack = QStackedWidget()
        self.pages = {}
        self._register_pages()
        content_layout.addWidget(self.stack)
        right.addWidget(content_wrapper)

        right_container = QWidget()
        right_container.setLayout(right)
        root.addWidget(right_container, stretch=1)

        self._select_page("dashboard" if self.user["role"] == "admin" else "students")

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedHeight(72)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "alkaouther.webp")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            logo.setPixmap(logo_pixmap.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            layout.addWidget(logo)

        title = QLabel(self.school_name)
        title.setObjectName("sidebarTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = {}

        entries = [("students", "Élèves"), ("teachers", "Enseignants"),
                   ("classes", "Classes"), ("events", "Calendrier")]
        if self.user["role"] == "admin":
            entries = [("dashboard", "Tableau de bord")] + entries + [
                ("finances", "Finances"),
                ("contacts", "Contacts"),
                ("users", "Utilisateurs"),
            ]

        for key, label in entries:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._select_page(k))
            layout.addWidget(btn)
            self.nav_group.addButton(btn)
            self.nav_buttons[key] = btn

        layout.addStretch()

        backup_btn = QPushButton("Sauvegarder la base")
        backup_btn.setObjectName("sidebarUtilityButton")
        backup_btn.setCursor(Qt.PointingHandCursor)
        backup_btn.clicked.connect(lambda: backup_database(self, DB_PATH))
        layout.addWidget(backup_btn)

        logout_btn = QPushButton("Déconnexion")
        logout_btn.setObjectName("sidebarUtilityButton")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        footer = QLabel(f"Connecté : {self.user['full_name']}\nRôle : {self.user['role'].capitalize()}")
        footer.setObjectName("sidebarFooter")
        layout.addWidget(footer)

        return sidebar

    def _build_header(self):
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(56)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        self.header_title = QLabel("")
        self.header_title.setObjectName("headerTitle")
        layout.addWidget(self.header_title)

        layout.addStretch()

        badge = QFrame()
        badge.setObjectName("headerUserBadge")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        user_label = QLabel(f"{self.user['full_name']}  ·  {self.user['role'].capitalize()}")
        user_label.setObjectName("headerUser")
        badge_layout.addWidget(user_label)
        layout.addWidget(badge)

        return header

    def _register_pages(self):
        self._add_page("students", "Gestion des élèves", StudentsWidget(self.user))
        self._add_page("teachers", "Gestion des enseignants", TeachersWidget(self.user))
        self._add_page("classes", "Gestion des classes", ClassesWidget(self.user))
        self._add_page("events", "Calendrier & événements", EventsWidget(self.user))
        if self.user["role"] == "admin":
            self._add_page("dashboard", "Tableau de bord", DashboardWidget(self.user))
            self._add_page("finances", "Gestion financière", FinancesWidget(self.user))
            self._add_page("contacts", "Carnet de contacts", ContactsWidget(self.user))
            self._add_page("users", "Gestion des utilisateurs", UsersWidget(self.user))

    def _add_page(self, key, title, widget):
        self.pages[key] = (title, widget)
        self.stack.addWidget(widget)

    def _select_page(self, key):
        title, widget = self.pages[key]
        self.stack.setCurrentWidget(widget)
        self.header_title.setText(title)
        if key in self.nav_buttons:
            self.nav_buttons[key].setChecked(True)
        if hasattr(widget, "refresh"):
            widget.refresh()

    def logout(self):
        log_action(self.user, "Déconnexion", f"Déconnexion de {self.user['username']}")
        self.close()
        from ui.login_window import LoginWindow
        login = LoginWindow(self.school_name)
        if login.exec():
            self.new_window = MainWindow(login.user, self.school_name)
            self.new_window.show()
