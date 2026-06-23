from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///rrhh_dev.db')
conn = engine.connect()
conn.execute(text("UPDATE turnos_horarios SET hora_salida_oficial = '10:00:00' WHERE empleado_id = 1 AND dia_semana = 1"))
conn.commit()
print('Horario actualizado')
conn.close()
