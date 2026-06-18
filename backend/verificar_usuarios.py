from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import UsuarioSistema

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

usuarios = session.scalars(select(UsuarioSistema)).all()
print("Usuarios en la base de datos:")
for u in usuarios:
    print(f"Username: {u.username}, Rol: {u.rol.nombre if u.rol else 'N/A'}, Activo: {u.activo}")
    print(f"  Hash de contraseña: {u.password_hash[:20]}..." if u.password_hash else "  Sin contraseña")
