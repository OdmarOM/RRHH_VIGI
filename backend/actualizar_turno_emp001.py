from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import time
from app.models import Empleado, TurnoHorario

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

emp = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'EMP001'))
if emp:
    turno = session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp.id))
    if turno:
        turno.hora_entrada_oficial = time(8, 0)
        turno.hora_salida_oficial = time(16, 0)
        turno.tolerancia_minutos = 120  # 2 horas de tolerancia para pruebas
        session.commit()
        print('Turno actualizado a 08:00-16:00 con tolerancia de 120 minutos')
    else:
        print('No se encontró turno para EMP001')
else:
    print('No se encontró empleado EMP001')
