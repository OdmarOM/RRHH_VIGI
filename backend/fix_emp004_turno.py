from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Empleado, TurnoHorario
from datetime import time

engine = create_engine("sqlite:///rrhh_dev.db")
with Session(engine) as session:
    # Buscar empleado EMP004
    empleado = session.scalar(select(Empleado).where(Empleado.numero_empleado == "EMP004"))
    if not empleado:
        print("Empleado EMP004 no encontrado")
    else:
        print(f"Empleado encontrado: {empleado.numero_empleado} - {empleado.nombre_completo}")
        
        # Buscar turno individual para lunes (dia_semana=0)
        turno = session.scalar(
            select(TurnoHorario).where(
                TurnoHorario.empleado_id == empleado.id,
                TurnoHorario.dia_semana == 0
            )
        )
        if turno:
            print(f"Turno actual - Entrada: {turno.hora_entrada_oficial}, Salida: {turno.hora_salida_oficial}")
            # Actualizar a 09:20:00
            turno.hora_entrada_oficial = time(9, 20, 0)
            session.commit()
            print(f"Turno actualizado - Nueva entrada: {turno.hora_entrada_oficial}")
        else:
            print("No tiene turno individual para lunes, creando uno...")
            nuevo_turno = TurnoHorario(
                empleado_id=empleado.id,
                dia_semana=0,
                hora_entrada_oficial=time(9, 20, 0),
                hora_salida_oficial=time(17, 0, 0),
                tolerancia_minutos=15,
                es_descanso=False,
                es_por_asistencia=False
            )
            session.add(nuevo_turno)
            session.commit()
            print("Turno creado exitosamente")
