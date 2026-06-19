from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date
from app.models import RegistroAsistencia, Empleado, SalidaTemporal
from app.services import calcular_horas_laboradas

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

emp = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'EMP001'))
fecha_prueba = date(2026, 6, 18)
reg = session.scalar(select(RegistroAsistencia).where(
    RegistroAsistencia.empleado_id == emp.id, 
    RegistroAsistencia.fecha_turno == fecha_prueba
))

print(f'Registro: {reg.hora_entrada_real} - {reg.hora_salida_real}')
print(f'Estado: {reg.estado_registro}')

salidas = session.scalars(select(SalidaTemporal).where(SalidaTemporal.asistencia_id == reg.id)).all()
print(f'Salidas temporales: {len(salidas)}')
for s in salidas:
    print(f'  {s.tipo_salida}: {s.hora_salida} - {s.hora_regreso}, Descuenta: {s.descuenta_tiempo}')

info = calcular_horas_laboradas(session, emp.id, fecha_prueba)
print(f'Minutos laborados: {info["minutos_laborados"]}')
print(f'Minutos descanso: {info["minutos_descanso"]}')
print(f'Minutos extra: {info["minutos_extra"]}')
print(f'Horas laboradas: {info["minutos_laborados"]/60:.2f}')
print(f'Correcciones: {info.get("correcciones", [])}')
