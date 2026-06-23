import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.database import Base, get_db
from app.models import Empleado, TurnoHorario, UsuarioSistema, Rol
from datetime import date, time, datetime
from passlib.context import CryptContext

# Motor de prueba en memoria
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture(scope="function")
def db_session():
    """Crea una sesión de base de datos en memoria para cada prueba"""
    Base.metadata.create_all(bind=engine)
    session = Session(engine)
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_data(db_session):
    """Crea datos de prueba básicos"""
    # Crear roles
    rol_admin = Rol(nombre="Administrador")
    rol_rrhh = Rol(nombre="RRHH")
    rol_supervisor = Rol(nombre="Supervisor")
    rol_vigilante = Rol(nombre="Vigilante")
    db_session.add_all([rol_admin, rol_rrhh, rol_supervisor, rol_vigilante])
    db_session.commit()
    
    # Crear usuario de prueba
    usuario = UsuarioSistema(
        username="test_user",
        password_hash=pwd_context.hash("test123"),
        rol_id=rol_admin.id,
        activo=True
    )
    db_session.add(usuario)
    db_session.commit()
    
    # Crear empleado de prueba
    empleado = Empleado(
        numero_empleado="TEST001",
        nombre_completo="Empleado Test",
        puesto="Vigilante",
        departamento_id=1,
        activo=True
    )
    db_session.add(empleado)
    db_session.commit()
    
    # Crear turno de prueba (Lunes 08:00-17:00)
    turno = TurnoHorario(
        empleado_id=empleado.id,
        dia_semana=0,  # Lunes
        hora_entrada_oficial=time(8, 0),
        hora_salida_oficial=time(17, 0),
        tolerancia_entrada_previa_minutos=15,
        tolerancia_minutos=15,
        tolerancia_salida_previa_minutos=5,
        tolerancia_salida_posterior_minutos=15
    )
    db_session.add(turno)
    db_session.commit()
    
    return {
        "empleado": empleado,
        "usuario": usuario,
        "turno": turno,
        "rol_admin": rol_admin,
        "rol_rrhh": rol_rrhh,
        "rol_supervisor": rol_supervisor
    }
