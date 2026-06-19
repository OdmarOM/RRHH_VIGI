from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Empleado, TurnoHorario, Departamento
from datetime import time

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("Creando turnos para empleados de prueba:")
print("=" * 80)

# Obtener departamento de pruebas
dept = session.scalar(select(Departamento).where(Departamento.nombre == 'Pruebas'))
if not dept:
    dept = Departamento(nombre='Pruebas')
    session.add(dept)
    session.flush()

# Crear turnos para Empleado Prueba 7
emp7 = session.scalar(select(Empleado).where(Empleado.nombre_completo == 'Empleado Prueba 7'))
if emp7:
    # Verificar si ya tiene turno
    turno_existente = session.scalar(
        select(TurnoHorario).where(
            TurnoHorario.empleado_id == emp7.id,
            TurnoHorario.dia_semana == 1  # Martes (2026-07-01 es martes)
        )
    )
    if not turno_existente:
        turno = TurnoHorario(
            empleado_id=emp7.id,
            dia_semana=1,  # Martes
            hora_entrada_oficial=time(8, 0),
            hora_salida_oficial=time(16, 0),
            tolerancia_minutos=15
        )
        session.add(turno)
        print(f"Creado turno para {emp7.nombre_completo}: 08:00 - 16:00")
    else:
        print(f"{emp7.nombre_completo} ya tiene turno")

session.commit()
print("Turnos creados exitosamente")
