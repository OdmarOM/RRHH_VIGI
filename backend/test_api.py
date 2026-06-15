"""
Pruebas básicas para verificar las funcionalidades del sistema RRHH
Ejecutar con: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def test_login():
    """Prueba de login"""
    print("\n=== Prueba de Login ===")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("OK Login exitoso")
        return token
    else:
        print("ERROR Login fallido")
        return None

def test_get_departamentos(token):
    """Prueba de obtener departamentos"""
    print("\n=== Prueba de Obtener Departamentos ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/departamentos", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"OK Departamentos obtenidos: {len(response.json())}")
    else:
        print("ERROR Error al obtener departamentos")

def test_get_empleados(token):
    """Prueba de obtener empleados"""
    print("\n=== Prueba de Obtener Empleados ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/empleados", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"OK Empleados obtenidos: {len(response.json())}")
    else:
        print("ERROR Error al obtener empleados")

def test_get_turnos(token):
    """Prueba de obtener turnos"""
    print("\n=== Prueba de Obtener Turnos ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/turnos", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"OK Turnos obtenidos: {len(response.json())}")
    else:
        print("ERROR Error al obtener turnos")

def test_get_plantillas(token):
    """Prueba de obtener plantillas"""
    print("\n=== Prueba de Obtener Plantillas ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/plantillas-turnos", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"OK Plantillas obtenidas: {len(response.json())}")
    else:
        print("ERROR Error al obtener plantillas")

def test_get_usuarios_sistema(token):
    """Prueba de obtener usuarios del sistema"""
    print("\n=== Prueba de Obtener Usuarios del Sistema ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/usuarios-sistema", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"OK Usuarios del sistema obtenidos: {len(response.json())}")
    else:
        print("ERROR Error al obtener usuarios del sistema")

def test_get_roles(token):
    """Prueba de obtener roles"""
    print("\n=== Prueba de Obtener Roles ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/roles", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"OK Roles obtenidos: {len(response.json())}")
        for rol in response.json():
            print(f"   - {rol['nombre']} (ID: {rol['id']})")
    else:
        print("ERROR Error al obtener roles")

def test_get_supervisores_departamentos(token):
    """Prueba de obtener relaciones supervisor-departamento"""
    print("\n=== Prueba de Obtener Relaciones Supervisor-Departamento ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/supervisores-departamentos", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"OK Relaciones obtenidas: {len(response.json())}")
    else:
        print("ERROR Error al obtener relaciones")

def test_crear_departamento(token):
    """Prueba de crear departamento"""
    print("\n=== Prueba de Crear Departamento ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/admin/departamentos", 
                            params={"nombre": "Prueba Test"},
                            headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("OK Departamento creado exitosamente")
    else:
        print("ERROR Error al crear departamento")

def test_crear_empleado(token):
    """Prueba de crear empleado"""
    print("\n=== Prueba de Crear Empleado ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/admin/empleados", 
                            json={
                                "numero_empleado": "999",
                                "nombre_completo": "Empleado Prueba",
                                "departamento_id": 1,
                                "puesto": "Puesto Prueba"
                            },
                            headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("OK Empleado creado exitosamente")
        return response.json()["id"]
    else:
        print("ERROR Error al crear empleado")
        return None

def test_activar_desactivar_empleado(token, empleado_id):
    """Prueba de activar/desactivar empleado"""
    print("\n=== Prueba de Activar/Desactivar Empleado ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(f"{BASE_URL}/admin/empleados/{empleado_id}/activo",
                           params={"activo": False},
                           headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("OK Empleado desactivado exitosamente")
    else:
        print("ERROR Error al desactivar empleado")

def main():
    print("=== Iniciando Pruebas del Sistema RRHH ===")
    print(f"Base URL: {BASE_URL}")
    
    # Login
    token = test_login()
    if not token:
        print("No se pudo obtener token, deteniendo pruebas")
        return
    
    # Pruebas de lectura
    test_get_departamentos(token)
    test_get_empleados(token)
    test_get_turnos(token)
    test_get_plantillas(token)
    test_get_usuarios_sistema(token)
    test_get_roles(token)
    test_get_supervisores_departamentos(token)
    
    # Pruebas de escritura
    test_crear_departamento(token)
    empleado_id = test_crear_empleado(token)
    if empleado_id:
        test_activar_desactivar_empleado(token, empleado_id)
    
    print("\n=== Pruebas Completadas ===")

if __name__ == "__main__":
    main()
