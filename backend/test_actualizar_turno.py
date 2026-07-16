import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models import Empleado, TurnoHorario
from sqlalchemy import select
from datetime import time

db = SessionLocal()

empleado = db.scalar(select(Empleado).where(Empleado.numero_empleado == "emp01"))
if not empleado:
    print("No hay empleado emp01, creando turno de prueba con el primer empleado disponible")
    empleado = db.scalar(select(Empleado))

if not empleado:
    print("No hay empleados en la base de datos")
else:
    print(f"Empleado: {empleado.nombre_completo} (ID: {empleado.id}), plantilla_turno_id: {empleado.plantilla_turno_id}")
    
    turno = db.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == empleado.id, TurnoHorario.dia_semana == 0))
    if turno:
        print(f"Turno existente día 0: entrada={turno.hora_entrada_oficial}, salida={turno.hora_salida_oficial}")
    else:
        print("No hay turno individual para día 0 - se creará uno de prueba")
        turno = TurnoHorario(
            empleado_id=empleado.id,
            dia_semana=0,
            hora_entrada_oficial=time(8, 0),
            hora_salida_oficial=time(17, 0),
            tolerancia_minutos=15
        )
        db.add(turno)
        db.commit()
        db.refresh(turno)
        print(f"Turno creado con ID: {turno.id}")
    
    # Simular actualización
    turno.hora_entrada_oficial = time(9, 0)
    turno.hora_salida_oficial = time(18, 0)
    db.commit()
    db.refresh(turno)
    print(f"Turno actualizado: entrada={turno.hora_entrada_oficial}, salida={turno.hora_salida_oficial}")

db.close()
