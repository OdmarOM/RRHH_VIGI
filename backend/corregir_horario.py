from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///rrhh_dev.db')
conn = engine.connect()

# Mapeo de nombres de días a índices weekday() de Python
# 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes, 5=Sábado, 6=Domingo
dias = {
    'LUNES': 0,
    'MARTES': 1,
    'MIERCOLES': 2,
    'JUEVES': 3,
    'VIERNES': 4,
    'SABADO': 5,
    'DOMINGO': 6
}

# Restaurar horario del lunes a 8-16
conn.execute(text("UPDATE turnos_horarios SET hora_salida_oficial = '16:00:00' WHERE empleado_id = 1 AND dia_semana = 0"))

# Restaurar horario del martes a 8-16
conn.execute(text("UPDATE turnos_horarios SET hora_salida_oficial = '16:00:00' WHERE empleado_id = 1 AND dia_semana = 1"))

conn.commit()

# Verificar resultado
result = conn.execute(text('SELECT dia_semana, hora_entrada_oficial, hora_salida_oficial FROM turnos_horarios WHERE empleado_id = 1 ORDER BY dia_semana'))
print("Horarios actualizados:")
for row in result:
    dia_nombre = [k for k, v in dias.items() if v == row[0]][0]
    print(f"  {dia_nombre} (dia_semana={row[0]}): {row[1]} - {row[2]}")

conn.close()
