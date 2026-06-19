from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, Empleado

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("Visitas pendientes (sin hora_fin):")
print("=" * 80)
visitas_pendientes = session.scalars(
    select(Visita).where(Visita.hora_fin.is_(None))
).all()

for v in visitas_pendientes:
    emp = session.get(Empleado, v.empleado_id)
    print(f"ID: {v.id}")
    print(f"  Empleado: {emp.nombre_completo if emp else 'N/A'} ({v.empleado_id})")
    print(f"  Asistencia ID: {v.asistencia_id}")
    print(f"  Fecha visita: {v.fecha_visita}")
    print(f"  Hora inicio: {v.hora_inicio}")
    print(f"  Hora fin: {v.hora_fin}")
    print(f"  Minutos duración: {v.minutos_duracion}")
    print(f"  Estado: {v.estado.value}")
    print(f"  Motivo: {v.motivo}")
    print("-" * 80)

print(f"\nTotal visitas pendientes: {len(visitas_pendientes)}")
