from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date
from app.models import Empleado, TurnoHorario
from app.services import get_empleado_turno

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

# Crear una nueva sesión para verificar
session2 = Session(engine)

emp5 = session2.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST005'))
fecha_test5 = date(2026, 6, 27)  # Viernes

print(f'Test para TEST005 (ID: {emp5.id}) el {fecha_test5} (día {fecha_test5.weekday()}):')

# Verificar si el turno horario existe
turno_directo = session2.scalar(
    select(TurnoHorario).where(
        TurnoHorario.empleado_id == emp5.id,
        TurnoHorario.dia_semana == fecha_test5.weekday()
    )
)
print(f'Turno directo: {turno_directo}')

if turno_directo:
    print(f'  Hora entrada: {turno_directo.hora_entrada_oficial}')
    print(f'  Hora salida: {turno_directo.hora_salida_oficial}')

# Verificar con get_empleado_turno
turno_funcion = get_empleado_turno(session2, emp5, fecha_test5.weekday())
print(f'Turno funcion: {turno_funcion}')

session2.close()
