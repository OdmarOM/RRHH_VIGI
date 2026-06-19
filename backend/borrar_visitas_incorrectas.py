from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("Borrando visitas incorrectas (IDs 11-15):")
print("=" * 80)

for visita_id in [11, 12, 13, 14, 15]:
    visita = session.get(Visita, visita_id)
    if visita:
        session.delete(visita)
        print(f"Borrada visita ID {visita_id}")

session.commit()
print("Visitas borradas exitosamente")
