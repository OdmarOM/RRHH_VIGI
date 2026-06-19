from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///rrhh_dev.db')
with engine.connect() as conn:
    tablas_a_verificar = [
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
    
    print('Verificando datos eliminados:')
    for tabla in tablas_a_verificar:
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM {tabla}'))
            count = result.fetchone()[0]
            print(f'  {tabla}: {count} registros')
        except Exception as e:
            print(f'  {tabla}: Error - {e}')
    
    print('\nTablas mantenidas con datos:')
    tablas_mantenidas = ['empleados', 'turnos_horarios', 'plantillas_turnos', 'detalles_plantilla_turno', 'usuarios_sistema']
    for tabla in tablas_mantenidas:
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM {tabla}'))
            count = result.fetchone()[0]
            print(f'  {tabla}: {count} registros')
        except Exception as e:
            print(f'  {tabla}: Error - {e}')
