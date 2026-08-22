# Application de Conciergerie

Une application web complète pour une conciergerie, permettant de gérer les trajets des salarié(e)s, utilisant Streamlit, SQLite, et l'API Google Maps.

## Installation et Utilisation

1. **Prérequis :** Assurez-vous d'avoir Python 3.8+ installé.
2. **Installation des dépendances :**
   ```bash
   pip install -r requirements.txt
   ```
3. **Clé API Google Maps :**
   - Créez un fichier `.env` à la racine du projet (le même dossier que `app.py`).
   - Ajoutez-y votre clé d'API Google Maps avec la ligne suivante :
     ```env
     GOOGLE_MAPS_API_KEY=votre_cle_api_ici
     ```
   - Si la clé n'est pas fournie, les distances calculées seront par défaut de `0.0 km`.
4. **Lancement de l'application :**
   ```bash
   streamlit run app.py
   ```
5. **Connexion par défaut :**
   - L'application créera automatiquement la base de données `conciergerie.db` au premier lancement.
   - Les adresses de base y seront importées.
   - Un compte administrateur sera créé :
     - **Nom d'utilisateur :** admin
     - **Mot de passe :** admin123

L'administrateur peut ensuite se connecter pour créer les comptes des "Salariés" (rôle "User").
