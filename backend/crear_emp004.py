from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import time
from app.models import Empleado, TurnoHorario, Departamento

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

# Buscar departamento
dept = session.scalar(select(Departamento).where(Departamento.nombre == "Operaciones"))
if not dept:
    dept = Departamento(nombre="Operaciones")
    session.add(dept)
    session.flush()

# Crear empleado EMP004
emp = session.scalar(select(Empleado).where(Empleado.numero_empleado == "EMP004"))
if not emp:
    emp = Empleado(
        numero_empleado="EMP004",
        nombre_completo="Test Ausencias",
        departamento_id=dept.id,
        puesto="Empleado de Pruebas",
        activo=True
    )
    session.add(emp)
    session.flush()
    
    # Crear turnos para cada día de la semana (0=Lunes, 6=Domingo)
    for dia in range(7):
        turno = TurnoHorario(
            empleado_id=emp.id,
            dia_semana=dia,
            hora_entrada_oficial=time(8, 0),
            hora_salida_oficial=time(16, 0),
            tolerancia_minutos=60
        )
        session.add(turno)
    session.commit()
    print('Empleado EMP004 creado exitosamente con turno Matutino para todos los días')
else:
    print('Empleado EMP004 ya existe')
