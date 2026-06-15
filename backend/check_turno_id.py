from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import TurnoHorario, Empleado

engine = create_engine("sqlite:///rrhh_dev.db")
with Session(engine) as session:
    # Verificar turno ID 2
    turno = session.get(TurnoHorario, 2)
    if turno:
        empleado = session.get(Empleado, turno.empleado_id)
        print(f"Turno ID 2 pertenece a: {empleado.numero_empleado} - {empleado.nombre_completo}")
        print(f"Día de semana: {turno.dia_semana}")
        print(f"Hora entrada: {turno.hora_entrada_oficial}")
    
    # Verificar turno de EMP004 para lunes
    emp004 = session.scalar(select(Empleado).where(Empleado.numero_empleado == "EMP004"))
    if emp004:
        turno_emp004 = session.scalar(
            select(TurnoHorario).where(
                TurnoHorario.empleado_id == emp004.id,
                TurnoHorario.dia_semana == 0
            )
        )
        if turno_emp004:
            print(f"\nTurno de EMP004 para lunes:")
            print(f"ID: {turno_emp004.id}")
            print(f"Hora entrada: {turno_emp004.hora_entrada_oficial}")
