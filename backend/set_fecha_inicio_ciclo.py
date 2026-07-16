from app.core.database import SessionLocal
from app.models import PlantillaTurno
from datetime import date
from sqlalchemy import select


def update():
    db = SessionLocal()
    plantilla = db.scalar(select(PlantillaTurno).where(PlantillaTurno.nombre == 'rotativo_1'))
    if plantilla:
        plantilla.fecha_inicio_ciclo = date(2026, 7, 13)
        db.commit()
        print('fecha_inicio_ciclo actualizada a 2026-07-13 para rotativo_1')
    else:
        print('rotativo_1 no encontrado')


if __name__ == "__main__":
    update()
