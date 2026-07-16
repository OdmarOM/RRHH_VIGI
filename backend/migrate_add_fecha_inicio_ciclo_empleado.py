from sqlalchemy import text
from app.core.database import engine


def migrate():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE empleados ADD COLUMN fecha_inicio_ciclo DATE"))
        conn.commit()
        print("Columna fecha_inicio_ciclo agregada a empleados correctamente.")


if __name__ == "__main__":
    migrate()
