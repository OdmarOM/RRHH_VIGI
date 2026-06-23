import requests
import json

# Prueba del endpoint /api/v1/admin/bloques-horas-extra
url = "http://localhost:8090/api/v1/admin/bloques-horas-extra"

# Token de autenticación (necesario para endpoints de admin)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdXBlcnVzdWFyaW8iLCJyb2xlIjoiU3VwZXJ1c3VhcmlvIiwiZXhwIjoxNzUwOTYxNjAwfQ.example"

headers = {
    "Authorization": f"Bearer {token}"
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Raw Response: {response.text}")
    if response.text:
        print(f"JSON Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
