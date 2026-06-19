from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import UsuarioSistema, Empleado

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print('Usuarios del sistema:')
usuarios = session.scalars(select(UsuarioSistema)).all()
for u in usuarios:
    print(f'  - {u.username} (activo: {u.activo})')

print('\nEmpleados:')
empleados = session.scalars(select(Empleado)).all()
if empleados:
    for e in empleados:
        print(f'  - {e.nombre_completo} ({e.numero_empleado})')
else:
    print('  No hay empleados')
