import psycopg2
import psycopg2.extras
import pandas as pd
from contextlib import contextmanager
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from psycopg2 import pool

def get_db_url():
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    return os.getenv("DATABASE_URL")

@st.cache_resource
def get_connection_pool():
    url = get_db_url()
    if not url:
        raise ValueError("DATABASE_URL is not set.")
    # Initialize a thread-safe connection pool with max 20 connections
    return psycopg2.pool.ThreadedConnectionPool(1, 20, url, cursor_factory=psycopg2.extras.DictCursor)

@contextmanager
def get_db_connection():
    pool = get_connection_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Table Users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('Admin', 'User')),
                    last_name TEXT DEFAULT ''
                )
            ''')

            # Table Addresses
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS addresses (
                    id SERIAL PRIMARY KEY,
                    reference TEXT NOT NULL,
                    city TEXT NOT NULL,
                    address TEXT NOT NULL
                )
            ''')

            # Table Trips
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trips (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    total_km REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'Travail',
                    hours REAL DEFAULT 0.0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Table Trip Steps
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trip_steps (
                    id SERIAL PRIMARY KEY,
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
                hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
                cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", ("admin", hashed, "Admin"))
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
                import psycopg2.extras
                psycopg2.extras.execute_values(
                    cursor,
                    "INSERT INTO addresses (reference, city, address) VALUES %s",
                    seed_addresses
                )
                conn.commit()

# --- Fonctions CRUD Utilisateurs ---
def get_user_by_username(username):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cursor.fetchone()

def get_all_users():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role, last_name FROM users")
            return cursor.fetchall()

def create_user(username, password_hash, role, last_name=""):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (username, password_hash, role, last_name) VALUES (%s, %s, %s, %s)", (username, password_hash, role, last_name))
                conn.commit()
                return True
    except psycopg2.IntegrityError:
        return False

def update_user_password(user_id, password_hash):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))
            conn.commit()

def delete_user(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM trip_steps WHERE trip_id IN (SELECT id FROM trips WHERE user_id = %s)", (user_id,))
            cursor.execute("DELETE FROM trips WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()

# --- Fonctions CRUD Adresses ---
def get_all_addresses():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM addresses ORDER BY reference ASC")
            return cursor.fetchall()

def create_address(reference, city, address):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO addresses (reference, city, address) VALUES (%s, %s, %s)", (reference, city, address))
            conn.commit()

def update_address(address_id, reference, city, address):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE addresses SET reference = %s, city = %s, address = %s WHERE id = %s", (reference, city, address, address_id))
            conn.commit()

def delete_address(address_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM addresses WHERE id = %s", (address_id,))
            conn.commit()

# --- Fonctions Trajets ---
def save_trip(user_id, date, total_km, steps, status='Travail', hours=0.0):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO trips (user_id, date, total_km, status, hours) VALUES (%s, %s, %s, %s, %s) RETURNING id", (user_id, date, total_km, status, hours))
            trip_id = cursor.fetchone()[0]
            
            step_records = [(trip_id, order, address_id) for order, address_id in enumerate(steps)]
            import psycopg2.extras
            psycopg2.extras.execute_values(
                cursor,
                "INSERT INTO trip_steps (trip_id, step_order, address_id) VALUES %s",
                step_records
            )
            conn.commit()
            return trip_id

def get_all_trips():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT t.id, t.date, t.total_km, u.username, u.last_name,
                       (SELECT COUNT(*) FROM trip_steps ts WHERE ts.trip_id = t.id) as step_count,
                       (
                           SELECT STRING_AGG(a.reference, ' ➔ ')
                           FROM (
                               SELECT ts.trip_id, a.reference
                               FROM trip_steps ts
                               JOIN addresses a ON ts.address_id = a.id
                               WHERE ts.trip_id = t.id
                               ORDER BY ts.step_order
                           ) a
                       ) as route_details,
                       t.status,
                       t.hours
                FROM trips t 
                JOIN users u ON t.user_id = u.id
                ORDER BY t.date DESC
            ''')
            return cursor.fetchall()

def get_trip_by_user_and_date(user_id, date):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM trips WHERE user_id = %s AND date = %s", (user_id, date))
            return cursor.fetchone()

def get_recorded_dates(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT date FROM trips WHERE user_id = %s", (user_id,))
            rows = cursor.fetchall()
            return [r['date'] for r in rows]

def delete_trip(trip_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM trip_steps WHERE trip_id = %s", (trip_id,))
            cursor.execute("DELETE FROM trips WHERE id = %s", (trip_id,))
            conn.commit()
