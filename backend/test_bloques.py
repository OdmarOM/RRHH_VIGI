from app.core.database import SessionLocal
from sqlalchemy import select
from app.models import BloqueHorasExtra, RegistroAsistencia

db = SessionLocal()
query = select(BloqueHorasExtra).join(RegistroAsistencia)
bloques = db.scalars(query).all()
print(f'Bloques encontrados: {len(bloques)}')
for b in bloques:
    print(f'  Bloque {b.id}: {b.tipo_bloque}, validacion_supervisor={b.validacion_supervisor}, validacion_rrhh={b.validacion_rrhh}')
db.close()
