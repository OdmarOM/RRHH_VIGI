from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Empleado, TurnoHorario

engine = create_engine("sqlite:///rrhh_dev.db")
with Session(engine) as session:
    # Buscar empleado EMP004
    empleado = session.scalar(select(Empleado).where(Empleado.numero_empleado == "EMP004"))
    if empleado:
        print(f"Empleado: {empleado.numero_empleado} - {empleado.nombre_completo}")
        
        # Verificar turno individual para lunes (dia_semana=0)
        turno = session.scalar(
            select(TurnoHorario).where(
                TurnoHorario.empleado_id == empleado.id,
                TurnoHorario.dia_semana == 0
            )
        )
        if turno:
            print(f"Turno lunes en DB: Entrada={turno.hora_entrada_oficial}, Salida={turno.hora_salida_oficial}")
        else:
            print("No tiene turno individual para lunes")
