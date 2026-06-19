from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import SalidaTemporal, RegistroAsistencia, Empleado, EventoAsistencia

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

salida = session.get(SalidaTemporal, 1)
asistencia = session.get(RegistroAsistencia, salida.asistencia_id)
empleado = session.get(Empleado, asistencia.empleado_id) if asistencia else None

print(f'Empleado: {empleado.nombre_completo if empleado else "N/A"}')
print(f'Fecha turno: {asistencia.fecha_turno if asistencia else "N/A"}')
print(f'Entrada real: {asistencia.hora_entrada_real if asistencia else "N/A"}')
print(f'Salida real: {asistencia.hora_salida_real if asistencia else "N/A"}')
print(f'Estado registro: {asistencia.estado_registro if asistencia else "N/A"}')

# Buscar eventos de asistencia del día
eventos = session.scalars(
    select(EventoAsistencia).where(
        EventoAsistencia.asistencia_id == asistencia.id
    ).order_by(EventoAsistencia.fecha_evento)
).all()

print(f'\nEventos del día ({len(eventos)}):')
for ev in eventos:
    print(f'  {ev.tipo_evento.value}: {ev.fecha_evento} - {ev.observaciones or ""}')
