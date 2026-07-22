import requests
from datetime import date
from app.core.database import SessionLocal
from app.models import Empleado, TurnoHorario

BASE = "http://localhost:8090/api/v1"

# Login
r = requests.post(f"{BASE}/auth/login", json={"username": "super", "password": "super123"})
r.raise_for_status()
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get current employee state
r = requests.get(f"{BASE}/admin/empleados/70", headers=headers)
emp = r.json()
print("Before:")
print("  plantilla_turno_id:", emp["plantilla_turno_id"])
print("  fecha_inicio_ciclo:", emp["fecha_inicio_ciclo"])

# Test romper plantilla
r = requests.post(f"{BASE}/admin/empleados/70/romper-plantilla", headers=headers)
print("Romper response status:", r.status_code)
print("Romper response body:", r.text)

# Verify employee has no plantilla but has individual shifts
db = SessionLocal()
emp_db = db.get(Empleado, 70)
print("After romper DB:")
print("  plantilla_turno_id:", emp_db.plantilla_turno_id)
print("  fecha_inicio_ciclo:", emp_db.fecha_inicio_ciclo)
turnos = db.query(TurnoHorario).where(TurnoHorario.empleado_id == 70).all()
print("  turnos_individuales:", len(turnos))

# Restore original assignment
pid = emp["plantilla_turno_id"]
fecha_inicio = emp["fecha_inicio_ciclo"]
if pid:
    params = {"fecha_inicio_ciclo": fecha_inicio} if fecha_inicio else {}
    r = requests.put(f"{BASE}/admin/empleados/70/plantilla-turno/{pid}", headers=headers, params=params)
    print("Restaurar plantilla status:", r.status_code)

# Verify restoration
r = requests.get(f"{BASE}/admin/empleados/70", headers=headers)
print("After restore:")
print("  plantilla_turno_id:", r.json()["plantilla_turno_id"])
print("  fecha_inicio_ciclo:", r.json()["fecha_inicio_ciclo"])

db.close()
