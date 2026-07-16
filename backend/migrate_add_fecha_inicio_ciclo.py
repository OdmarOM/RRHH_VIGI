from sqlalchemy import text
from app.core.database import engine
from datetime import date


def migrate():
    with engine.connect() as conn:
        # Agregar columna con un valor por defecto
        default = date.today().isoformat()
        conn.execute(text(f"ALTER TABLE plantillas_turnos ADD COLUMN fecha_inicio_ciclo DATE DEFAULT '{default}'"))
        conn.commit()
        print("Columna fecha_inicio_ciclo agregada correctamente.")


if __name__ == "__main__":
    migrate()
