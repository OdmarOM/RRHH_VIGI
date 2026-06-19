from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Empleado, TurnoHorario, DetallePlantillaTurno, PlantillaTurno

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

emp = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'EMP001'))
print(f'Empleado: {emp.nombre_completo}')
print(f'Plantilla ID: {emp.plantilla_turno_id}')

turno = session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp.id))
if turno:
    print(f'Turno individual: {turno.hora_entrada_oficial}-{turno.hora_salida_oficial}')
else:
    print('Sin turno individual')

plantilla = session.get(PlantillaTurno, emp.plantilla_turno_id) if emp.plantilla_turno_id else None
if plantilla:
    print(f'Plantilla: {plantilla.nombre}')
    detalles = session.scalars(select(DetallePlantillaTurno).where(DetallePlantillaTurno.plantilla_id == plantilla.id)).all()
    for d in detalles:
        print(f'  Dia {d.dia_semana}: {d.hora_entrada_oficial}-{d.hora_salida_oficial}, Tolerancia: {d.tolerancia_minutos}')
