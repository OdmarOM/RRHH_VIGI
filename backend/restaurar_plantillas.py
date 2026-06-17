"""
Script para restaurar las plantillas base de turnos.
Matutino: 8:00 AM a 4:00 PM
Vespertino: 2:00 PM a 10:00 PM
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_PATH = r"c:\Users\SunyLibramineto\Documents\RRHH_APP\backend\rrhh_dev.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
session = Session()

print("Restaurando plantillas base de turnos...")

try:
    # Desactivar foreign keys temporalmente
    session.execute(text("PRAGMA foreign_keys = OFF"))
    session.commit()
    
    # Insertar plantilla Matutino
    print("  Creando plantilla Matutino (8:00 AM - 4:00 PM)...")
    session.execute(text("""
        INSERT INTO plantillas_turnos (nombre, descripcion)
        VALUES ('Matutino', 'Turno matutino de 8:00 AM a 4:00 PM')
    """))
    session.commit()
    
    # Obtener ID de la plantilla Matutino
    matutino_id = session.execute(text("SELECT last_insert_rowid()")).scalar()
    print(f"  ID plantilla Matutino: {matutino_id}")
    
    # Insertar detalles para cada dia de la semana (0=Lunes, 6=Domingo)
    for dia in range(7):
        session.execute(text("""
            INSERT INTO detalles_plantilla_turno 
            (plantilla_id, dia_semana, hora_entrada_oficial, hora_salida_oficial, 
             tolerancia_minutos, tolerancia_entrada_previa_minutos, 
             tolerancia_salida_posterior_minutos, tolerancia_salida_previa_minutos, 
             es_descanso, es_por_asistencia)
            VALUES (:plantilla_id, :dia, '08:00:00', '16:00:00', 
                    15, 30, 30, 15, 0, 0)
        """), {"plantilla_id": matutino_id, "dia": dia})
    session.commit()
    print(f"  [OK] Plantilla Matutino creada con detalles para 7 dias")
    
    # Insertar plantilla Vespertino
    print("  Creando plantilla Vespertino (2:00 PM - 10:00 PM)...")
    session.execute(text("""
        INSERT INTO plantillas_turnos (nombre, descripcion)
        VALUES ('Vespertino', 'Turno vespertino de 2:00 PM a 10:00 PM')
    """))
    session.commit()
    
    # Obtener ID de la plantilla Vespertino
    vespertino_id = session.execute(text("SELECT last_insert_rowid()")).scalar()
    print(f"  ID plantilla Vespertino: {vespertino_id}")
    
    # Insertar detalles para cada dia de la semana
    for dia in range(7):
        session.execute(text("""
            INSERT INTO detalles_plantilla_turno 
            (plantilla_id, dia_semana, hora_entrada_oficial, hora_salida_oficial, 
             tolerancia_minutos, tolerancia_entrada_previa_minutos, 
             tolerancia_salida_posterior_minutos, tolerancia_salida_previa_minutos, 
             es_descanso, es_por_asistencia)
            VALUES (:plantilla_id, :dia, '14:00:00', '22:00:00', 
                    15, 30, 30, 15, 0, 0)
        """), {"plantilla_id": vespertino_id, "dia": dia})
    session.commit()
    print(f"  [OK] Plantilla Vespertino creada con detalles para 7 dias")
    
    # Reactivar foreign keys
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()
    
    # Verificar plantillas creadas
    plantillas = session.execute(text("SELECT id, nombre FROM plantillas_turnos")).fetchall()
    print(f"\nPlantillas en la base de datos:")
    for p in plantillas:
        print(f"  - ID {p[0]}: {p[1]}")
    
    print("\n[OK] Plantillas base restauradas exitosamente")
    
except Exception as e:
    print(f"\n[ERROR] Error durante la restauracion: {e}")
    session.rollback()
finally:
    session.close()
