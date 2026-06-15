from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import UsuarioSistema

engine = create_engine("sqlite:///rrhh_dev.db")
with Session(engine) as session:
    users = session.scalars(select(UsuarioSistema)).all()
    print(f"Total usuarios: {len(users)}")
    for user in users:
        hash_preview = user.password_hash[:50] if user.password_hash else "None"
        print(f"Usuario: {user.username}, Hash preview: {hash_preview}...")
