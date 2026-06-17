from sqlalchemy import select, func
from app.core.database import SessionLocal, engine
from app.models import RegistroAsistencia, Visita, EstadoRegistro
from app.services import crear_visita

with SessionLocal() as db:
    # Buscar registros con estado VISITA_DESCANSO que no tienen visita
    visitas_descanso = db.scalars(
        select(RegistroAsistencia).where(RegistroAsistencia.estado_registro == EstadoRegistro.VISITA_DESCANSO)
    ).all()
    
    print(f"Registros con estado VISITA_DESCANSO: {len(visitas_descanso)}")
    
    for reg in visitas_descanso:
        visita = db.scalar(select(Visita).where(Visita.asistencia_id == reg.id))
        if not visita:
            print(f"  - Registro ID {reg.id} (empleado_id={reg.empleado_id}) NO tiene visita creada - CREANDO...")
            crear_visita(db, reg.empleado_id, reg.id)
        else:
            print(f"  - Registro ID {reg.id} (empleado_id={reg.empleado_id}) tiene visita ID {visita.id}")
    
    # Total visitas en tabla visitas
    total_visitas = db.scalar(func.count(Visita.id))
    print(f"\nTotal visitas en tabla visitas: {total_visitas}")
