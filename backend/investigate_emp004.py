from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Empleado, TurnoHorario, PlantillaTurno, DetallePlantillaTurno

engine = create_engine("sqlite:///rrhh_dev.db")
with Session(engine) as session:
    # Buscar empleado EMP004
    empleado = session.scalar(select(Empleado).where(Empleado.numero_empleado == "EMP004"))
    if not empleado:
        print("Empleado EMP004 no encontrado")
    else:
        print(f"Empleado encontrado: {empleado.numero_empleado} - {empleado.nombre_completo}")
        print(f"Plantilla asignada ID: {empleado.plantilla_turno_id}")
        
        # Verificar si tiene plantilla asignada
        if empleado.plantilla_turno_id:
            plantilla = session.get(PlantillaTurno, empleado.plantilla_turno_id)
            print(f"Plantilla: {plantilla.nombre}")
            
            # Verificar detalles de la plantilla para lunes (dia_semana=0)
            detalle_plantilla = session.scalar(
                select(DetallePlantillaTurno).where(
                    DetallePlantillaTurno.plantilla_id == plantilla.id,
                    DetallePlantillaTurno.dia_semana == 0
                )
            )
            if detalle_plantilla:
                print(f"Detalle plantilla lunes - Entrada: {detalle_plantilla.hora_entrada_oficial}, Salida: {detalle_plantilla.hora_salida_oficial}")
            else:
                print("No hay detalle de plantilla para lunes")
        
        # Verificar turnos individuales para lunes (dia_semana=0)
        turno_individual = session.scalar(
            select(TurnoHorario).where(
                TurnoHorario.empleado_id == empleado.id,
                TurnoHorario.dia_semana == 0
            )
        )
        if turno_individual:
            print(f"Turno individual lunes - Entrada: {turno_individual.hora_entrada_oficial}, Salida: {turno_individual.hora_salida_oficial}")
            print(f"Tolerancia: {turno_individual.tolerancia_minutos}")
        else:
            print("No tiene turno individual para lunes")
