from app.core.database import SessionLocal
from app.models import PlantillaTurno, Empleado
from sqlalchemy import select

db = SessionLocal()
plantillas = db.scalars(select(PlantillaTurno)).all()
for p in plantillas:
    print(p.id, p.nombre, p.es_rotativa, p.ciclo_rotacion_semanas, p.plantilla_semana_impar_id, p.plantilla_semana_par_id, p.plantilla_semana_3_id)

print('---')
emp = db.scalar(select(Empleado).where(Empleado.numero_empleado == 'EMP471'))
if emp:
    print(emp.id, emp.numero_empleado, emp.plantilla_turno_id)
else:
    print('EMP471 no encontrado')
