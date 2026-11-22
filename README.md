# Application de gestion d'école privée

Application desktop **Windows** (fonctionne aussi sur macOS/Linux) développée en **Python + PySide6**,
avec une base de données locale **SQLite**. Interface entièrement en français, identité visuelle
reprenant le logo de l'école (doré / bleu marine / bleu).

## 1. Installation (Windows)

1. Installer **Python 3.10+** depuis [python.org](https://www.python.org/downloads/) (cocher
   "Add Python to PATH" pendant l'installation).
2. Ouvrir une invite de commandes dans le dossier du projet et installer les dépendances :

   ```
   pip install -r requirements.txt
   ```

3. Lancer l'application :

   ```
   python main.py
   ```

## 2. Connexion

Un compte administrateur est créé automatiquement au premier lancement :

- **Identifiant :** `admin`
- **Mot de passe :** `admin123`

⚠️ Pensez à changer ce mot de passe dès la première connexion (module *Utilisateurs* réservé à l'Admin,
via "Réinitialiser le mot de passe").

Le compte admin peut ensuite créer des comptes **secrétaire** depuis le module *Utilisateurs*.

## 3. Modules disponibles

| Module | Secrétaire | Admin |
|---|---|---|
| Élèves (CRUD, paiements, absences, reçus) | ✅ | ✅ |
| Enseignants (CRUD, fiche) | ✅ (salaire masqué) | ✅ |
| Classes / Niveaux | ✅ | ✅ |
| Calendrier / Événements | ✅ | ✅ |
| Tableau de bord | ❌ | ✅ |
| Finances (revenus, impayés, dépenses) | ❌ | ✅ |
| Contacts | ❌ | ✅ |
| Gestion des utilisateurs + historique | ❌ | ✅ |

## 4. Fonctionnalités transversales

- Recherche et filtres disponibles dans chaque module.
- Sauvegarde de la base de données en un clic (bouton dans le menu latéral) — copie le fichier
  `ecole.db` vers l'emplacement de votre choix.
- Impression des reçus de paiement (boîte de dialogue d'impression Windows) et export PDF.
- Export CSV (ouvrable directement dans Excel) pour les listes d'impayés et de dépenses.
- Confirmation obligatoire avant toute suppression.
- Historique des actions importantes consultable par l'Admin.

## 5. Base de données

Le fichier `ecole.db` (SQLite) est créé automatiquement dans le dossier de l'application au premier
lancement. Il contient toutes les données : élèves, enseignants, classes, paiements, absences,
événements, contacts, dépenses, utilisateurs et historique.

Pour changer d'année scolaire, la table `school_years` peut être étendue depuis le code
(`database.py`) — une base pour l'archivage multi-année est déjà en place (`school_year` sur la
fiche élève).

## 6. Générer un exécutable Windows (.exe) — optionnel

Pour distribuer l'application sans que l'utilisateur installe Python, vous pouvez utiliser
**PyInstaller** :

```
pip install pyinstaller
pyinstaller --noconsole --onefile --name "GestionEcole" main.py
```

L'exécutable sera généré dans le dossier `dist/`.

## 7. Personnalisation

- **Nom de l'école** : modifier la variable `SCHOOL_NAME` en haut de `main.py`.
- **Logo réel** : remplacer le badge "N" généré dans `ui/login_window.py` par votre image (ex. avec
  un `QLabel` + `QPixmap("assets/logo.png")`), et l'ajouter également dans `ui/main_window.py`
  (en-tête) ainsi que dans les reçus (`utils.py`, fonction `build_receipt_html`).
- **Couleurs** : la palette est centralisée dans `styles.py`.

## 8. Structure du projet

```
ecole_app/
├── main.py                 # Point d'entrée
├── database.py              # Connexion SQLite + schéma
├── auth.py                  # Authentification (mots de passe hachés PBKDF2)
├── styles.py                 # Palette de couleurs + feuille de style QSS
├── utils.py                  # Validation, reçus, export, sauvegarde
├── requirements.txt
└── ui/
    ├── login_window.py
    ├── main_window.py
    ├── dashboard_widget.py
    ├── students_widget.py
    ├── student_form_dialog.py
    ├── student_detail_dialog.py
    ├── teachers_widget.py
    ├── teacher_form_dialog.py
    ├── classes_widget.py
    ├── events_widget.py
    ├── finances_widget.py
    ├── contacts_widget.py
    └── users_widget.py
```
