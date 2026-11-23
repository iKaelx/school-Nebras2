"""
main.py
Point d'entrée de l'application de gestion d'école privée.
Lance l'écran de connexion puis la fenêtre principale selon le rôle.
"""
import sys

from PySide6.QtWidgets import QApplication

from database import init_db
import styles
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

SCHOOL_NAME = "Alkaouther Academy"


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(styles.APP_STYLESHEET)

    init_db()

    login = LoginWindow(SCHOOL_NAME)
    if login.exec():
        window = MainWindow(login.user, SCHOOL_NAME)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
