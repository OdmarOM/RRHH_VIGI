import requests
from datetime import date
from app.core.database import SessionLocal
from app.models import Empleado

BASE = "http://localhost:8000/api/v1"

# Set employee's fecha_inicio_ciclo to next week (so this week is still week 1?)
# Let's test with 2026-07-06 (one week before). Then for 2026-07-13, semana_ciclo should be 2.
db = SessionLocal()
emp = db.query(Empleado).filter(Empleado.numero_empleado == 'EMP471').first()
print('Before:', emp.fecha_inicio_ciclo)
emp.fecha_inicio_ciclo = date(2026, 7, 6)
db.commit()
print('After:', emp.fecha_inicio_ciclo)

# Login and test
r = requests.post(f"{BASE}/auth/login", json={"username": "super", "password": "super123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

for f in ["2026-07-13", "2026-07-20", "2026-07-27", "2026-08-03"]:
    r = requests.get(f"{BASE}/admin/empleados/70/plantilla-efectiva", headers=headers, params={"fecha": f})
    data = r.json()
    print(f, data.get('semana_ciclo'), data.get('plantilla_efectiva', {}).get('nombre'))

# Reset to plantilla default (null)
emp.fecha_inicio_ciclo = None
db.commit()
print('Reset:', emp.fecha_inicio_ciclo)
