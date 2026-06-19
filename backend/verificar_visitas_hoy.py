from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, Empleado, RegistroAsistencia
from datetime import datetime, date

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("=" * 80)
print("VISITAS DE HOY")
print("=" * 80)
hoy = date.today()
visitas_hoy = session.scalars(
    select(Visita).where(Visita.fecha_visita >= hoy)
).all()

print(f"Total visitas hoy: {len(visitas_hoy)}")
for v in visitas_hoy:
    emp = session.get(Empleado, v.empleado_id)
    asistencia = session.get(RegistroAsistencia, v.asistencia_id)
    print(f"Visita ID: {v.id}")
    print(f"  Empleado: {emp.nombre_completo if emp else 'N/A'}")
    print(f"  Asistencia ID: {v.asistencia_id}")
    print(f"  Fecha visita: {v.fecha_visita}")
    print(f"  Hora inicio: {v.hora_inicio}")
    print(f"  Hora fin: {v.hora_fin}")
    print(f"  Minutos duración: {v.minutos_duracion}")
    print(f"  Estado: {v.estado.value}")
    print(f"  Motivo: {v.motivo}")
    print(f"  ¿Aparece en panel? {'SÍ' if v.hora_fin else 'NO (falta hora_fin)'}")
    print("-" * 80)

print("\n" + "=" * 80)
print("VISITAS QUE DEBERÍAN APARECER EN PANEL (con hora_fin)")
print("=" * 80)
visitas_con_hora_fin = session.scalars(
    select(Visita).where(Visita.hora_fin.is_not(None))
).all()

print(f"Total visitas con hora_fin: {len(visitas_con_hora_fin)}")
for v in visitas_con_hora_fin:
    emp = session.get(Empleado, v.empleado_id)
    print(f"ID: {v.id}, Empleado: {emp.nombre_completo if emp else 'N/A'}, Hora fin: {v.hora_fin}, Minutos: {v.minutos_duracion}, Estado: {v.estado.value}")
