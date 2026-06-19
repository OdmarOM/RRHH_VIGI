from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, RegistroAsistencia, EventoAsistencia, Empleado
from datetime import datetime, date

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("=" * 80)
print("REGISTROS DE ASISTENCIA DE HOY (2026-07-01)")
print("=" * 80)
hoy = date(2026, 7, 1)
asistencias_hoy = session.scalars(
    select(RegistroAsistencia).where(RegistroAsistencia.fecha_turno == hoy)
).all()

print(f"Total asistencias de hoy: {len(asistencias_hoy)}")
for a in asistencias_hoy:
    emp = session.get(Empleado, a.empleado_id)
    print(f"Asistencia ID: {a.id}")
    print(f"  Empleado: {emp.nombre_completo if emp else 'N/A'}")
    print(f"  Hora entrada: {a.hora_entrada_real}")
    print(f"  Hora salida: {a.hora_salida_real}")
    print(f"  Estado registro: {a.estado_registro}")
    
    # Mostrar eventos
    eventos = session.scalars(
        select(EventoAsistencia).where(EventoAsistencia.asistencia_id == a.id)
        .order_by(EventoAsistencia.fecha_evento)
    ).all()
    print(f"  Eventos ({len(eventos)}):")
    for e in eventos:
        print(f"    {e.tipo_evento.value}: {e.fecha_evento} - {e.observaciones}")
    print("-" * 80)

print("\n" + "=" * 80)
print("VISITAS DE HOY (2026-07-01)")
print("=" * 80)
visitas_hoy = session.scalars(
    select(Visita).where(Visita.fecha_visita >= datetime.combine(hoy, datetime.min.time()))
).all()

print(f"Total visitas de hoy: {len(visitas_hoy)}")
for v in visitas_hoy:
    emp = session.get(Empleado, v.empleado_id)
    print(f"Visita ID: {v.id}")
    print(f"  Empleado: {emp.nombre_completo if emp else 'N/A'}")
    print(f"  Hora inicio: {v.hora_inicio}")
    print(f"  Hora fin: {v.hora_fin}")
    print(f"  Minutos duración: {v.minutos_duracion}")
    print(f"  Estado: {v.estado.value}")
    print("-" * 80)
