import sqlite3

conn = sqlite3.connect(r'c:\Users\SunyLibramineto\Documents\RRHH_APP\backend\rrhh_dev.db')
cursor = conn.cursor()

print("=== Estructura de plantillas_turnos ===")
cursor.execute("PRAGMA table_info(plantillas_turnos)")
for col in cursor.fetchall():
    print(f"  {col}")

print("\n=== Estructura de turnos_horarios ===")
cursor.execute("PRAGMA table_info(turnos_horarios)")
for col in cursor.fetchall():
    print(f"  {col}")

print("\n=== Estructura de detalles_plantilla_turno ===")
cursor.execute("PRAGMA table_info(detalles_plantilla_turno)")
for col in cursor.fetchall():
    print(f"  {col}")

conn.close()
