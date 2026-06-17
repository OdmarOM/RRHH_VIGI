from sqlalchemy import text
from app.core.database import engine

def migrate():
    """Agrega el campo hora_entrada_almacen a la tabla fila_externos"""
    with engine.connect() as conn:
        # Verificar si la columna ya existe
        result = conn.execute(text("PRAGMA table_info(fila_externos)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'hora_entrada_almacen' not in columns:
            conn.execute(text("""
                ALTER TABLE fila_externos 
                ADD COLUMN hora_entrada_almacen TIMESTAMP WITH TIME ZONE
            """))
            conn.commit()
            print("Migracion completada: columna hora_entrada_almacen agregada")
        else:
            print("La columna hora_entrada_almacen ya existe")

if __name__ == "__main__":
    migrate()
