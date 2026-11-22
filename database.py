"""
database.py
Gestion de la connexion SQLite, création du schéma et données initiales.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecole.db")

_connection = None


def get_connection():
    """Retourne une connexion SQLite unique (singleton) avec les clés étrangères activées."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_PATH)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA foreign_keys = ON")
    return _connection


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'secretaire')),
    full_name TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    level TEXT,
    capacity INTEGER
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    birth_date TEXT,
    sex TEXT CHECK(sex IN ('M', 'F', '')),
    photo_path TEXT,
    class_id INTEGER,
    parent_name TEXT,
    parent_phone TEXT,
    parent_address TEXT,
    registration_date TEXT,
    status TEXT NOT NULL DEFAULT 'actif' CHECK(status IN ('actif', 'inactif', 'a_quitte')),
    school_year TEXT,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    email TEXT,
    subjects TEXT,
    hire_date TEXT,
    salary REAL,
    schedule TEXT
);

CREATE TABLE IF NOT EXISTS teacher_classes (
    teacher_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    PRIMARY KEY (teacher_id, class_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    method TEXT,
    receipt_number TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS absences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    justified INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    start_datetime TEXT NOT NULL,
    end_datetime TEXT,
    event_type TEXT,
    class_id INTEGER,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    category TEXT,
    amount REAL NOT NULL,
    date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS school_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT UNIQUE NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 0
);
"""


def init_db():
    """Crée les tables si elles n'existent pas et insère un compte admin par défaut."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()

    cur = conn.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        from auth import create_user
        create_user("admin", "admin123", "admin", "Administrateur")

    cur = conn.execute("SELECT COUNT(*) AS c FROM school_years")
    if cur.fetchone()["c"] == 0:
        year_label = f"{datetime.now().year}-{datetime.now().year + 1}"
        conn.execute(
            "INSERT INTO school_years (label, is_current) VALUES (?, 1)", (year_label,)
        )
        conn.commit()


def log_action(user, action, details=""):
    """Enregistre une action dans l'historique (audit_log)."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (user_id, username, action, details, timestamp) VALUES (?, ?, ?, ?, ?)",
        (
            user["id"] if user else None,
            user["username"] if user else "système",
            action,
            details,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()


def get_current_school_year():
    conn = get_connection()
    row = conn.execute("SELECT label FROM school_years WHERE is_current = 1").fetchone()
    return row["label"] if row else ""
