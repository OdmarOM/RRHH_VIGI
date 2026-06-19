from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, Empleado
from datetime import datetime, date

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("=" * 80)
print("SIMULANDO LLAMADA AL ENDPOINT /caseta/visitas")
print("=" * 80)

# Simular la query del endpoint
query = select(Visita)
query = query.where(Visita.hora_fin.is_not(None))
visitas = session.scalars(query.order_by(Visita.fecha_visita.desc())).all()

print(f"Total visitas devueltas por endpoint: {len(visitas)}")
for v in visitas:
    emp = session.get(Empleado, v.empleado_id)
    print(f"ID: {v.id}, Empleado: {emp.nombre_completo if emp else 'N/A'}, Fecha: {v.fecha_visita}, Hora fin: {v.hora_fin}, Minutos: {v.minutos_duracion}, Estado: {v.estado.value}")

print("\n" + "=" * 80)
print("FILTRANDO POR FECHA DE HOY")
print("=" * 80)
hoy = date.today()
query_hoy = select(Visita)
query_hoy = query_hoy.where(Visita.fecha_visita >= datetime.combine(hoy, datetime.min.time()))
query_hoy = query_hoy.where(Visita.fecha_visita <= datetime.combine(hoy, datetime.max.time()))
query_hoy = query_hoy.where(Visita.hora_fin.is_not(None))
visitas_hoy = session.scalars(query_hoy.order_by(Visita.fecha_visita.desc())).all()

print(f"Total visitas de hoy: {len(visitas_hoy)}")
for v in visitas_hoy:
    emp = session.get(Empleado, v.empleado_id)
    print(f"ID: {v.id}, Empleado: {emp.nombre_completo if emp else 'N/A'}, Fecha: {v.fecha_visita}, Hora fin: {v.hora_fin}, Minutos: {v.minutos_duracion}, Estado: {v.estado.value}")
