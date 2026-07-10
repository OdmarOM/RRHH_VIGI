from datetime import time
from sqlalchemy import select
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Departamento, DetallePlantillaTurno, PlantillaTurno, Rol, RolNombre, UsuarioSistema


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    for nombre in RolNombre:
        if not db.scalar(select(Rol).where(Rol.nombre == nombre)):
            db.add(Rol(nombre=nombre))
    db.flush()

    super_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.SUPERUSUARIO))
    vigilante_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.VIGILANTE))
    supervisor_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.SUPERVISOR))
    rrhh_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.RRHH))
    admin_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.ADMINISTRADOR))
    
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "super")):
        db.add(UsuarioSistema(username="super", password_hash=hash_password("super123"), rol_id=super_rol.id, activo=True))
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "vigilante")):
        db.add(UsuarioSistema(username="vigilante", password_hash=hash_password("vigilante123"), rol_id=vigilante_rol.id, activo=True))
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "supervisor")):
        db.add(UsuarioSistema(username="supervisor", password_hash=hash_password("supervisor123"), rol_id=supervisor_rol.id, activo=True))
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "rrhh")):
        db.add(UsuarioSistema(username="rrhh", password_hash=hash_password("rrhh123"), rol_id=rrhh_rol.id, activo=True))
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "admin")):
        db.add(UsuarioSistema(username="admin", password_hash=hash_password("admin123"), rol_id=admin_rol.id, activo=True))
    db.flush()

    departamentos = [
        "ALMACÉN",
        "EMBARQUES",
        "VENTAS",
        "OPERACIÓN",
        "ADMINISTRATIVA",
        "RUTAS",
        "SEGURIDAD Y VIGILANCIA",
        "SÚPER",
        "LIMPIEZA"
    ]
    
    for nombre in departamentos:
        if not db.scalar(select(Departamento).where(Departamento.nombre == nombre)):
            db.add(Departamento(nombre=nombre))
    db.flush()

    if not db.scalar(select(PlantillaTurno).where(PlantillaTurno.nombre == "Matutino")):
        plantilla_matutino = PlantillaTurno(nombre="Matutino", descripcion="Turno de 8:00 AM a 4:00 PM")
        db.add(plantilla_matutino)
        db.flush()

        for dia in range(0, 5):
            db.add(DetallePlantillaTurno(
                plantilla_id=plantilla_matutino.id,
                dia_semana=dia,
                hora_entrada_oficial=time(8, 0),
                hora_salida_oficial=time(16, 0),
                tolerancia_minutos=15
            ))

    if not db.scalar(select(PlantillaTurno).where(PlantillaTurno.nombre == "Vespertino")):
        plantilla_vespertino = PlantillaTurno(nombre="Vespertino", descripcion="Turno de 2:00 PM a 10:00 PM")
        db.add(plantilla_vespertino)
        db.flush()

        for dia in range(0, 5):
            db.add(DetallePlantillaTurno(
                plantilla_id=plantilla_vespertino.id,
                dia_semana=dia,
                hora_entrada_oficial=time(14, 0),
                hora_salida_oficial=time(22, 0),
                tolerancia_minutos=15
            ))
    
    db.commit()

print("Seed de producción completado - Base de datos limpia con usuarios base y turnos configurados")
