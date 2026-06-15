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
    
    # Probar endpoint de visitas
    response = requests.get("http://localhost:8001/api/v1/caseta/visitas", headers=headers)
    print(f"Visitas status: {response.status_code}")
    print(f"Visitas response: {response.text}")
else:
    print(f"Login failed: {login_response.text}")
