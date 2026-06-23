from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("Agregando campo salida_anticipada a registro_asistencias...")
try:
    session.execute(text("ALTER TABLE registro_asistencias ADD COLUMN salida_anticipada BOOLEAN DEFAULT 0"))
    session.commit()
    print("Campo agregado exitosamente")
except Exception as e:
    print(f"Error: {e}")
    print("El campo probablemente ya existe")
