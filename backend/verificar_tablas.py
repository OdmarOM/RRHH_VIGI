from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///rrhh_dev.db')
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    print('Tablas en la base de datos:')
    for row in result:
        print(f'  - {row[0]}')
