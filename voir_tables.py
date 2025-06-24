import sqlite3
import os

# Construire le chemin vers la base dans instance
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'sett_wecc.db')

# Connexion à la base
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Exemple : afficher les tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables dans la base :")
for table in tables:
    print(table[0])

conn.close()
