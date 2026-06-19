from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date
from app.models import Empleado, TurnoHorario
from app.services import get_empleado_turno

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

emp5 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST005'))
emp6 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST006'))

fecha_test5 = date(2026, 6, 27)  # Viernes
fecha_test6 = date(2026, 6, 30)  # Lunes

print(f'Turno para TEST005 el {fecha_test5} (viernes):')
turno5 = get_empleado_turno(session, emp5, fecha_test5.weekday())
print(f'  {turno5}')

print(f'\nTurno para TEST006 el {fecha_test6} (lunes):')
turno6 = get_empleado_turno(session, emp6, fecha_test6.weekday())
print(f'  {turno6}')

print(f'\nTurnos horarios en base de datos:')
turnos = session.scalars(select(TurnoHorario)).all()
for t in turnos:
    print(f'  Empleado ID: {t.empleado_id}, Día: {t.dia_semana}, Entrada: {t.hora_entrada_oficial}, Salida: {t.hora_salida_oficial}')

print(f'\nIDs de empleados de prueba:')
print(f'  TEST005 ID: {emp5.id}')
print(f'  TEST006 ID: {emp6.id}')

print(f'\nTurnos horarios para TEST005 (ID {emp5.id}):')
turnos_emp5 = session.scalars(select(TurnoHorario).where(TurnoHorario.empleado_id == emp5.id)).all()
for t in turnos_emp5:
    print(f'  Día: {t.dia_semana}, Entrada: {t.hora_entrada_oficial}, Salida: {t.hora_salida_oficial}')

print(f'\nTurnos horarios para TEST006 (ID {emp6.id}):')
turnos_emp6 = session.scalars(select(TurnoHorario).where(TurnoHorario.empleado_id == emp6.id)).all()
for t in turnos_emp6:
    print(f'  Día: {t.dia_semana}, Entrada: {t.hora_entrada_oficial}, Salida: {t.hora_salida_oficial}')
