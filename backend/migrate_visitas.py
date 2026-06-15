from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///rrhh_dev.db")

with engine.connect() as conn:
    # Verificar si las columnas ya existen
    result = conn.execute(text("PRAGMA table_info(visitas)"))
    columns = [row[1] for row in result.fetchall()]
    print(f"Columnas actuales en visitas: {columns}")
    
    # Agregar columnas faltantes
    if 'hora_inicio' not in columns:
        conn.execute(text("ALTER TABLE visitas ADD COLUMN hora_inicio DATETIME"))
        print("Columna hora_inicio agregada")
    
    if 'hora_fin' not in columns:
        conn.execute(text("ALTER TABLE visitas ADD COLUMN hora_fin DATETIME"))
        print("Columna hora_fin agregada")
    
    if 'minutos_duracion' not in columns:
        conn.execute(text("ALTER TABLE visitas ADD COLUMN minutos_duracion INTEGER"))
        print("Columna minutos_duracion agregada")
    
    conn.commit()
    print("Migración completada exitosamente")
