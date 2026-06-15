from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models import UsuarioSistema

engine = create_engine("sqlite:///rrhh_dev.db")
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

with Session(engine) as session:
    users = session.scalars(select(UsuarioSistema)).all()
    print(f"Actualizando {len(users)} usuarios con sha256_crypt...")
    
    # Contraseñas por defecto para cada usuario
    default_passwords = {
        "super": "super",
        "admin": "admin", 
        "rrhh": "rrhh",
        "supervisor": "supervisor",
        "vigilante": "vigilante"
    }
    
    for user in users:
        if user.username in default_passwords:
            user.password_hash = pwd_context.hash(default_passwords[user.username])
            print(f"Usuario {user.username} actualizado con sha256_crypt")
    
    session.commit()
    print("Contraseñas actualizadas exitosamente")
