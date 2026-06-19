from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

# Tablas a eliminar (manteniendo solo empleados, turnos_horarios, plantillas_turnos, detalles_plantilla_turno, usuarios_sistema)
tablas_a_eliminar = [
    'solicitudes_pase_trabajo',
    'departamentos',
    'roles',
    'evidencias_fotograficas',
    'registro_ausencias',
    'supervisores_departamentos',
    'registro_asistencias',
    'fila_externos',
    'correcciones_manuales',
    'bloques_horas_extra',
    'observaciones_caseta',
    'eventos_asistencia',
    'visitas',
    'salidas_temporales'
]

print('Limpiando base de datos...')
for tabla in tablas_a_eliminar:
    try:
        session.execute(text(f'DELETE FROM {tabla}'))
        print(f'  [OK] {tabla} eliminada')
    except Exception as e:
        print(f'  [ERROR] Error al eliminar {tabla}: {e}')

session.commit()
print('\nBase de datos limpiada exitosamente.')
print('Tablas mantenidas: empleados, turnos_horarios, plantillas_turnos, detalles_plantilla_turno, usuarios_sistema')
