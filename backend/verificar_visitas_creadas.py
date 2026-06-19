from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, Empleado

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("Últimas visitas creadas:")
print("=" * 80)
visitas = session.scalars(
    select(Visita).order_by(Visita.id.desc()).limit(10)
).all()

for v in visitas:
    emp = session.get(Empleado, v.empleado_id)
    print(f"ID: {v.id}")
    print(f"  Empleado: {emp.nombre_completo if emp else 'N/A'}")
    print(f"  Fecha visita: {v.fecha_visita}")
    print(f"  Hora inicio: {v.hora_inicio}")
    print(f"  Hora fin: {v.hora_fin}")
    print(f"  Minutos duración: {v.minutos_duracion}")
    print(f"  Estado: {v.estado.value}")
    print(f"  Motivo: {v.motivo}")
    print("-" * 80)
