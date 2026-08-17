import sqlite3
import pandas as pd
from contextlib import contextmanager

DB_NAME = "conciergerie.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Admin', 'User'))
            )
        ''')

        # Table Addresses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT NOT NULL,
                city TEXT NOT NULL,
                address TEXT NOT NULL
            )
        ''')

        # Table Trips
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                total_km REAL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Table Trip Steps
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trip_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                step_order INTEGER NOT NULL,
                address_id INTEGER NOT NULL,
                FOREIGN KEY (trip_id) REFERENCES trips (id),
                FOREIGN KEY (address_id) REFERENCES addresses (id)
            )
        ''')

        conn.commit()

        # Seed data pour le premier administrateur (si la table est vide)
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            import bcrypt
            # Mot de passe par défaut : admin123
            hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", hashed, "Admin"))
            conn.commit()

        # Seed data pour les adresses
        cursor.execute("SELECT COUNT(*) FROM addresses")
        if cursor.fetchone()[0] == 0:
            seed_addresses = [
                ("Local", "Guérande", "69 rue de la maisonneuve"),
                ("Pichavant", "Saint-Nazaire", "55 boulevard de la fraternité"),
                ("Designe", "Guérande", "48 rue du château de careil"),
                ("Hervieux", "Guérande", "48 rue du château de careil"),
                ("Bordais", "Pornichet", "10 avenue de la villès de chevissens"),
                ("Mallet", "La Turballe", "camping les chardons bleus - Boulevard de la grande falaise"),
                ("Millet", "La Turballe", "camping les chardons bleus - Boulevard de la grande falaise"),
                ("Faiella", "La Turballe", "camping les chardons bleus - Boulevard de la grande falaise"),
                ("Santin", "La Baule-Escoublac", "1 impasse alfred bruneau"),
                ("Ardanuy", "La Baule-Escoublac", "65 avenue de lyon"),
                ("Halgand", "Pornichet", "98 avenue de Saint-Sebastien"),
                ("Cartier", "Saint-Nazaire", "16 rue Jean Jaurès"),
                ("Marcon", "Saint-Nazaire", "19 rue Maria Verone"),
                ("Mostini", "La Baule-Escoublac", "4 avenue du Capitaine David"),
                ("Tavares", "Pornichet", "10 avenue de la plage"),
                ("Siebenschuh", "Guérande", "1 rue de l'aire"),
                ("Babonneau", "La Baule-Escoublac", "37 boulevard de l'océan"),
                ("Lavanoux", "Batz-sur-mer", "14 route de Saint-Nudec"),
                ("Vinet", "Saint-Nazaire", "10 rue de Cardurand"),
                ("Pepion", "Pornichet", "10 avenue de la plage"),
                ("Savignac", "La Baule-Escoublac", "2 avenue Lannelongue"),
                ("Le Denmat", "Pornichet", "102 avenue de bonne source"),
                ("Camus", "Le Pouliguen", "6 rue Delestage"),
                ("Miry", "Le Pouliguen", "53 rue de la pierre plate"),
                ("Thibault", "La Baule-Escoublac", "30 avenue Suser"),
                ("Guichard", "Guérande", "18 rue des saulniers"),
                ("Guihard", "La Baule-Escoublac", "35 esplanade Francois André"),
                ("Duchaussoy", "Saint-andré-des-eaux", "9 rue de l'ile du moulin"),
                ("Sancinena", "La Baule-Escoublac", "11 avenue des impairs"),
                ("Auffret", "Pornichet", "12 allée de la Virée Morandais"),
                ("Betscoun", "Guérande", "22 rue de kergonan"),
                ("Guerry", "La Baule-Escoublac", "80 boulevard de l'océan"),
                ("Savary", "Pornichet", "27 avenue des Noës"),
                ("Verde", "Pornichet", "79 avenue des loriettes"),
                ("Rault", "Saint-andré-des-eaux", "32 route d'Avrillac"),
                ("Donnadieu", "Pornichet", "8 allée des pinsons"),
                ("Peniguel", "La Baule-Escoublac", "22 avenue Jean de la fontaine"),
                ("Desponds", "La Baule-Escoublac", "15 avenue des goélands"),
                ("Coquet", "Pornichet", "65 avenue de bonne source"),
                ("Lebeau", "La Baule-Escoublac", "9 boulevard Guy de Champsavin"),
                ("Fourreau", "Pornichet", "120 boulevard des Oceanides"),
                ("Labbé", "Guérande", "2 avenue Paul Gauguin"),
                ("Daudin", "La Baule-Escoublac", "2 quai Rageot de la touche"),
                ("Deschamps", "Pornichet", "2 avenue de la mer"),
                ("Esnault", "Guérande", "16 allée de la torré"),
                ("Cassou", "Pornichet", "118 bis avenue de bonne source"),
                ("Delahaie", "Le Pouliguen", "14 rue de la plage"),
                ("Truffandier", "La Baule-Escoublac", "7 avenue Isabelle"),
                ("Leblond", "Piriac sur mer", "5 impasse des moutonniers"),
                ("Gendry", "Piriac sur mer", "2 rue de la fontaine"),
                ("Niaufre", "Guérande", "279 chemin de la nantaise"),
                ("Cahingt", "La Baule-Escoublac", "5 allée des gnomes"),
                ("Rocher", "La Baule-Escoublac", "4 avenue d'Armorique"),
                ("Odile", "La Baule-Escoublac", "35 boulevard René Dubois")
            ]
            cursor.executemany("INSERT INTO addresses (reference, city, address) VALUES (?, ?, ?)", seed_addresses)
            conn.commit()

# --- Fonctions CRUD Utilisateurs ---
def get_user_by_username(username):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

def get_all_users():
    with get_db_connection() as conn:
        return conn.execute("SELECT id, username, role FROM users").fetchall()

def create_user(username, password_hash, role):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, role))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def update_user_password(user_id, password_hash):
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        conn.commit()

def delete_user(user_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

# --- Fonctions CRUD Adresses ---
def get_all_addresses():
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM addresses ORDER BY reference ASC").fetchall()

def create_address(reference, city, address):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO addresses (reference, city, address) VALUES (?, ?, ?)", (reference, city, address))
        conn.commit()

def update_address(address_id, reference, city, address):
    with get_db_connection() as conn:
        conn.execute("UPDATE addresses SET reference = ?, city = ?, address = ? WHERE id = ?", (reference, city, address, address_id))
        conn.commit()

def delete_address(address_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM addresses WHERE id = ?", (address_id,))
        conn.commit()

# --- Fonctions Trajets ---
def save_trip(user_id, date, total_km, steps):
    """steps est une liste d'IDs d'adresses dans l'ordre d'apparition"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO trips (user_id, date, total_km) VALUES (?, ?, ?)", (user_id, date, total_km))
        trip_id = cursor.lastrowid
        
        step_records = [(trip_id, order, address_id) for order, address_id in enumerate(steps)]
        cursor.executemany("INSERT INTO trip_steps (trip_id, step_order, address_id) VALUES (?, ?, ?)", step_records)
        conn.commit()
        return trip_id

def get_all_trips():
    with get_db_connection() as conn:
        return conn.execute('''
            SELECT t.id, t.date, t.total_km, u.username, 
                   (SELECT COUNT(*) FROM trip_steps ts WHERE ts.trip_id = t.id) as step_count,
                   (
                       SELECT GROUP_CONCAT(a.reference, ' ➔ ') 
                       FROM trip_steps ts 
                       JOIN addresses a ON ts.address_id = a.id 
                       WHERE ts.trip_id = t.id 
                       ORDER BY ts.step_order
                   ) as route_details
            FROM trips t 
            JOIN users u ON t.user_id = u.id
            ORDER BY t.date DESC
        ''').fetchall()

def get_trip_by_user_and_date(user_id, date):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM trips WHERE user_id = ? AND date = ?", (user_id, date)).fetchone()

def delete_trip(trip_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM trip_steps WHERE trip_id = ?", (trip_id,))
        conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        conn.commit()
