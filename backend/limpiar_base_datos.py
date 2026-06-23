from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

# Tablas a eliminar (manteniendo: usuarios_sistema, roles, departamentos, turnos_horarios, plantillas_turnos, detalles_plantilla_turno)
tablas_a_eliminar = [
    'solicitudes_pase_trabajo',
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
    'salidas_temporales',
    'empleados'  # Eliminar empleados para empezar desde cero
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
print('Tablas mantenidas: usuarios_sistema, roles, departamentos, turnos_horarios, plantillas_turnos, detalles_plantilla_turno')
