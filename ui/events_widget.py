"""
ui/events_widget.py
Module « Calendrier / Événements » : vue calendrier mensuelle, liste, recherche,
ajout/modification/suppression d'événements.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QCalendarWidget,
    QDialog, QFormLayout, QDateTimeEdit, QTextEdit, QDialogButtonBox, QSplitter
)
from PySide6.QtCore import Qt, QDateTime, QDate
from PySide6.QtGui import QTextCharFormat, QColor

from database import get_connection, log_action
from utils import confirm_delete, show_error
import styles

EVENT_TYPES = ["Examen", "Réunion", "Sortie scolaire", "Vacances", "Fête", "Autre"]


class EventFormDialog(QDialog):
    def __init__(self, parent=None, event_data=None):
        super().__init__(parent)
        # NB: on n'utilise jamais "self.event" comme nom d'attribut : QDialog possède déjà
        # une méthode interne event() utilisée par Qt : l'écraser casse la boîte de dialogue.
        self.event_row = event_data
        self.setWindowTitle("Modifier l'événement" if event_data else "Ajouter un événement")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.description = QTextEdit()
        self.description.setFixedHeight(70)

        self.event_type = QComboBox()
        self.event_type.addItems(EVENT_TYPES)

        self.class_combo = QComboBox()
        self.class_combo.addItem("Toutes les classes", None)
        conn = get_connection()
        for row in conn.execute("SELECT id, name FROM classes ORDER BY name"):
            self.class_combo.addItem(row["name"], row["id"])

        self.start_dt = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_dt.setCalendarPopup(True)
        self.start_dt.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.end_dt = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.end_dt.setCalendarPopup(True)
        self.end_dt.setDisplayFormat("yyyy-MM-dd HH:mm")

        form.addRow("Titre *", self.title_edit)
        form.addRow("Description", self.description)
        form.addRow("Type", self.event_type)
        form.addRow("Classe concernée", self.class_combo)
        form.addRow("Début", self.start_dt)
        form.addRow("Fin", self.end_dt)
        layout.addLayout(form)

        if event_data:
            self.title_edit.setText(event_data["title"])
            self.description.setPlainText(event_data["description"] or "")
            self.event_type.setCurrentText(event_data["event_type"] or "Autre")
            self.start_dt.setDateTime(QDateTime.fromString(event_data["start_datetime"], "yyyy-MM-dd HH:mm"))
            if event_data["end_datetime"]:
                self.end_dt.setDateTime(QDateTime.fromString(event_data["end_datetime"], "yyyy-MM-dd HH:mm"))
            if event_data["class_id"]:
                idx = self.class_combo.findData(event_data["class_id"])
                if idx >= 0:
                    self.class_combo.setCurrentIndex(idx)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Save).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self):
        if not self.title_edit.text().strip():
            show_error(self, "Le titre de l'événement est obligatoire.")
            return
        conn = get_connection()
        data = (
            self.title_edit.text().strip(),
            self.description.toPlainText().strip(),
            self.start_dt.dateTime().toString("yyyy-MM-dd HH:mm"),
            self.end_dt.dateTime().toString("yyyy-MM-dd HH:mm"),
            self.event_type.currentText(),
            self.class_combo.currentData(),
        )
        if self.event_row:
            conn.execute(
                """UPDATE events SET title=?, description=?, start_datetime=?, end_datetime=?,
                   event_type=?, class_id=? WHERE id=?""",
                data + (self.event_row["id"],),
            )
        else:
            conn.execute(
                """INSERT INTO events (title, description, start_datetime, end_datetime, event_type, class_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                data,
            )
        conn.commit()
        self.accept()


class EventsWidget(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Calendrier & Événements")
        title.setProperty("role", "title")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Rechercher par mot-clé…")
        self.search_edit.textChanged.connect(self.refresh)
        self.type_filter = QComboBox()
        self.type_filter.addItem("Tous les types", None)
        for t in EVENT_TYPES:
            self.type_filter.addItem(t, t)
        self.type_filter.currentIndexChanged.connect(self.refresh)
        add_btn = QPushButton("+ Ajouter un événement")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_event)
        toolbar.addWidget(self.search_edit, stretch=1)
        toolbar.addWidget(self.type_filter)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)

        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self._on_date_clicked)
        splitter.addWidget(self.calendar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Titre", "Type", "Début", "Classe"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_event)
        right_layout.addWidget(self.table)

        action_row = QHBoxLayout()
        edit_btn = QPushButton("Modifier")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.clicked.connect(self.edit_event)
        delete_btn = QPushButton("Supprimer")
        delete_btn.setProperty("variant", "danger")
        delete_btn.clicked.connect(self.delete_event)
        action_row.addWidget(edit_btn)
        action_row.addStretch()
        action_row.addWidget(delete_btn)
        right_layout.addLayout(action_row)

        splitter.addWidget(right)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

    def _on_date_clicked(self, date: QDate):
        self.search_edit.blockSignals(True)
        self.search_edit.clear()
        self.search_edit.blockSignals(False)
        self._filter_date = date.toString("yyyy-MM-dd")
        self.refresh(day_filter=self._filter_date)

    def refresh(self, day_filter=None):
        conn = get_connection()
        query = """
            SELECT e.*, c.name AS class_name FROM events e
            LEFT JOIN classes c ON e.class_id = c.id WHERE 1=1
        """
        params = []
        search = self.search_edit.text().strip()
        if search:
            query += " AND (e.title LIKE ? OR e.description LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        etype = self.type_filter.currentData()
        if etype:
            query += " AND e.event_type = ?"
            params.append(etype)
        if day_filter:
            query += " AND e.start_datetime LIKE ?"
            params.append(f"{day_filter}%")
        query += " ORDER BY e.start_datetime"

        rows = conn.execute(query, params).fetchall()
        self.table.setRowCount(0)

        # Réinitialise le formatage du calendrier puis marque les jours avec événements
        default_fmt = QTextCharFormat()
        self.calendar.setDateTextFormat(QDate(), default_fmt)
        marked_fmt = QTextCharFormat()
        marked_fmt.setBackground(QColor(styles.GOLD))
        marked_fmt.setForeground(QColor(styles.NAVY))
        all_events = conn.execute("SELECT DISTINCT start_datetime FROM events").fetchall()
        for r in all_events:
            d = QDate.fromString(r["start_datetime"][:10], "yyyy-MM-dd")
            if d.isValid():
                self.calendar.setDateTextFormat(d, marked_fmt)

        for r in rows:
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(r["title"]))
            self.table.setItem(idx, 1, QTableWidgetItem(r["event_type"] or "-"))
            self.table.setItem(idx, 2, QTableWidgetItem(r["start_datetime"]))
            self.table.setItem(idx, 3, QTableWidgetItem(r["class_name"] or "Toutes"))
            self.table.item(idx, 0).setData(Qt.UserRole, r["id"])

    def _selected_event(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        event_id = self.table.item(row, 0).data(Qt.UserRole)
        conn = get_connection()
        return conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()

    def add_event(self):
        dlg = EventFormDialog(self)
        if dlg.exec():
            log_action(self.user, "Événement ajouté", dlg.title_edit.text())
            self.refresh()

    def edit_event(self):
        event = self._selected_event()
        if not event:
            show_error(self, "Veuillez sélectionner un événement.")
            return
        dlg = EventFormDialog(self, event)
        if dlg.exec():
            log_action(self.user, "Événement modifié", event["title"])
            self.refresh()

    def delete_event(self):
        event = self._selected_event()
        if not event:
            show_error(self, "Veuillez sélectionner un événement.")
            return
        if confirm_delete(self, f"l'événement « {event['title']} »"):
            conn = get_connection()
            conn.execute("DELETE FROM events WHERE id=?", (event["id"],))
            conn.commit()
            log_action(self.user, "Événement supprimé", event["title"])
            self.refresh()
