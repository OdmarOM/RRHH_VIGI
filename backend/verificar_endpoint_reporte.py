from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.models import RegistroAsistencia, Empleado
from app.services import calcular_horas_laboradas

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

emp = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'EMP001'))
fecha_prueba = date(2026, 6, 18)

# Simular el cálculo que hace el endpoint
horas_info = calcular_horas_laboradas(session, emp.id, fecha_prueba)
horas = horas_info.get("minutos_laborados", 0) / 60
horas_redondeadas = round(horas, 2)

print(f'Minutos laborados (calcular_horas_laboradas): {horas_info["minutos_laborados"]}')
print(f'Horas laboradas (minutos/60): {horas:.4f}')
print(f'Horas laboradas (redondeado a 2 decimales): {horas_redondeadas}')
print(f'Minutos descanso: {horas_info.get("minutos_descanso", 0)}')
print(f'Correcciones: {horas_info.get("correcciones", [])}')

# Verificar si hay algún cálculo adicional
print(f'\nVerificación manual:')
print(f'13 minutos / 60 = {13/60:.4f} horas')
print(f'13 minutos / 60 redondeado = {round(13/60, 2)} horas')
print(f'10.2 minutos / 60 = {10.2/60:.4f} horas (lo que muestra el reporte)')
