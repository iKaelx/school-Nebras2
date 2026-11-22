"""
utils.py
Fonctions transversales : validation de champs, génération de reçus,
export CSV et sauvegarde de la base de données.
"""
import re
import csv
import shutil
from datetime import datetime

from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def validate_phone(phone: str) -> bool:
    if not phone:
        return True  # champ optionnel dans certains formulaires
    return bool(re.match(r"^[0-9+\-\s()]{6,20}$", phone))


def validate_date(date_str: str) -> bool:
    if not date_str:
        return True
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_currency(amount) -> str:
    try:
        return f"{float(amount):,.2f} DA".replace(",", " ")
    except (TypeError, ValueError):
        return "0.00 DA"


def confirm_delete(parent, item_name: str = "cet élément") -> bool:
    """Affiche une boîte de confirmation avant suppression."""
    reply = QMessageBox.question(
        parent,
        "Confirmation de suppression",
        f"Voulez-vous vraiment supprimer {item_name} ?\nCette action est irréversible.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes


def show_error(parent, message: str):
    QMessageBox.critical(parent, "Erreur", message)


def show_info(parent, message: str, title: str = "Information"):
    QMessageBox.information(parent, title, message)


def export_rows_to_csv(parent, headers, rows, default_name="export.csv"):
    """Exporte une liste de lignes (tuples/listes) vers un fichier CSV (compatible Excel)."""
    path, _ = QFileDialog.getSaveFileName(parent, "Exporter en CSV", default_name, "Fichiers CSV (*.csv)")
    if not path:
        return
    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(headers)
            writer.writerows(rows)
        show_info(parent, f"Export réalisé avec succès :\n{path}")
    except OSError as e:
        show_error(parent, f"Impossible d'exporter le fichier :\n{e}")


def backup_database(parent, db_path: str):
    """Copie le fichier de base de données vers un emplacement choisi par l'utilisateur."""
    default_name = f"ecole_sauvegarde_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    path, _ = QFileDialog.getSaveFileName(parent, "Sauvegarder la base de données", default_name, "Base SQLite (*.db)")
    if not path:
        return
    try:
        shutil.copyfile(db_path, path)
        show_info(parent, f"Sauvegarde effectuée avec succès :\n{path}")
    except OSError as e:
        show_error(parent, f"Échec de la sauvegarde :\n{e}")


def build_receipt_html(school_name, student, payment) -> str:
    """Construit le HTML d'un reçu de paiement imprimable."""
    mois_label = MOIS_FR[int(payment["month"]) - 1] if 1 <= int(payment["month"]) <= 12 else payment["month"]
    return f"""
    <html>
    <body style="font-family: 'Segoe UI', sans-serif; color: #2B2F38;">
        <div style="text-align:center; border-bottom: 3px solid #E3A93B; padding-bottom: 10px; margin-bottom: 20px;">
            <h2 style="color:#101B36; margin-bottom:0;">{school_name}</h2>
            <p style="color:#1E6FB0; margin-top:4px;">Reçu de paiement</p>
        </div>
        <table width="100%" style="font-size:14px;">
            <tr><td><b>N° de reçu :</b></td><td>{payment['receipt_number']}</td></tr>
            <tr><td><b>Date de paiement :</b></td><td>{payment['payment_date']}</td></tr>
            <tr><td><b>Élève :</b></td><td>{student['first_name']} {student['last_name']}</td></tr>
            <tr><td><b>Classe :</b></td><td>{student.get('class_name', '-')}</td></tr>
            <tr><td><b>Période :</b></td><td>{mois_label} {payment['year']}</td></tr>
            <tr><td><b>Montant :</b></td><td><b>{format_currency(payment['amount'])}</b></td></tr>
            <tr><td><b>Méthode de paiement :</b></td><td>{payment['method'] or '-'}</td></tr>
        </table>
        <p style="margin-top:40px; color:#6b7280; font-size:11px;">
            Reçu généré automatiquement — {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
    </body>
    </html>
    """


def print_html_document(parent, html: str):
    """Ouvre la boîte de dialogue d'impression pour un contenu HTML donné."""
    doc = QTextDocument()
    doc.setHtml(html)
    printer = QPrinter(QPrinter.HighResolution)
    dialog = QPrintDialog(printer, parent)
    if dialog.exec() == QPrintDialog.Accepted:
        doc.print_(printer)


def export_html_to_pdf(parent, html: str, default_name="document.pdf"):
    """Exporte un contenu HTML en fichier PDF."""
    path, _ = QFileDialog.getSaveFileName(parent, "Exporter en PDF", default_name, "Fichiers PDF (*.pdf)")
    if not path:
        return
    doc = QTextDocument()
    doc.setHtml(html)
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(path)
    doc.print_(printer)
    show_info(parent, f"PDF généré avec succès :\n{path}")
