from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Empleado, TurnoHorario
from datetime import date

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

emp7 = session.scalar(select(Empleado).where(Empleado.nombre_completo == 'Empleado Prueba 7'))
print(f"Empleado: {emp7.nombre_completo} (ID: {emp7.id})")

turnos = session.scalars(
    select(TurnoHorario).where(TurnoHorario.empleado_id == emp7.id)
).all()

print(f"Turnos configurados: {len(turnos)}")
for t in turnos:
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    print(f"  Día {t.dia_semana} ({dias[t.dia_semana]}): {t.hora_entrada_oficial} - {t.hora_salida_oficial}")

print(f"\nFecha de prueba: 2026-07-01 (Martes, weekday=1)")
