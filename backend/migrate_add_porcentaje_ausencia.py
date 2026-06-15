"""
Script de migración para agregar el campo porcentaje_aportacion a la tabla registro_ausencias
"""
import sqlite3

DB_PATH = "rrhh_dev.db"

def migrate():
    """Agrega la columna porcentaje_aportacion a la tabla registro_ausencias"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(registro_ausencias)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'porcentaje_aportacion' in columns:
            print("La columna porcentaje_aportacion ya existe en la tabla registro_ausencias")
            return
        
        # Agregar la columna
        cursor.execute("""
            ALTER TABLE registro_ausencias 
            ADD COLUMN porcentaje_aportacion INTEGER DEFAULT 100 NOT NULL
        """)
        
        conn.commit()
        print("[OK] Columna porcentaje_aportacion agregada exitosamente a registro_ausencias")
        
        # Actualizar registros existentes con valor por defecto
        cursor.execute("""
            UPDATE registro_ausencias 
            SET porcentaje_aportacion = 100 
            WHERE porcentaje_aportacion IS NULL OR porcentaje_aportacion = 0
        """)
        conn.commit()
        print("[OK] Registros existentes actualizados con porcentaje_aportacion = 100")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error durante la migracion: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
