from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import RegistroAsistencia, Empleado
from app.services import calcular_horas_laboradas

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

regs = session.scalars(select(RegistroAsistencia).where(RegistroAsistencia.fecha_turno == '2026-06-18')).all()
for reg in regs:
    emp = session.get(Empleado, reg.empleado_id)
    info = calcular_horas_laboradas(session, reg.empleado_id, reg.fecha_turno)
    print(f'Empleado: {emp.nombre_completo}')
    print(f'  Minutos laborados: {info["minutos_laborados"]}')
    print(f'  Horas laboradas: {info["minutos_laborados"]/60:.2f}')
    print(f'  Minutos descanso: {info["minutos_descanso"]}')
    print(f'  Minutos extra: {info["minutos_extra"]}')
