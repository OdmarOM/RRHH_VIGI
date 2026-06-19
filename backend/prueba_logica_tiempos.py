from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta
from app.models import (
    Empleado, TurnoHorario, PlantillaTurno, DetallePlantillaTurno,
    RegistroAsistencia, EventoAsistencia, TipoEvento, TipoSalida,
    BloqueHorasExtra, Visita, EstadoVisita
)
from app.services import calcular_horas_laboradas

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("=" * 80)
print("PRUEBA INTEGRAL DE LÓGICA DE TIEMPOS")
print("=" * 80)

# Caso 1: Empleado con turno normal, sin salidas temporales
print("\n[ CASO 1 ] Empleado con turno normal, sin salidas temporales")
print("-" * 80)
# Crear departamento de prueba
from app.models import Departamento
if not session.scalar(select(Departamento).where(Departamento.nombre == 'Pruebas')):
    dept_pruebas = Departamento(nombre='Pruebas')
    session.add(dept_pruebas)
    session.flush()
else:
    dept_pruebas = session.scalar(select(Departamento).where(Departamento.nombre == 'Pruebas'))

# Crear empleado de prueba
if not session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST001')):
    emp1 = Empleado(
        numero_empleado='TEST001',
        nombre_completo='Empleado Prueba 1',
        departamento_id=dept_pruebas.id,
        puesto='Prueba',
        estado_actual='Fuera'
    )
    session.add(emp1)
    session.flush()
else:
    emp1 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST001'))

# Crear turno de prueba (8:00 AM - 4:00 PM)
if not session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp1.id)):
    turno1 = TurnoHorario(
        empleado_id=emp1.id,
        dia_semana=0,  # Lunes
        hora_entrada_oficial=time(8, 0),
        hora_salida_oficial=time(16, 0),
        tolerancia_minutos=15
    )
    session.add(turno1)
    session.flush()

# Crear registro de asistencia normal
fecha_test = date(2026, 6, 23)
reg1 = RegistroAsistencia(
    empleado_id=emp1.id,
    fecha_turno=fecha_test,
    hora_entrada_real=datetime.combine(fecha_test, time(8, 0)),
    hora_salida_real=datetime.combine(fecha_test, time(16, 0)),
    estado_registro='Normal'
)
session.add(reg1)
session.flush()

# Crear eventos
eventos_caso1 = [
    EventoAsistencia(
        empleado_id=emp1.id,
        asistencia_id=reg1.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=datetime.combine(fecha_test, time(8, 0)),
        observaciones='Entrada normal'
    ),
    EventoAsistencia(
        empleado_id=emp1.id,
        asistencia_id=reg1.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=datetime.combine(fecha_test, time(16, 0)),
        observaciones='Salida normal'
    )
]
for e in eventos_caso1:
    session.add(e)
session.flush()

resultado1 = calcular_horas_laboradas(session, emp1.id, fecha_test)
print(f"Entrada: 08:00, Salida: 16:00")
print(f"Minutos laborados: {resultado1['minutos_laborados']}")
print(f"Minutos extra: {resultado1['minutos_extra']}")
print(f"Minutos descanso: {resultado1['minutos_descanso']}")
print(f"Horas laboradas: {resultado1['minutos_laborados'] / 60:.2f}")
print(f"Expected: 480 minutos (8 horas)")
print(f"Status: {'[PASS]' if resultado1['minutos_laborados'] == 480 else '[FAIL]'}")

# Caso 2: Empleado con retardo aprobado
print("\n[ CASO 2 ] Empleado con retardo aprobado")
print("-" * 80)
if not session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST002')):
    emp2 = Empleado(
        numero_empleado='TEST002',
        nombre_completo='Empleado Prueba 2',
        departamento_id=dept_pruebas.id,
        puesto='Prueba',
        estado_actual='Fuera'
    )
    session.add(emp2)
    session.flush()
else:
    emp2 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST002'))

if not session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp2.id)):
    turno2 = TurnoHorario(
        empleado_id=emp2.id,
        dia_semana=1,  # Martes
        hora_entrada_oficial=time(8, 0),
        hora_salida_oficial=time(16, 0),
        tolerancia_minutos=15
    )
    session.add(turno2)
    session.flush()

fecha_test2 = date(2026, 6, 24)
reg2 = RegistroAsistencia(
    empleado_id=emp2.id,
    fecha_turno=fecha_test2,
    hora_entrada_real=datetime.combine(fecha_test2, time(8, 30)),
    hora_salida_real=datetime.combine(fecha_test2, time(16, 0)),
    estado_registro='Retardo_Aprobado'
)
session.add(reg2)
session.flush()

eventos_caso2 = [
    EventoAsistencia(
        empleado_id=emp2.id,
        asistencia_id=reg2.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=datetime.combine(fecha_test2, time(8, 30)),
        observaciones='Entrada con retardo'
    ),
    EventoAsistencia(
        empleado_id=emp2.id,
        asistencia_id=reg2.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=datetime.combine(fecha_test2, time(16, 0)),
        observaciones='Salida normal'
    )
]
for e in eventos_caso2:
    session.add(e)
session.flush()

resultado2 = calcular_horas_laboradas(session, emp2.id, fecha_test2)
print(f"Entrada: 08:30, Salida: 16:00 (Retardo de 30 min)")
print(f"Minutos laborados: {resultado2['minutos_laborados']}")
print(f"Minutos extra: {resultado2['minutos_extra']}")
print(f"Minutos descanso: {resultado2['minutos_descanso']}")
print(f"Horas laboradas: {resultado2['minutos_laborados'] / 60:.2f}")
print(f"Expected: 450 minutos (7.5 horas)")
print(f"Status: {'[PASS]' if resultado2['minutos_laborados'] == 450 else '[FAIL]'}")

# Caso 3: Empleado con salida temporal de comida
print("\n[ CASO 3 ] Empleado con salida temporal de comida")
print("-" * 80)
if not session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST003')):
    emp3 = Empleado(
        numero_empleado='TEST003',
        nombre_completo='Empleado Prueba 3',
        departamento_id=dept_pruebas.id,
        puesto='Prueba',
        estado_actual='Fuera'
    )
    session.add(emp3)
    session.flush()
else:
    emp3 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST003'))

if not session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp3.id)):
    turno3 = TurnoHorario(
        empleado_id=emp3.id,
        dia_semana=2,  # Miércoles
        hora_entrada_oficial=time(8, 0),
        hora_salida_oficial=time(16, 0),
        tolerancia_minutos=15
    )
    session.add(turno3)
    session.flush()

fecha_test3 = date(2026, 6, 25)
reg3 = RegistroAsistencia(
    empleado_id=emp3.id,
    fecha_turno=fecha_test3,
    hora_entrada_real=datetime.combine(fecha_test3, time(8, 0)),
    hora_salida_real=datetime.combine(fecha_test3, time(16, 0)),
    estado_registro='Normal'
)
session.add(reg3)
session.flush()

eventos_caso3 = [
    EventoAsistencia(
        empleado_id=emp3.id,
        asistencia_id=reg3.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=datetime.combine(fecha_test3, time(8, 0)),
        observaciones='Entrada normal'
    ),
    EventoAsistencia(
        empleado_id=emp3.id,
        asistencia_id=reg3.id,
        tipo_evento=TipoEvento.SALIDA_TEMPORAL,
        fecha_evento=datetime.combine(fecha_test3, time(12, 0)),
        tipo_salida=TipoSalida.COMER,
        observaciones='Salida temporal: Comer'
    ),
    EventoAsistencia(
        empleado_id=emp3.id,
        asistencia_id=reg3.id,
        tipo_evento=TipoEvento.REGRESO_SALIDA_TEMPORAL,
        fecha_evento=datetime.combine(fecha_test3, time(13, 0)),
        observaciones='Regreso de salida temporal'
    ),
    EventoAsistencia(
        empleado_id=emp3.id,
        asistencia_id=reg3.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=datetime.combine(fecha_test3, time(16, 0)),
        observaciones='Salida normal'
    )
]
for e in eventos_caso3:
    session.add(e)
session.flush()

resultado3 = calcular_horas_laboradas(session, emp3.id, fecha_test3)
print(f"Entrada: 08:00, Salida comida: 12:00, Regreso: 13:00, Salida: 16:00")
print(f"Minutos laborados: {resultado3['minutos_laborados']}")
print(f"Minutos extra: {resultado3['minutos_extra']}")
print(f"Minutos descanso: {resultado3['minutos_descanso']}")
print(f"Horas laboradas: {resultado3['minutos_laborados'] / 60:.2f}")
print(f"Expected: 480 minutos (8 horas) - Comida se cuenta como trabajo")
print(f"Status: {'[PASS]' if resultado3['minutos_laborados'] == 480 else '[FAIL]'}")

# Caso 4: Empleado con salida temporal de permiso personal
print("\n[ CASO 4 ] Empleado con salida temporal de permiso personal")
print("-" * 80)
if not session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST004')):
    emp4 = Empleado(
        numero_empleado='TEST004',
        nombre_completo='Empleado Prueba 4',
        departamento_id=dept_pruebas.id,
        puesto='Prueba',
        estado_actual='Fuera'
    )
    session.add(emp4)
    session.flush()
else:
    emp4 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST004'))

if not session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp4.id)):
    turno4 = TurnoHorario(
        empleado_id=emp4.id,
        dia_semana=3,  # Jueves
        hora_entrada_oficial=time(8, 0),
        hora_salida_oficial=time(16, 0),
        tolerancia_minutos=15
    )
    session.add(turno4)
    session.flush()

fecha_test4 = date(2026, 6, 26)
reg4 = RegistroAsistencia(
    empleado_id=emp4.id,
    fecha_turno=fecha_test4,
    hora_entrada_real=datetime.combine(fecha_test4, time(8, 0)),
    hora_salida_real=datetime.combine(fecha_test4, time(16, 0)),
    estado_registro='Normal'
)
session.add(reg4)
session.flush()

eventos_caso4 = [
    EventoAsistencia(
        empleado_id=emp4.id,
        asistencia_id=reg4.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=datetime.combine(fecha_test4, time(8, 0)),
        observaciones='Entrada normal'
    ),
    EventoAsistencia(
        empleado_id=emp4.id,
        asistencia_id=reg4.id,
        tipo_evento=TipoEvento.SALIDA_TEMPORAL,
        fecha_evento=datetime.combine(fecha_test4, time(10, 0)),
        tipo_salida=TipoSalida.PERMISO_PERSONAL,
        observaciones='Salida temporal: Permiso_Personal'
    ),
    EventoAsistencia(
        empleado_id=emp4.id,
        asistencia_id=reg4.id,
        tipo_evento=TipoEvento.REGRESO_SALIDA_TEMPORAL,
        fecha_evento=datetime.combine(fecha_test4, time(11, 0)),
        observaciones='Regreso de salida temporal'
    ),
    EventoAsistencia(
        empleado_id=emp4.id,
        asistencia_id=reg4.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=datetime.combine(fecha_test4, time(16, 0)),
        observaciones='Salida normal'
    )
]
for e in eventos_caso4:
    session.add(e)
session.flush()

resultado4 = calcular_horas_laboradas(session, emp4.id, fecha_test4)
print(f"Entrada: 08:00, Salida permiso: 10:00, Regreso: 11:00, Salida: 16:00")
print(f"Minutos laborados: {resultado4['minutos_laborados']}")
print(f"Minutos extra: {resultado4['minutos_extra']}")
print(f"Minutos descanso: {resultado4['minutos_descanso']}")
print(f"Horas laboradas: {resultado4['minutos_laborados'] / 60:.2f}")
print(f"Expected: 420 minutos laborados (7 horas) - 60 minutos permiso NO descuentan")
print(f"Status: {'[PASS]' if resultado4['minutos_laborados'] == 420 and resultado4['minutos_descanso'] == 60 else '[FAIL]'}")

# Caso 5: Empleado con horas extra previas
print("\n[ CASO 5 ] Empleado con horas extra previas")
print("-" * 80)
if not session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST005')):
    emp5 = Empleado(
        numero_empleado='TEST005',
        nombre_completo='Empleado Prueba 5',
        departamento_id=dept_pruebas.id,
        puesto='Prueba',
        estado_actual='Fuera'
    )
    session.add(emp5)
    session.flush()
else:
    emp5 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST005'))

if not session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp5.id)):
    turno5 = TurnoHorario(
        empleado_id=emp5.id,
        dia_semana=4,  # Viernes
        hora_entrada_oficial=time(8, 0),
        hora_salida_oficial=time(16, 0),
        tolerancia_minutos=15
    )
    session.add(turno5)
    session.commit()
    session.flush()

fecha_test5 = date(2026, 6, 26)  # Viernes (día 4)
reg5 = RegistroAsistencia(
    empleado_id=emp5.id,
    fecha_turno=fecha_test5,
    hora_entrada_real=datetime.combine(fecha_test5, time(7, 0)),
    hora_salida_real=datetime.combine(fecha_test5, time(16, 0)),
    estado_registro='Normal'
)
session.add(reg5)
session.flush()

eventos_caso5 = [
    EventoAsistencia(
        empleado_id=emp5.id,
        asistencia_id=reg5.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=datetime.combine(fecha_test5, time(7, 0)),
        observaciones='Entrada temprano'
    ),
    EventoAsistencia(
        empleado_id=emp5.id,
        asistencia_id=reg5.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=datetime.combine(fecha_test5, time(16, 0)),
        observaciones='Salida normal'
    )
]
for e in eventos_caso5:
    session.add(e)
session.flush()

resultado5 = calcular_horas_laboradas(session, emp5.id, fecha_test5)
print(f"Entrada: 07:00, Salida: 16:00 (Extra previa de 1 hora)")
print(f"Minutos laborados: {resultado5['minutos_laborados']}")
print(f"Minutos extra: {resultado5['minutos_extra']}")
print(f"Minutos descanso: {resultado5['minutos_descanso']}")
print(f"Bloques extra: {len(resultado5['bloques_extra'])}")
print(f"Horas laboradas: {resultado5['minutos_laborados'] / 60:.2f}")
print(f"Expected: 480 minutos laborados, 0 minutos extra (requiere validacion RRHH)")
print(f"Status: {'[PASS]' if resultado5['minutos_laborados'] == 480 and resultado5['minutos_extra'] == 0 and len(resultado5['bloques_extra']) == 1 else '[FAIL]'}")

# Caso 6: Empleado con horas extra posteriores
print("\n[ CASO 6 ] Empleado con horas extra posteriores")
print("-" * 80)
if not session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST006')):
    emp6 = Empleado(
        numero_empleado='TEST006',
        nombre_completo='Empleado Prueba 6',
        departamento_id=dept_pruebas.id,
        puesto='Prueba',
        estado_actual='Fuera'
    )
    session.add(emp6)
    session.flush()
else:
    emp6 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST006'))

if not session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp6.id)):
    turno6 = TurnoHorario(
        empleado_id=emp6.id,
        dia_semana=0,  # Lunes
        hora_entrada_oficial=time(8, 0),
        hora_salida_oficial=time(16, 0),
        tolerancia_minutos=15
    )
    session.add(turno6)
    session.commit()
    session.flush()

fecha_test6 = date(2026, 6, 29)  # Lunes (día 0)
reg6 = RegistroAsistencia(
    empleado_id=emp6.id,
    fecha_turno=fecha_test6,
    hora_entrada_real=datetime.combine(fecha_test6, time(8, 0)),
    hora_salida_real=datetime.combine(fecha_test6, time(17, 0)),
    estado_registro='Normal'
)
session.add(reg6)
session.flush()

eventos_caso6 = [
    EventoAsistencia(
        empleado_id=emp6.id,
        asistencia_id=reg6.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=datetime.combine(fecha_test6, time(8, 0)),
        observaciones='Entrada normal'
    ),
    EventoAsistencia(
        empleado_id=emp6.id,
        asistencia_id=reg6.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=datetime.combine(fecha_test6, time(17, 0)),
        observaciones='Salida tardía'
    )
]
for e in eventos_caso6:
    session.add(e)
session.flush()

resultado6 = calcular_horas_laboradas(session, emp6.id, fecha_test6)
print(f"Entrada: 08:00, Salida: 17:00 (Extra posterior de 1 hora)")
print(f"Minutos laborados: {resultado6['minutos_laborados']}")
print(f"Minutos extra: {resultado6['minutos_extra']}")
print(f"Minutos descanso: {resultado6['minutos_descanso']}")
print(f"Bloques extra: {len(resultado6['bloques_extra'])}")
print(f"Horas laboradas: {resultado6['minutos_laborados'] / 60:.2f}")
print(f"Expected: 480 minutos laborados, 0 minutos extra (requiere validacion RRHH)")
print(f"Status: {'[PASS]' if resultado6['minutos_laborados'] == 480 and resultado6['minutos_extra'] == 0 and len(resultado6['bloques_extra']) == 1 else '[FAIL]'}")

# Caso 7: Empleado con visita (fuera de horario)
print("\n[ CASO 7 ] Empleado con visita (fuera de horario)")
print("-" * 80)
if not session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST007')):
    emp7 = Empleado(
        numero_empleado='TEST007',
        nombre_completo='Empleado Prueba 7',
        departamento_id=dept_pruebas.id,
        puesto='Prueba',
        estado_actual='Fuera'
    )
    session.add(emp7)
    session.flush()
else:
    emp7 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST007'))

if not session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp7.id)):
    turno7 = TurnoHorario(
        empleado_id=emp7.id,
        dia_semana=1,  # Martes
        hora_entrada_oficial=time(8, 0),
        hora_salida_oficial=time(16, 0),
        tolerancia_minutos=15
    )
    session.add(turno7)
    session.flush()

fecha_test7 = date(2026, 7, 1)
reg7 = RegistroAsistencia(
    empleado_id=emp7.id,
    fecha_turno=fecha_test7,
    hora_entrada_real=datetime.combine(fecha_test7, time(8, 0)),
    hora_salida_real=datetime.combine(fecha_test7, time(16, 0)),
    estado_registro='Normal'
)
session.add(reg7)
session.flush()

eventos_caso7 = [
    EventoAsistencia(
        empleado_id=emp7.id,
        asistencia_id=reg7.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=datetime.combine(fecha_test7, time(8, 0)),
        observaciones='Entrada normal'
    ),
    EventoAsistencia(
        empleado_id=emp7.id,
        asistencia_id=reg7.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=datetime.combine(fecha_test7, time(16, 0)),
        observaciones='Salida normal'
    ),
    EventoAsistencia(
        empleado_id=emp7.id,
        asistencia_id=reg7.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=datetime.combine(fecha_test7, time(17, 0)),
        observaciones='Entrada visita'
    ),
    EventoAsistencia(
        empleado_id=emp7.id,
        asistencia_id=reg7.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=datetime.combine(fecha_test7, time(18, 0)),
        observaciones='Salida visita'
    )
]
for e in eventos_caso7:
    session.add(e)
session.flush()

resultado7 = calcular_horas_laboradas(session, emp7.id, fecha_test7)
print(f"Turno: 08:00 - 16:00, Visita: 17:00 - 18:00")
print(f"Minutos laborados: {resultado7['minutos_laborados']}")
print(f"Minutos extra: {resultado7['minutos_extra']}")
print(f"Minutos descanso: {resultado7['minutos_descanso']}")
print(f"Bloques extra: {len(resultado7['bloques_extra'])}")
print(f"Horas laboradas: {resultado7['minutos_laborados'] / 60:.2f}")
print(f"Expected: 540 minutos laborados (visita cuenta hasta validacion RRHH)")
print(f"Status: {'[PASS]' if resultado7['minutos_laborados'] == 540 and resultado7['minutos_extra'] == 0 else '[FAIL]'}")

# Resumen
print("\n" + "=" * 80)
print("RESUMEN DE PRUEBAS")
print("=" * 80)
print("Caso 1: Turno normal sin salidas temporales")
print("Caso 2: Retardo aprobado")
print("Caso 3: Salida temporal de comida")
print("Caso 4: Salida temporal de permiso personal")
print("Caso 5: Horas extra previas")
print("Caso 6: Horas extra posteriores")
print("Caso 7: Visita fuera de horario")
print("\nPara validar horas extra por supervisor/RRHH, usar la interfaz web.")
print("Para validar visitas por RRHH, usar la interfaz web.")

session.commit()
print("\nPruebas completadas. Datos de prueba guardados en la base de datos.")
