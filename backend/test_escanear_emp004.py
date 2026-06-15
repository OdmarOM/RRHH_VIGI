import requests

# Escanear EMP004
response = requests.post("http://localhost:8001/api/v1/caseta/escanear/EMP004")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# También probar el endpoint de test-horario
response2 = requests.get("http://localhost:8001/api/v1/caseta/test-horario/EMP004")
print(f"\nTest horario status: {response2.status_code}")
print(f"Test horario response: {response2.json()}")
