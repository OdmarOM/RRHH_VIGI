from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Verificar si la tabla existe
    result = conn.execute(text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='correcciones_manuales'
    """)).fetchone()
    
    if result:
        # La tabla existe, modificar la columna minutos_agregados a REAL
        try:
            # SQLite no permite ALTER COLUMN directamente, recreamos la tabla
            conn.execute(text("""
                CREATE TABLE correcciones_manuales_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empleado_id INTEGER NOT NULL,
                    fecha DATE NOT NULL,
                    tipo_correccion VARCHAR(50) NOT NULL,
                    minutos_agregados REAL NOT NULL,
                    motivo VARCHAR(200) NOT NULL,
                    autorizado_por INTEGER NOT NULL,
                    fecha_registro DATETIME NOT NULL,
                    FOREIGN KEY (empleado_id) REFERENCES empleados(id),
                    FOREIGN KEY (autorizado_por) REFERENCES usuarios_sistema(id)
                )
            """))
            
            # Copiar datos
            conn.execute(text("""
                INSERT INTO correcciones_manuales_new 
                SELECT id, empleado_id, fecha, tipo_correccion, 
                       CAST(minutos_agregados AS REAL), motivo, autorizado_por, fecha_registro
                FROM correcciones_manuales
            """))
            
            # Eliminar tabla vieja
            conn.execute(text("DROP TABLE correcciones_manuales"))
            
            # Renombrar tabla nueva
            conn.execute(text("ALTER TABLE correcciones_manuales_new RENAME TO correcciones_manuales"))
            
            # Recrear índice
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_correcciones_empleado 
                ON correcciones_manuales(empleado_id)
            """))
            
            conn.commit()
            print("Tabla correcciones_manuales actualizada a REAL exitosamente")
        except Exception as e:
            print(f"Error actualizando tabla: {e}")
    else:
        # Crear tabla nueva con REAL
        conn.execute(text("""
            CREATE TABLE correcciones_manuales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado_id INTEGER NOT NULL,
                fecha DATE NOT NULL,
                tipo_correccion VARCHAR(50) NOT NULL,
                minutos_agregados REAL NOT NULL,
                motivo VARCHAR(200) NOT NULL,
                autorizado_por INTEGER NOT NULL,
                fecha_registro DATETIME NOT NULL,
                FOREIGN KEY (empleado_id) REFERENCES empleados(id),
                FOREIGN KEY (autorizado_por) REFERENCES usuarios_sistema(id)
            )
        """))
        
        # Crear índice en empleado_id
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_correcciones_empleado 
            ON correcciones_manuales(empleado_id)
        """))
        
        conn.commit()
        print("Tabla correcciones_manuales creada exitosamente con REAL")
