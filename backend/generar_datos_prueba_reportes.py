"""
Generar datos de prueba para reportes Excel y descargar los archivos
"""
import requests
from datetime import datetime, timedelta
import os

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

# Obtener empleados
response = requests.get(f"{BASE_URL}/admin/empleados", headers=headers)
empleados = response.json()
print(f"Empleados encontrados: {len(empleados)}")

if not empleados:
    print("ERROR: No hay empleados en la base de datos")
    exit(1)

# Fechas de prueba (últimos 7 días)
hoy = datetime.now()
fecha_fin = hoy.strftime("%Y-%m-%d")
fecha_inicio = (hoy - timedelta(days=7)).strftime("%Y-%m-%d")

print(f"\nGenerando datos de prueba del {fecha_inicio} al {fecha_fin}")

# Generar registros de asistencia de prueba
print("\n1. Generando registros de asistencia...")
empleado = empleados[0]
empleado_id = empleado['id']

fecha_actual = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
while fecha_actual <= datetime.strptime(fecha_fin, "%Y-%m-%d").date():
    # Solo días laborables (lunes a viernes)
    if fecha_actual.weekday() < 5:
        # Crear registro de asistencia
        hora_entrada = datetime.combine(fecha_actual, datetime.min.time()) + timedelta(hours=9)
        hora_salida = hora_entrada + timedelta(hours=8)
        
        response = requests.post(f"{BASE_URL}/caseta/escanear", json={
            "numero_empleado": empleado['numero_empleado'],
            "tipo_evento": "entrada"
        })
        
        if response.status_code == 200:
            asistencia_id = response.json().get('asistencia_id')
            if asistencia_id:
                # Simular salida
                requests.post(f"{BASE_URL}/caseta/escanear", json={
                    "numero_empleado": empleado['numero_empleado'],
                    "tipo_evento": "salida"
                })
                print(f"   - {fecha_actual.strftime('%Y-%m-%d')}: Asistencia registrada")
    
    fecha_actual += timedelta(days=1)

# Generar horas extra (aprobar algunas)
print("\n2. Aprobando horas extra...")
response = requests.get(f"{BASE_URL}/admin/incidencias/horas-extra-pendientes", headers=headers)
if response.status_code == 200:
    pendientes = response.json()
    for pendiente in pendientes[:3]:  # Aprobar hasta 3
        requests.put(f"{BASE_URL}/admin/incidencias/horas-extra/{pendiente['id']}/aprobar-rrhh", headers=headers)
        print(f"   - Horas extra aprobadas para asistencia {pendiente['id']}")

# Directorio para guardar archivos Excel
output_dir = os.path.join(os.path.dirname(__file__), "reportes_excel_prueba")
os.makedirs(output_dir, exist_ok=True)

# Descargar reportes
print(f"\n3. Descargando reportes Excel a: {output_dir}")

# Reporte horas laboradas
params = f"fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}"
response = requests.get(f"{BASE_URL}/admin/reportes/horas-laboradas/excel?{params}", headers=headers)
if response.status_code == 200:
    filepath = os.path.join(output_dir, f"horas_laboradas_{fecha_inicio}_{fecha_fin}.xlsx")
    with open(filepath, 'wb') as f:
        f.write(response.content)
    print(f"   OK Horas laboradas: {filepath}")
else:
    print(f"   ERROR Horas laboradas: {response.text}")

# Reporte horas extra
response = requests.get(f"{BASE_URL}/admin/reportes/horas-extra/excel?{params}", headers=headers)
if response.status_code == 200:
    filepath = os.path.join(output_dir, f"horas_extra_{fecha_inicio}_{fecha_fin}.xlsx")
    with open(filepath, 'wb') as f:
        f.write(response.content)
    print(f"   OK Horas extra: {filepath}")
else:
    print(f"   ERROR Horas extra: {response.text}")

# Reporte asistencias
response = requests.get(f"{BASE_URL}/admin/reportes/asistencias/excel?{params}", headers=headers)
if response.status_code == 200:
    filepath = os.path.join(output_dir, f"asistencias_{fecha_inicio}_{fecha_fin}.xlsx")
    with open(filepath, 'wb') as f:
        f.write(response.content)
    print(f"   OK Asistencias: {filepath}")
else:
    print(f"   ERROR Asistencias: {response.text}")

print(f"\nOK Datos de prueba generados y archivos Excel descargados")
print(f"  Ubicacion: {output_dir}")
