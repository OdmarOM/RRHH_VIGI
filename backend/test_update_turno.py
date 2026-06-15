import requests

# Login para obtener token
login_response = requests.post(
    "http://localhost:8001/api/v1/auth/login",
    json={"username": "admin", "password": "admin"}
)
print(f"Login status: {login_response.status_code}")
if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obtener turnos actuales
    response = requests.get("http://localhost:8001/api/v1/admin/turnos-raw", headers=headers)
    print(f"Turnos status: {response.status_code}")
    turnos = response.json()
    
    # Buscar turno de EMP004 para lunes
    emp004_turno = next((t for t in turnos if t['empleado_id'] == 4 and t['dia_semana'] == 0), None)
    if emp004_turno:
        print(f"Turno EMP004 lunes actual: {emp004_turno}")
        
        # Actualizar turno
        print(f"\nActualizando turno ID {emp004_turno['id']}...")
        update_response = requests.put(
            f"http://localhost:8001/api/v1/admin/turnos/{emp004_turno['id']}",
            json={
                "hora_entrada_oficial": "09:30:00",
                "hora_salida_oficial": "17:00:00"
            },
            headers=headers
        )
        print(f"Update status: {update_response.status_code}")
        print(f"Update response: {update_response.text}")
        
        # Verificar que se actualizó
        response2 = requests.get("http://localhost:8001/api/v1/admin/turnos-raw", headers=headers)
        turnos2 = response2.json()
        emp004_turno2 = next((t for t in turnos2 if t['empleado_id'] == 4 and t['dia_semana'] == 0), None)
        print(f"Turno EMP004 lunes después de actualizar: {emp004_turno2}")
    else:
        print("No se encontró turno de EMP004 para lunes")
else:
    print(f"Login failed: {login_response.text}")
