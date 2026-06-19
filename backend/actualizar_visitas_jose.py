from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Visita, RegistroAsistencia, EventoAsistencia, TipoEvento

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

# Obtener las visitas de JOSE DE JESUS
visitas_jose = session.scalars(
    select(Visita).where(Visita.empleado_id == 1)
).all()

print("Visitas de JOSE DE JESUS antes de actualizar:")
print("=" * 80)
for v in visitas_jose:
    print(f"ID: {v.id}")
    print(f"  Asistencia ID: {v.asistencia_id}")
    print(f"  Hora inicio: {v.hora_inicio}")
    print(f"  Hora fin: {v.hora_fin}")
    print(f"  Minutos duración: {v.minutos_duracion}")
    print(f"  Estado: {v.estado.value}")
    print("-" * 80)

# Para cada visita, intentar calcular hora_fin basado en eventos
for v in visitas_jose:
    if v.hora_fin is None and v.minutos_duracion is None:
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
                v.motivo = "Visita fuera de horario"
                session.add(v)
                print(f"Actualizada visita ID {v.id}: hora_fin={v.hora_fin}, minutos={v.minutos_duracion}")
                break

session.commit()

print("\nVisitas de JOSE DE JESUS después de actualizar:")
print("=" * 80)
visitas_jose_actualizadas = session.scalars(
    select(Visita).where(Visita.empleado_id == 1)
).all()
for v in visitas_jose_actualizadas:
    print(f"ID: {v.id}")
    print(f"  Asistencia ID: {v.asistencia_id}")
    print(f"  Hora inicio: {v.hora_inicio}")
    print(f"  Hora fin: {v.hora_fin}")
    print(f"  Minutos duración: {v.minutos_duracion}")
    print(f"  Estado: {v.estado.value}")
    print(f"  Motivo: {v.motivo}")
    print("-" * 80)
