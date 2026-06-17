import sqlite3

conn = sqlite3.connect(r'c:\Users\SunyLibramineto\Documents\RRHH_APP\backend\rrhh_dev.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tablas = [row[0] for row in cursor.fetchall()]
print("Tablas en la base de datos:")
for tabla in tablas:
    print(f"  - {tabla}")
conn.close()
