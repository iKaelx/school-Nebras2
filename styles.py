"""
styles.py
Palette de couleurs et feuille de style (QSS) basées sur le logo de l'école
(flamme dorée en N, goutte bleue, livre ouvert, fond navy).
"""

GOLD = "#E3A93B"
GOLD_DARK = "#B87A1E"
BLUE = "#1E6FB0"
NAVY = "#101B36"
BG_LIGHT = "#F5F6F8"
WHITE = "#FFFFFF"
TEXT = "#2B2F38"
RED = "#C0392B"
GREEN = "#3C8D5C"

FONT_FAMILY = "Segoe UI"

APP_STYLESHEET = f"""
QWidget {{
    font-family: '{FONT_FAMILY}';
    color: {TEXT};
    font-size: 13px;
}}

QMainWindow, QDialog {{
    background-color: {BG_LIGHT};
}}
#contentArea {{
    background-color: {BG_LIGHT};
}}

/* ---- Sidebar ---- */
#sidebar {{
    background-color: {NAVY};
}}
#sidebar QPushButton {{
    background-color: transparent;
    color: #c3cbe0;
    text-align: left;
    padding: 13px 22px;
    border: none;
    font-size: 13px;
    font-weight: 500;
    border-left: 3px solid transparent;
    border-radius: 0px;
}}
#sidebar QPushButton:hover {{
    background-color: #182548;
    color: white;
}}
#sidebar QPushButton:checked {{
    background-color: #16223f;
    border-left: 3px solid {GOLD};
    color: {GOLD};
    font-weight: 600;
}}
#sidebarTitle {{
    color: white;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 0.3px;
    padding: 26px 22px 20px 22px;
    border-bottom: 1px solid #223055;
}}
#sidebarFooter {{
    color: #7c88ab;
    padding: 14px 22px;
    font-size: 11px;
    line-height: 160%;
    border-top: 1px solid #223055;
}}
#sidebarUtilityButton {{
    background-color: transparent;
    color: #9aa5c4;
    text-align: left;
    padding: 11px 22px;
    border: none;
    font-size: 12px;
    font-weight: 500;
    border-radius: 0px;
}}
#sidebarUtilityButton:hover {{
    background-color: #182548;
    color: white;
}}

/* ---- Header ---- */
#header {{
    background-color: {WHITE};
    border-bottom: 1px solid #e7e9ee;
}}
#headerTitle {{
    color: {NAVY};
    font-size: 18px;
    font-weight: 700;
}}
#headerUser {{
    color: #6b7280;
    font-size: 12px;
    font-weight: 500;
}}
#headerUserBadge {{
    background-color: {BG_LIGHT};
    border-radius: 14px;
    padding: 5px 14px;
}}

/* ---- Titles ---- */
QLabel[role="title"] {{
    color: {NAVY};
    font-size: 21px;
    font-weight: 700;
    padding-bottom: 4px;
}}
QLabel[role="section"] {{
    color: {NAVY};
    font-size: 14px;
    font-weight: 700;
}}
QLabel[role="subtitle"] {{
    color: #8a90a0;
    font-size: 12px;
    font-weight: 500;
}}

/* ---- Scrollbars ---- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #cfd4de;
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #b6bcc9;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ---- Buttons ---- */
QPushButton {{
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
}}
QPushButton[variant="primary"] {{
    background-color: {GOLD};
    color: {NAVY};
    border: none;
}}
QPushButton[variant="primary"]:hover {{
    background-color: {GOLD_DARK};
    color: white;
}}
QPushButton[variant="primary"]:pressed {{
    background-color: #a06a1a;
}}
QPushButton[variant="secondary"] {{
    background-color: white;
    color: {NAVY};
    border: 1px solid #ced3dd;
}}
QPushButton[variant="secondary"]:hover {{
    background-color: #eef1f6;
    border: 1px solid {NAVY};
}}
QPushButton[variant="danger"] {{
    background-color: white;
    color: {RED};
    border: 1px solid #e3b0aa;
}}
QPushButton[variant="danger"]:hover {{
    background-color: {RED};
    color: white;
    border: 1px solid {RED};
}}
QPushButton:disabled {{
    background-color: #eceef2;
    color: #b0b4bd;
    border: 1px solid #e1e4ea;
}}

/* ---- Inputs ---- */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QDateTimeEdit {{
    background-color: white;
    border: 1px solid #d5d9e1;
    border-radius: 5px;
    padding: 6px 9px;
    selection-background-color: {GOLD};
    selection-color: {NAVY};
}}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QDateTimeEdit:hover {{
    border: 1px solid #b7bdc9;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDateTimeEdit:focus, QTextEdit:focus {{
    border: 1px solid {BLUE};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QCheckBox {{
    spacing: 8px;
}}

/* ---- Tables ---- */
QHeaderView::section {{
    background-color: {NAVY};
    color: white;
    padding: 8px 10px;
    border: none;
    font-weight: 600;
    font-size: 12px;
}}
QTableWidget {{
    background-color: white;
    alternate-background-color: #fafbfc;
    gridline-color: #edeff2;
    selection-background-color: #fbe9c8;
    selection-color: {NAVY};
    border: 1px solid #e3e6eb;
    border-radius: 6px;
}}
QTableWidget::item {{
    padding: 5px 6px;
    border-bottom: 1px solid #f0f1f4;
}}
QTableWidget::item:selected {{
    background-color: #fbe9c8;
    color: {NAVY};
}}

/* ---- Cards (Dashboard) ---- */
QFrame[role="card"] {{
    background-color: white;
    border-radius: 10px;
    border: 1px solid #e9ebf0;
    padding: 4px;
}}
QFrame[card_accent="gold"] {{
    border-top: 4px solid {GOLD};
}}
QFrame[card_accent="blue"] {{
    border-top: 4px solid {BLUE};
}}
QFrame[card_accent="red"] {{
    border-top: 4px solid {RED};
}}
QFrame[card_accent="green"] {{
    border-top: 4px solid {GREEN};
}}
QLabel[role="cardValue"] {{
    font-size: 25px;
    font-weight: 700;
    color: {NAVY};
}}
QLabel[role="cardLabel"] {{
    color: #7c8494;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2px;
    text-transform: uppercase;
}}

/* ---- Tabs ---- */
QTabBar::tab {{
    background: transparent;
    color: #7c8494;
    padding: 10px 20px;
    border: none;
    font-weight: 600;
    margin-right: 4px;
}}
QTabBar::tab:hover {{
    color: {NAVY};
}}
QTabBar::tab:selected {{
    background: transparent;
    color: {NAVY};
    border-bottom: 3px solid {GOLD};
}}
QTabWidget::pane {{
    border: none;
    border-top: 1px solid #e3e6eb;
    background: transparent;
    padding-top: 12px;
}}

/* Status colors */
QLabel[status="paye"] {{ color: {GREEN}; font-weight: bold; }}
QLabel[status="retard"] {{ color: {RED}; font-weight: bold; }}
"""


def refresh_style(widget):
    """Force Qt à ré-appliquer le style après changement d'une propriété dynamique (ex: variant)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
