import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'sett_wecc.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Création de la table "admin" (sans "s")
cursor.execute('''
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("Table 'admin' créée (si elle n'existait pas).")
