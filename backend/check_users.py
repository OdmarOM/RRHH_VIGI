from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import UsuarioSistema

engine = create_engine("sqlite:///rrhh_dev.db")
with Session(engine) as session:
    users = session.scalars(select(UsuarioSistema)).all()
    print(f"Total usuarios: {len(users)}")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Activo: {user.activo}, Rol: {user.rol.nombre if user.rol else 'Sin rol'}")
