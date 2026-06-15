"""
Script para depurar el turno del empleado EMP004
"""
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Empleado, TurnoHorario

TEST_DB_URL = "sqlite:///rrhh_dev.db"
test_engine = create_engine(TEST_DB_URL)

session = Session(test_engine)

empleado = session.scalar(select(Empleado).where(Empleado.numero_empleado == "EMP004"))
print(f"Empleado: {empleado.nombre_completo} (ID: {empleado.id})")

turnos = session.scalars(
    select(TurnoHorario).where(TurnoHorario.empleado_id == empleado.id)
).all()

print(f"\nTurnos del empleado:")
for turno in turnos:
    print(f"  Dia semana: {turno.dia_semana}")
    print(f"  Hora entrada: {turno.hora_entrada_oficial}")
    print(f"  Hora salida: {turno.hora_salida_oficial}")
    print(f"  Es descanso: {turno.es_descanso}")
    print(f"  ---")

session.close()
