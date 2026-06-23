import requests
import json

# Primero hacer login para obtener un token
login_url = "http://localhost:8090/api/v1/auth/login"
login_data = {
    "username": "super",
    "password": "admin123"  # Ajusta esto según tu configuración
}

try:
    login_response = requests.post(login_url, json=login_data)
    print(f"Login Status Code: {login_response.status_code}")
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print(f"Token obtenido: {token[:50]}...")
        
        # Ahora probar el endpoint de bloques de horas extra
        bloques_url = "http://localhost:8090/api/v1/admin/bloques-horas-extra"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        bloques_response = requests.get(bloques_url, headers=headers)
        print(f"\nBloques Status Code: {bloques_response.status_code}")
        print(f"Content-Type: {bloques_response.headers.get('Content-Type')}")
        print(f"Raw Response: {bloques_response.text}")
        if bloques_response.text:
            print(f"JSON Response: {json.dumps(bloques_response.json(), indent=2)}")
    else:
        print(f"Login failed: {login_response.text}")
except Exception as e:
    print(f"Error: {e}")
