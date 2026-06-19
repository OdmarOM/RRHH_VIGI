from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, RegistroAsistencia, Empleado

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("Relación entre visitas y asistencias:")
print("=" * 80)

visitas = session.scalars(select(Visita)).all()
for v in visitas:
    emp = session.get(Empleado, v.empleado_id)
    asistencia = session.get(RegistroAsistencia, v.asistencia_id)
    print(f"Visita ID: {v.id}")
    print(f"  Empleado: {emp.nombre_completo if emp else 'N/A'}")
    print(f"  Asistencia ID: {v.asistencia_id}")
    print(f"  Fecha asistencia: {asistencia.fecha_turno if asistencia else 'N/A'}")
    print(f"  Hora entrada asistencia: {asistencia.hora_entrada_real if asistencia else 'N/A'}")
    print(f"  Hora salida asistencia: {asistencia.hora_salida_real if asistencia else 'N/A'}")
    print(f"  Fecha visita: {v.fecha_visita}")
    print(f"  Hora inicio visita: {v.hora_inicio}")
    print(f"  Hora fin visita: {v.hora_fin}")
    print(f"  Minutos duración: {v.minutos_duracion}")
    print(f"  Estado: {v.estado.value}")
    print("-" * 80)
