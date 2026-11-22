"""
ui/dashboard_widget.py
Tableau de bord Admin : vue synthétique (élèves, enseignants, présence,
événements à venir, indicateurs financiers).
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from database import get_connection
from utils import format_currency


def _card(title, value, accent="gold"):
    frame = QFrame()
    frame.setProperty("role", "card")
    frame.setProperty("card_accent", accent)
    frame.setMinimumHeight(92)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(6)
    value_label = QLabel(str(value))
    value_label.setProperty("role", "cardValue")
    value_label.setWordWrap(True)
    title_label = QLabel(title)
    title_label.setProperty("role", "cardLabel")
    layout.addWidget(value_label)
    layout.addWidget(title_label)

    shadow = QGraphicsDropShadowEffect(frame)
    shadow.setBlurRadius(18)
    shadow.setXOffset(0)
    shadow.setYOffset(3)
    shadow.setColor(QColor(16, 27, 54, 25))
    frame.setGraphicsEffect(shadow)

    return frame


class DashboardWidget(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.layout_ = QVBoxLayout(self)
        self.layout_.setSpacing(18)
        title = QLabel("Tableau de bord")
        title.setProperty("role", "title")
        self.layout_.addWidget(title)

        section1_label = QLabel("Vue d'ensemble")
        section1_label.setProperty("role", "subtitle")
        self.layout_.addWidget(section1_label)

        self.grid = QGridLayout()
        self.grid.setSpacing(16)
        self.layout_.addLayout(self.grid)

        section2_label = QLabel("Indicateurs financiers")
        section2_label.setProperty("role", "subtitle")
        self.layout_.addWidget(section2_label)

        self.section2 = QGridLayout()
        self.section2.setSpacing(16)
        self.layout_.addLayout(self.section2)
        self.layout_.addStretch()

    def refresh(self):
        conn = get_connection()

        # nettoyage des grilles
        for grid in (self.grid, self.section2):
            while grid.count():
                item = grid.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

        total_students = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
        active_students = conn.execute("SELECT COUNT(*) c FROM students WHERE status='actif'").fetchone()["c"]
        inactive_students = total_students - active_students
        total_teachers = conn.execute("SELECT COUNT(*) c FROM teachers").fetchone()["c"]

        now = datetime.now()
        upcoming_events = conn.execute(
            "SELECT COUNT(*) c FROM events WHERE start_datetime >= ?",
            (now.strftime("%Y-%m-%d %H:%M"),),
        ).fetchone()["c"]

        total_absences = conn.execute("SELECT COUNT(*) c FROM absences").fetchone()["c"]
        unjustified = conn.execute("SELECT COUNT(*) c FROM absences WHERE justified=0").fetchone()["c"]

        current_year = now.year
        revenue = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM payments WHERE year=?", (current_year,)
        ).fetchone()["s"]
        expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM expenses WHERE strftime('%Y', date)=?",
            (str(current_year),),
        ).fetchone()["s"]

        unpaid_count = 0
        current_month = now.month
        for s in conn.execute("SELECT id FROM students WHERE status='actif'"):
            paid = conn.execute(
                "SELECT COUNT(*) c FROM payments WHERE student_id=? AND month=? AND year=?",
                (s["id"], current_month, current_year),
            ).fetchone()["c"]
            if paid == 0:
                unpaid_count += 1

        cards = [
            (f"{active_students} actifs / {inactive_students} inactifs", f"Élèves ({total_students} au total)", "blue"),
            (total_teachers, "Enseignants", "blue"),
            (upcoming_events, "Événements à venir", "gold"),
            (f"{total_absences} ({unjustified} non justifiées)", "Absences enregistrées", "red"),
        ]
        for i, (value, label, accent) in enumerate(cards):
            self.grid.addWidget(_card(label, value, accent), 0, i)

        balance = revenue - expenses
        cards2 = [
            (format_currency(revenue), f"Revenus {current_year}", "green"),
            (format_currency(expenses), f"Dépenses {current_year}", "red"),
            (format_currency(balance), "Bilan (revenus - dépenses)", "gold"),
            (unpaid_count, "Élèves en retard ce mois-ci", "red"),
        ]
        for i, (value, label, accent) in enumerate(cards2):
            self.section2.addWidget(_card(label, value, accent), 0, i)
