from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, EventoAsistencia, TipoEvento

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("Actualizando visitas pendientes con hora_fin basado en eventos:")
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
    
    # Buscar el primer evento de salida después de la hora de inicio de la visita
    for evento in eventos:
        if evento.tipo_evento == TipoEvento.SALIDA and evento.fecha_evento > v.hora_inicio:
            v.hora_fin = evento.fecha_evento
            v.minutos_duracion = int((evento.fecha_evento - v.hora_inicio).total_seconds() / 60)
            v.motivo = v.motivo or "Visita fuera de horario"
            session.add(v)
            print(f"Actualizada visita ID {v.id}: hora_fin={v.hora_fin}, minutos={v.minutos_duracion}")
            break

session.commit()

print("\nVerificando visitas después de actualizar:")
print("=" * 80)
visitas_con_hora_fin = session.scalars(
    select(Visita).where(Visita.hora_fin.is_not(None))
).all()

print(f"Total visitas con hora_fin: {len(visitas_con_hora_fin)}")
for v in visitas_con_hora_fin:
    print(f"ID: {v.id}, Hora fin: {v.hora_fin}, Minutos: {v.minutos_duracion}, Estado: {v.estado.value}")
