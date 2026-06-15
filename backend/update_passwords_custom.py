from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models import UsuarioSistema

engine = create_engine("sqlite:///rrhh_dev.db")

with Session(engine) as session:
    users = session.scalars(select(UsuarioSistema)).all()
    print(f"Actualizando {len(users)} usuarios con formato personalizado...")
    
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
            user.password_hash = hash_password(default_passwords[user.username])
            print(f"Usuario {user.username} actualizado con formato personalizado")
    
    session.commit()
    print("Contraseñas actualizadas exitosamente")
