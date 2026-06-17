"""
Script para limpiar la base de datos de RRHH.
Elimina todos los registros para iniciar pruebas desde cero.
Mantiene la estructura de la base de datos y usuarios del sistema.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Ruta de la base de datos
DB_PATH = r"c:\Users\SunyLibramineto\Documents\RRHH_APP\backend\rrhh_dev.db"

# Crear engine
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
session = Session()

print("Iniciando limpieza de la base de datos...")
print(f"Base de datos: {DB_PATH}")

# Orden de eliminación respetando foreign keys
tablas_a_limpiar = [
    "correcciones_manuales",
    "bloques_horas_extra",
    "salidas_temporales",
    "visitas",
    "eventos_asistencia",
    "registro_ausencias",
    "registro_asistencias",
    "detalles_plantilla_turno",
    "plantillas_turnos",
    "turnos_horarios",
    "supervisores_departamentos",
    "empleados",
    "departamentos",
    "solicitudes_pase_trabajo",
    "evidencias_fotograficas",
    "observaciones_caseta",
    "fila_externos",
    # NOTA: No eliminamos usuarios del sistema (usuarios_sistema), roles, sqlite_sequence
]

try:
    # Desactivar foreign keys temporalmente (SQLite)
    session.execute(text("PRAGMA foreign_keys = OFF"))
    session.commit()
    
    for tabla in tablas_a_limpiar:
        try:
            # Contar registros antes de eliminar
            count = session.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar()
            if count > 0:
                print(f"  Eliminando {count} registros de {tabla}...")
                session.execute(text(f"DELETE FROM {tabla}"))
                session.commit()
                print(f"  [OK] {tabla} limpiada")
            else:
                print(f"  - {tabla} ya esta vacia")
        except Exception as e:
            print(f"  [ERROR] Error al limpiar {tabla}: {e}")
            session.rollback()
    
    # Reactivar foreign keys
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()
    
    # Verificar usuarios del sistema
    usuarios = session.execute(text("SELECT COUNT(*) FROM usuarios_sistema")).scalar()
    print(f"\nUsuarios del sistema mantenidos: {usuarios}")
    
    print("\n[OK] Limpieza completada exitosamente")
    
except Exception as e:
    print(f"\n[ERROR] Error durante la limpieza: {e}")
    session.rollback()
finally:
    session.close()
