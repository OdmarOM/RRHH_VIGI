from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, Empleado, RegistroAsistencia, EventoAsistencia, ObservacionCaseta
from datetime import datetime

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("=" * 80)
print("VISITAS RECIENTES (últimas 10)")
print("=" * 80)
visitas = session.scalars(
    select(Visita).order_by(Visita.fecha_visita.desc()).limit(10)
).all()

for v in visitas:
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
    print("-" * 80)

print("\n" + "=" * 80)
print("REGISTROS DE ASISTENCIA RECIENTES (últimos 5)")
print("=" * 80)
asistencias = session.scalars(
    select(RegistroAsistencia).order_by(RegistroAsistencia.fecha_turno.desc()).limit(5)
).all()

for a in asistencias:
    emp = session.get(Empleado, a.empleado_id)
    print(f"Asistencia ID: {a.id}")
    print(f"  Empleado: {emp.nombre_completo if emp else 'N/A'}")
    print(f"  Fecha turno: {a.fecha_turno}")
    print(f"  Hora entrada: {a.hora_entrada_real}")
    print(f"  Hora salida: {a.hora_salida_real}")
    print(f"  Estado registro: {a.estado_registro}")
    print("-" * 80)

print("\n" + "=" * 80)
print("OBSERVACIONES CASETA RECIENTES (últimas 10)")
print("=" * 80)
obs = session.scalars(
    select(ObservacionCaseta).order_by(ObservacionCaseta.fecha_registro.desc()).limit(10)
).all()

for o in obs:
    print(f"Observación ID: {o.id}")
    print(f"  Asistencia ID: {o.asistencia_id}")
    print(f"  Tipo: {o.tipo_observacion}")
    print(f"  Fecha: {o.fecha_registro}")
    print("-" * 80)
