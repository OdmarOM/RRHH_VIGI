from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models import Visita, EventoAsistencia, TipoEvento

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("Actualizando visitas pendientes:")
print("=" * 80)

visitas_pendientes = session.scalars(
    select(Visita).where(Visita.hora_fin.is_(None))
).all()

for v in visitas_pendientes:
    # Obtener eventos de la asistencia asociada
    eventos = session.scalars(
        select(EventoAsistencia).where(
            EventoAsistencia.asistencia_id == v.asistencia_id
        ).order_by(EventoAsistencia.fecha_evento)
    ).all()
    
    # Buscar el último evento de salida después de la hora de inicio
    for evento in eventos:
        if evento.tipo_evento == TipoEvento.SALIDA and evento.fecha_evento > v.hora_inicio:
            v.hora_fin = evento.fecha_evento
            v.minutos_duracion = int((evento.fecha_evento - v.hora_inicio).total_seconds() / 60)
            v.motivo = v.motivo or "Visita fuera de horario"
            session.add(v)
            print(f"Actualizada visita ID {v.id}: hora_fin={v.hora_fin}, minutos={v.minutos_duracion}")
            break

session.commit()

print("\nVisitas después de actualizar:")
print("=" * 80)
visitas_actualizadas = session.scalars(
    select(Visita).where(Visita.hora_fin.is_not(None))
).all()

for v in visitas_actualizadas:
    print(f"ID: {v.id}, Hora fin: {v.hora_fin}, Minutos: {v.minutos_duracion}, Estado: {v.estado.value}")

print(f"\nTotal visitas actualizadas: {len(visitas_actualizadas)}")
