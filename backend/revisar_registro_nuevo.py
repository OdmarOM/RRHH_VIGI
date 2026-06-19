from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date
from app.models import RegistroAsistencia, Empleado, EventoAsistencia

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

emp = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'EMP001'))
fecha_prueba = date(2026, 6, 18)

eventos = session.scalars(select(EventoAsistencia).where(
    EventoAsistencia.empleado_id == emp.id,
    EventoAsistencia.fecha_evento >= fecha_prueba,
    EventoAsistencia.fecha_evento < fecha_prueba.replace(day=fecha_prueba.day + 1)
)).all()

print(f'Eventos para {emp.nombre_completo} el {fecha_prueba}:')
for e in eventos:
    print(f'  {e.tipo_evento.value}: {e.fecha_evento}, Observaciones: {e.observaciones}')

from app.services import calcular_horas_laboradas
resultado = calcular_horas_laboradas(session, emp.id, fecha_prueba)
print(f'\nCálculo:')
print(f'Minutos laborados: {resultado.get("minutos_laborados", 0)}')
print(f'Minutos descanso: {resultado.get("minutos_descanso", 0)}')
print(f'Minutos extra: {resultado.get("minutos_extra", 0)}')
print(f'Horas laboradas: {resultado.get("minutos_laborados", 0) / 60:.2f}')
