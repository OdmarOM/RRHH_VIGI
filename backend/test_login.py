import requests

try:
    response = requests.post(
        "http://localhost:8001/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
