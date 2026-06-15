"""
Prueba simple para verificar generación de reportes Excel
"""
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001/api/v1"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "admin"
})
if response.status_code != 200:
    print("ERROR: Login fallido")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Fechas de prueba (últimos 7 días)
hoy = datetime.now()
fecha_fin = hoy.strftime("%Y-%m-%d")
fecha_inicio = (hoy - timedelta(days=7)).strftime("%Y-%m-%d")

print(f"Probando reportes Excel del {fecha_inicio} al {fecha_fin}")
print()

# Probar reporte de horas laboradas
print("1. Probando reporte de horas laboradas...")
params = f"fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}"
response = requests.get(f"{BASE_URL}/admin/reportes/horas-laboradas/excel?{params}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print("   OK: Reporte generado exitosamente")
else:
    print(f"   ERROR: {response.text}")
print()

# Probar reporte de horas extra
print("2. Probando reporte de horas extra...")
response = requests.get(f"{BASE_URL}/admin/reportes/horas-extra/excel?{params}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print("   OK: Reporte generado exitosamente")
else:
    print(f"   ERROR: {response.text}")
print()

# Probar reporte de asistencias
print("3. Probando reporte de asistencias...")
response = requests.get(f"{BASE_URL}/admin/reportes/asistencias/excel?{params}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print("   OK: Reporte generado exitosamente")
else:
    print(f"   ERROR: {response.text}")
print()

print("Pruebas completadas")
