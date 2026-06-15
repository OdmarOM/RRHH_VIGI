from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import TurnoHorario, Empleado
from datetime import time

engine = create_engine("sqlite:///rrhh_dev.db")
with Session(engine) as session:
    # Buscar empleado EMP004
    emp004 = session.scalar(select(Empleado).where(Empleado.numero_empleado == "EMP004"))
    if emp004:
        # Buscar turno de lunes (dia_semana=0)
        turno_lunes = session.scalar(
            select(TurnoHorario).where(
                TurnoHorario.empleado_id == emp004.id,
                TurnoHorario.dia_semana == 0
            )
        )
        if turno_lunes:
            print(f"Turno lunes actual: {turno_lunes.hora_entrada_oficial}")
            # Actualizar a 10:00:00 (la hora que querías)
            turno_lunes.hora_entrada_oficial = time(10, 0, 0)
            session.commit()
            print(f"Turno lunes actualizado: {turno_lunes.hora_entrada_oficial}")
        else:
            print("No tiene turno para lunes")
