"""
auth.py
Authentification et gestion sécurisée des mots de passe (PBKDF2-HMAC-SHA256).
Aucun mot de passe n'est jamais stocké en clair.
"""
import hashlib
import os
import binascii
from datetime import datetime

from database import get_connection

ITERATIONS = 200_000


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return binascii.hexlify(dk).decode("ascii")


def create_user(username: str, password: str, role: str, full_name: str) -> bool:
    """Crée un nouvel utilisateur. Retourne False si le nom d'utilisateur existe déjà."""
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        return False

    salt = os.urandom(16)
    salt_hex = binascii.hexlify(salt).decode("ascii")
    password_hash = _hash_password(password, salt)

    conn.execute(
        "INSERT INTO users (username, password_hash, salt, role, full_name, active, created_at) "
        "VALUES (?, ?, ?, ?, ?, 1, ?)",
        (username, password_hash, salt_hex, role, full_name, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return True


def verify_login(username: str, password: str):
    """Vérifie les identifiants. Retourne le dict utilisateur si succès, sinon None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND active = 1", (username,)
    ).fetchone()
    if not row:
        return None

    salt = binascii.unhexlify(row["salt"])
    candidate_hash = _hash_password(password, salt)
    if candidate_hash == row["password_hash"]:
        return dict(row)
    return None


def change_password(user_id: int, new_password: str):
    conn = get_connection()
    salt = os.urandom(16)
    salt_hex = binascii.hexlify(salt).decode("ascii")
    password_hash = _hash_password(new_password, salt)
    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
        (password_hash, salt_hex, user_id),
    )
    conn.commit()


def set_user_active(user_id: int, active: bool):
    conn = get_connection()
    conn.execute("UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, user_id))
    conn.commit()


def list_secretaries():
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM users WHERE role = 'secretaire' ORDER BY full_name"
    ).fetchall()
