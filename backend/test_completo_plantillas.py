import requests
import sys
from datetime import date
from app.core.database import SessionLocal
from app.models import Empleado, PlantillaTurno, TurnoHorario, DetallePlantillaTurno

BASE = "http://localhost:8000/api/v1"
TOKEN = None

def login():
    global TOKEN
    r = requests.post(f"{BASE}/auth/login", json={"username": "super", "password": "super123"})
    assert r.status_code == 200, f"Login falló: {r.text}"
    TOKEN = r.json()["access_token"]


def h():
    return {"Authorization": f"Bearer {TOKEN}"}


def crear_empleado(numero, nombre, departamento_id=1, puesto="Operador"):
    payload = {"numero_empleado": numero, "nombre_completo": nombre, "departamento_id": departamento_id, "puesto": puesto}
    r = requests.post(f"{BASE}/admin/empleados", json=payload, headers=h())
    assert r.status_code == 200, f"Crear empleado falló: {r.text}"
    return r.json()


def eliminar_empleado(emp_id):
    r = requests.delete(f"{BASE}/admin/empleados/{emp_id}", headers=h())
    assert r.status_code == 200, f"Eliminar empleado falló: {r.text}"


def crear_plantilla(nombre, es_rotativa=False, ciclo=2, fecha_inicio=None, sem_par=None, sem_impar=None, sem_3=None):
    params = {
        "nombre": nombre,
        "descripcion": "Prueba",
        "es_rotativa": es_rotativa,
        "ciclo_rotacion_semanas": ciclo,
        "fecha_inicio_ciclo": fecha_inicio.isoformat() if fecha_inicio else None,
        "plantilla_semana_par_id": sem_par,
        "plantilla_semana_impar_id": sem_impar,
        "plantilla_semana_3_id": sem_3
    }
    r = requests.post(f"{BASE}/admin/plantillas-turnos", params=params, headers=h())
    assert r.status_code == 200, f"Crear plantilla falló: {r.text}"
    return r.json()


def eliminar_plantilla(pid):
    r = requests.delete(f"{BASE}/admin/plantillas-turnos/{pid}", headers=h())
    if r.status_code != 200:
        print(f"  [WARN] No se pudo eliminar plantilla {pid}: {r.status_code} {r.text}")


def agregar_detalle(pid, dia, entrada, salida, es_descanso=False):
    payload = {"dia_semana": dia, "hora_entrada": entrada, "hora_salida": salida, "tolerancia": 15, "es_descanso": es_descanso}
    r = requests.post(f"{BASE}/admin/plantillas-turnos/{pid}/detalles", json=payload, headers=h())
    assert r.status_code == 200, f"Agregar detalle falló: {r.text}"


def asignar_plantilla(emp_id, pid, fecha_inicio=None):
    params = {"fecha_inicio_ciclo": fecha_inicio.isoformat() if fecha_inicio else None}
    r = requests.put(f"{BASE}/admin/empleados/{emp_id}/plantilla-turno/{pid}", params=params, headers=h())
    assert r.status_code == 200, f"Asignar plantilla falló: {r.text}"


def plantilla_efectiva(emp_id, fecha=None):
    params = {"fecha": fecha.isoformat() if fecha else None}
    r = requests.get(f"{BASE}/admin/empleados/{emp_id}/plantilla-efectiva", params=params, headers=h())
    assert r.status_code == 200, f"Plantilla efectiva falló: {r.text}"
    return r.json()


def romper_plantilla(emp_id):
    r = requests.post(f"{BASE}/admin/empleados/{emp_id}/romper-plantilla", headers=h())
    assert r.status_code == 200, f"Romper plantilla falló: {r.text}"


def cleanup():
    db = SessionLocal()
    try:
        db.execute(Empleado.__table__.delete().where(Empleado.numero_empleado.like("TEST%")))
        db.execute(PlantillaTurno.__table__.delete().where(PlantillaTurno.nombre.like("Test%")))
        db.commit()
    finally:
        db.close()


def assert_eq(a, b, msg):
    if a != b:
        print(f"  [FAIL] {msg}: esperado {b}, obtenido {a}")
        sys.exit(1)
    print(f"  [OK] {msg}: {b}")


def main():
    print("Iniciando pruebas completas...")
    login()
    cleanup()

    # Crear plantillas base
    print("\n1. Creando plantillas base...")
    matutino = crear_plantilla("Test Matutino")
    agregar_detalle(matutino["id"], 0, "08:00", "16:00")
    vespertino = crear_plantilla("Test Vespertino")
    agregar_detalle(vespertino["id"], 0, "14:00", "22:00")
    turno_medio = crear_plantilla("Test Medio")
    agregar_detalle(turno_medio["id"], 0, "10:00", "18:00")
    no_rot = crear_plantilla("Test No Rotativa")
    agregar_detalle(no_rot["id"], 0, "07:00", "15:00")

    # Plantilla rotativa 2 semanas
    print("\n2. Creando plantilla rotativa 2 semanas...")
    rot2 = crear_plantilla("Test Rotativa 2 Sem", es_rotativa=True, ciclo=2, fecha_inicio=date(2026, 7, 13), sem_impar=matutino["id"], sem_par=vespertino["id"])

    # Plantilla rotativa 3 semanas
    print("\n3. Creando plantilla rotativa 3 semanas...")
    rot3 = crear_plantilla("Test Rotativa 3 Sem", es_rotativa=True, ciclo=3, fecha_inicio=date(2026, 7, 13), sem_impar=matutino["id"], sem_par=vespertino["id"], sem_3=turno_medio["id"])

    # Escenario A: No rotativa
    print("\n4. Escenario A: Plantilla no rotativa")
    empA = crear_empleado("TESTA", "Empleado A")
    asignar_plantilla(empA["id"], no_rot["id"])
    res = plantilla_efectiva(empA["id"], date(2026, 7, 13))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test No Rotativa", "No rotativa 13 jul")
    res = plantilla_efectiva(empA["id"], date(2026, 7, 20))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test No Rotativa", "No rotativa 20 jul")
    assert_eq(res["es_rotativa"], False, "No rotativa flag")

    # Escenario B: Rotativa 2 semanas, fechas default
    print("\n5. Escenario B: Rotativa 2 semanas default")
    empB = crear_empleado("TESTB", "Empleado B")
    asignar_plantilla(empB["id"], rot2["id"])
    res = plantilla_efectiva(empB["id"], date(2026, 7, 13))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "Rot2 13 jul (impar)")
    res = plantilla_efectiva(empB["id"], date(2026, 7, 20))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Vespertino", "Rot2 20 jul (par)")
    res = plantilla_efectiva(empB["id"], date(2026, 7, 27))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "Rot2 27 jul (impar)")

    # Escenario C: Rotativa 2 semanas con fecha_inicio_ciclo propia del empleado
    print("\n6. Escenario C: Rotativa 2 semanas con inicio de ciclo empleado 2026-07-20")
    empC = crear_empleado("TESTC", "Empleado C")
    asignar_plantilla(empC["id"], rot2["id"], fecha_inicio=date(2026, 7, 20))
    res = plantilla_efectiva(empC["id"], date(2026, 7, 13))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Vespertino", "Rot2 empC 13 jul (par respecto a 20)")
    res = plantilla_efectiva(empC["id"], date(2026, 7, 20))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "Rot2 empC 20 jul (impar respecto a 20)")
    res = plantilla_efectiva(empC["id"], date(2026, 7, 27))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Vespertino", "Rot2 empC 27 jul (par respecto a 20)")

    # Escenario D: Rotativa 3 semanas default
    print("\n7. Escenario D: Rotativa 3 semanas default")
    empD = crear_empleado("TESTD", "Empleado D")
    asignar_plantilla(empD["id"], rot3["id"])
    res = plantilla_efectiva(empD["id"], date(2026, 7, 13))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "Rot3 13 jul (sem1)")
    res = plantilla_efectiva(empD["id"], date(2026, 7, 20))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Vespertino", "Rot3 20 jul (sem2)")
    res = plantilla_efectiva(empD["id"], date(2026, 7, 27))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Medio", "Rot3 27 jul (sem3)")
    res = plantilla_efectiva(empD["id"], date(2026, 8, 3))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "Rot3 3 ago (sem1)")

    # Escenario E: Rotativa 3 semanas con fecha empleado desfasada
    print("\n8. Escenario E: Rotativa 3 semanas con inicio 2026-07-06")
    empE = crear_empleado("TESTE", "Empleado E")
    asignar_plantilla(empE["id"], rot3["id"], fecha_inicio=date(2026, 7, 6))
    res = plantilla_efectiva(empE["id"], date(2026, 7, 13))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Vespertino", "Rot3 empE 13 jul (sem2)")
    res = plantilla_efectiva(empE["id"], date(2026, 7, 20))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Medio", "Rot3 empE 20 jul (sem3)")
    res = plantilla_efectiva(empE["id"], date(2026, 7, 27))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "Rot3 empE 27 jul (sem1)")

    # Escenario F: Empleados B y E con misma plantilla pero rotaciones independientes
    print("\n9. Escenario F: Misma plantilla, diferentes inicios")
    resB = plantilla_efectiva(empB["id"], date(2026, 7, 13))
    resE = plantilla_efectiva(empE["id"], date(2026, 7, 13))
    assert_eq(resB["plantilla_efectiva"]["nombre"], "Test Matutino", "EmpB 13 jul")
    assert_eq(resE["plantilla_efectiva"]["nombre"], "Test Vespertino", "EmpE 13 jul")
    assert_eq(resB["fecha_inicio_ciclo"], "2026-07-13", "EmpB inicio default")
    assert_eq(resE["fecha_inicio_ciclo"], "2026-07-06", "EmpE inicio propio")

    # Escenario G: Modificar fecha_inicio_ciclo del empleado
    print("\n10. Escenario G: Modificar fecha_inicio_ciclo del empleado E")
    asignar_plantilla(empE["id"], rot3["id"], fecha_inicio=date(2026, 7, 13))
    res = plantilla_efectiva(empE["id"], date(2026, 7, 13))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "EmpE 13 jul luego de cambiar inicio")
    res = plantilla_efectiva(empE["id"], date(2026, 7, 27))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Medio", "EmpE 27 jul luego de cambiar inicio")

    # Escenario H: Romper referencia de plantilla rotativa
    print("\n11. Escenario H: Romper referencia de plantilla rotativa")
    empH = crear_empleado("TESTH", "Empleado H")
    asignar_plantilla(empH["id"], rot2["id"], fecha_inicio=date(2026, 7, 13))
    res = plantilla_efectiva(empH["id"], date(2026, 7, 13))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "EmpH antes de romper")
    romper_plantilla(empH["id"])
    res = plantilla_efectiva(empH["id"])
    assert_eq(res["plantilla_efectiva"], None, "EmpH sin plantilla tras romper")
    db = SessionLocal()
    try:
        turnos = db.query(TurnoHorario).where(TurnoHorario.empleado_id == empH["id"]).all()
        assert_eq(len(turnos), 1, "EmpH tiene 1 turno individual creado")
        assert_eq(turnos[0].hora_entrada_oficial.strftime("%H:%M"), "08:00", "EmpH turno entrada 08:00")
    finally:
        db.close()

    # Escenario I: Asignar plantilla a empleado que ya tenía turnos individuales
    print("\n12. Escenario I: Asignar plantilla rotativa a empleado con turnos individuales")
    empI = crear_empleado("TESTI", "Empleado I")
    payload = {"empleado_id": empI["id"], "dia_semana": 0, "hora_entrada_oficial": "09:00", "hora_salida_oficial": "17:00", "tolerancia_minutos": 15}
    r = requests.post(f"{BASE}/admin/turnos", json=payload, headers=h())
    assert r.status_code == 200, f"Crear turno individual falló: {r.text}"
    asignar_plantilla(empI["id"], rot2["id"], fecha_inicio=date(2026, 7, 13))
    res = plantilla_efectiva(empI["id"], date(2026, 7, 13))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "EmpI plantilla asignada")
    db = SessionLocal()
    try:
        turnos = db.query(TurnoHorario).where(TurnoHorario.empleado_id == empI["id"]).all()
        assert_eq(len(turnos), 0, "EmpI turnos individuales eliminados")
    finally:
        db.close()

    # Escenario J: Modificar fecha_inicio_ciclo a traves de actualizar empleado
    print("\n13. Escenario J: Actualizar fecha_inicio_ciclo via EmpleadoUpdate")
    r = requests.put(f"{BASE}/admin/empleados/{empC['id']}", json={"fecha_inicio_ciclo": "2026-07-27"}, headers=h())
    assert r.status_code == 200, f"Actualizar empleado falló: {r.text}"
    empC_actualizado = r.json()
    assert_eq(empC_actualizado["fecha_inicio_ciclo"], "2026-07-27", "EmpleadoUpdate fecha_inicio_ciclo")
    res = plantilla_efectiva(empC["id"], date(2026, 7, 27))
    assert_eq(res["plantilla_efectiva"]["nombre"], "Test Matutino", "EmpC 27 jul es ahora sem1")

    # Limpieza
    print("\n14. Limpieza...")
    for emp_id in [empA["id"], empB["id"], empC["id"], empD["id"], empE["id"], empH["id"], empI["id"]]:
        eliminar_empleado(emp_id)
    for pid in [rot2["id"], rot3["id"], no_rot["id"], matutino["id"], vespertino["id"], turno_medio["id"]]:
        eliminar_plantilla(pid)

    print("\n" + "="*60)
    print("TODAS LAS PRUEBAS PASARON")
    print("="*60)


if __name__ == "__main__":
    main()
