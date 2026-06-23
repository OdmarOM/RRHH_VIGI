from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import BloqueHorasExtra

engine = create_engine("sqlite:///rrhh_dev.db")
with Session(engine) as session:
    # Buscar el bloque de horas extra del EMP001
    bloques = session.scalars(select(BloqueHorasExtra)).all()
    print(f"Total bloques: {len(bloques)}")
    for bloque in bloques:
        print(f"ID: {bloque.id}, validado_supervisor: {bloque.validacion_supervisor}, validado_rrhh: {bloque.validacion_rrhh}")
    
    # Revocar autorización RRHH del último bloque
    if bloques:
        ultimo_bloque = bloques[-1]
        print(f"\nRevocando autorización RRHH del bloque ID: {ultimo_bloque.id}")
        ultimo_bloque.validacion_rrhh = False
        session.commit()
        print("Autorización RRHH revocada correctamente")
