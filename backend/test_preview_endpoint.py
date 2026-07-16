import requests

BASE = "http://localhost:8000/api/v1"

# Login
r = requests.post(f"{BASE}/auth/login", json={"username": "super", "password": "super123"})
print('login', r.status_code)
if r.status_code != 200:
    print(r.text)
    exit()
token = r.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Probar diferentes fechas
fechas = ["2026-07-13", "2026-07-20", "2026-07-27", "2026-08-03", "2026-08-10"]
for f in fechas:
    r = requests.get(f"{BASE}/admin/empleados/70/plantilla-efectiva", headers=headers, params={"fecha": f})
    print(f, r.status_code, r.json())
