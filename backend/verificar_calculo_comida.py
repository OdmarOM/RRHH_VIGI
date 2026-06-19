from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import SalidaTemporal, RegistroAsistencia, Empleado
from app.services import calcular_horas_laboradas

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

salida = session.get(SalidaTemporal, 1)
asistencia = session.get(RegistroAsistencia, salida.asistencia_id)
empleado = session.get(Empleado, asistencia.empleado_id) if asistencia else None

print(f'Empleado: {empleado.nombre_completo if empleado else "N/A"}')
print(f'Fecha turno: {asistencia.fecha_turno if asistencia else "N/A"}')
print(f'Entrada real: {asistencia.hora_entrada_real if asistencia else "N/A"}')
print(f'Salida real: {asistencia.hora_salida_real if asistencia else "N/A"}')
print(f'Estado registro: {asistencia.estado_registro if asistencia else "N/A"}')

# Calcular horas laboradas
resultado = calcular_horas_laboradas(session, empleado.id, asistencia.fecha_turno)

print(f'\nResultado de calcular_horas_laboradas:')
print(f'  Minutos laborados: {resultado["minutos_laborados"]}')
print(f'  Minutos extra: {resultado["minutos_extra"]}')
print(f'  Minutos descanso: {resultado["minutos_descanso"]}')
print(f'  Total eventos: {resultado["total_eventos"]}')
print(f'  Bloques extra: {len(resultado["bloques_extra"])}')

# Verificar si la salida de comida está en los eventos
print(f'\nEventos detalle:')
for ev in resultado["eventos"]:
    print(f'  {ev}')

# Calcular manualmente lo que debería ser
print(f'\nCalculo manual esperado:')
print(f'  11:20:58 a 11:22:41: ~2 minutos laborados')
print(f'  11:22:41 a 11:29:27: ~7 minutos de comida (deberian sumarse a laborados)')
print(f'  11:29:27 a 11:31:06: ~2 minutos laborados')
print(f'  11:31:06 a 11:34:03: ~3 minutos de permiso (descanso)')
print(f'  11:34:03 a 11:36:15: ~2 minutos laborados')
print(f'  Total esperado: 13 minutos laborados, 3 minutos descanso')
