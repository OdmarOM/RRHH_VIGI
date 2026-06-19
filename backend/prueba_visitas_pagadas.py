from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date, datetime, time
from app.models import (
    Empleado, TurnoHorario, RegistroAsistencia, EventoAsistencia,
    TipoEvento, Visita, EstadoVisita, Departamento
)
from app.services import calcular_horas_laboradas

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("=" * 80)
print("PRUEBA DE VISITAS PAGADAS")
print("=" * 80)

# Crear departamento de prueba
if not session.scalar(select(Departamento).where(Departamento.nombre == 'Pruebas')):
    dept_pruebas = Departamento(nombre='Pruebas')
    session.add(dept_pruebas)
    session.flush()
else:
    dept_pruebas = session.scalar(select(Departamento).where(Departamento.nombre == 'Pruebas'))

# Crear empleado de prueba
if not session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST008')):
    emp8 = Empleado(
        numero_empleado='TEST008',
        nombre_completo='Empleado Prueba 8',
        departamento_id=dept_pruebas.id,
        puesto='Prueba',
        estado_actual='Fuera'
    )
    session.add(emp8)
    session.flush()
else:
    emp8 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST008'))

# Crear turno de prueba (8:00 AM - 4:00 PM)
if not session.scalar(select(TurnoHorario).where(TurnoHorario.empleado_id == emp8.id)):
    turno8 = TurnoHorario(
        empleado_id=emp8.id,
        dia_semana=0,  # Lunes
        hora_entrada_oficial=time(8, 0),
        hora_salida_oficial=time(16, 0),
        tolerancia_minutos=15
    )
    session.add(turno8)
    session.commit()
    session.flush()

fecha_test = date(2026, 6, 29)  # Lunes

# Crear registro de asistencia normal
reg8 = RegistroAsistencia(
    empleado_id=emp8.id,
    fecha_turno=fecha_test,
    hora_entrada_real=datetime.combine(fecha_test, time(8, 0)),
    hora_salida_real=datetime.combine(fecha_test, time(16, 0)),
    estado_registro='Normal'
)
session.add(reg8)
session.flush()

# Crear eventos del turno normal
eventos_turno = [
    EventoAsistencia(
        empleado_id=emp8.id,
        asistencia_id=reg8.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=datetime.combine(fecha_test, time(8, 0)),
        observaciones='Entrada normal'
    ),
    EventoAsistencia(
        empleado_id=emp8.id,
        asistencia_id=reg8.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=datetime.combine(fecha_test, time(16, 0)),
        observaciones='Salida normal'
    )
]
for e in eventos_turno:
    session.add(e)
session.flush()

# Crear visita fuera de horario (17:00 - 18:00)
visita = Visita(
    empleado_id=emp8.id,
    asistencia_id=reg8.id,
    fecha_visita=datetime.combine(fecha_test, time(17, 0)),
    hora_inicio=datetime.combine(fecha_test, time(17, 0)),
    hora_fin=datetime.combine(fecha_test, time(18, 0)),
    minutos_duracion=60,
    estado=EstadoVisita.PENDIENTE,
    motivo='Visita de prueba'
)
session.add(visita)
session.flush()

print("\n[ TEST 1 ] Visita PENDIENTE (no debe contar como laborados)")
print("-" * 80)
resultado1 = calcular_horas_laboradas(session, emp8.id, fecha_test)
print(f"Turno: 08:00 - 16:00, Visita: 17:00 - 18:00 (PENDIENTE)")
print(f"Minutos laborados: {resultado1['minutos_laborados']}")
print(f"Minutos extra: {resultado1['minutos_extra']}")
print(f"Minutos descanso: {resultado1['minutos_descanso']}")
print(f"Horas laboradas: {resultado1['minutos_laborados'] / 60:.2f}")
print(f"Expected: 480 minutos laborados (visita PENDIENTE no cuenta)")
print(f"Status: {'[PASS]' if resultado1['minutos_laborados'] == 480 else '[FAIL]'}")

# Cambiar visita a PAGADA
visita.estado = EstadoVisita.PAGADA
session.add(visita)
session.commit()

print("\n[ TEST 2 ] Visita PAGADA (debe contar como laborados)")
print("-" * 80)
resultado2 = calcular_horas_laboradas(session, emp8.id, fecha_test)
print(f"Turno: 08:00 - 16:00, Visita: 17:00 - 18:00 (PAGADA)")
print(f"Minutos laborados: {resultado2['minutos_laborados']}")
print(f"Minutos extra: {resultado2['minutos_extra']}")
print(f"Minutos descanso: {resultado2['minutos_descanso']}")
print(f"Horas laboradas: {resultado2['minutos_laborados'] / 60:.2f}")
print(f"Expected: 540 minutos laborados (visita PAGADA cuenta)")
print(f"Status: {'[PASS]' if resultado2['minutos_laborados'] == 540 else '[FAIL]'}")

# Cambiar visita a NO_PAGADA
visita.estado = EstadoVisita.NO_PAGADA
session.add(visita)
session.commit()

print("\n[ TEST 3 ] Visita NO_PAGADA (no debe contar como laborados)")
print("-" * 80)
resultado3 = calcular_horas_laboradas(session, emp8.id, fecha_test)
print(f"Turno: 08:00 - 16:00, Visita: 17:00 - 18:00 (NO_PAGADA)")
print(f"Minutos laborados: {resultado3['minutos_laborados']}")
print(f"Minutos extra: {resultado3['minutos_extra']}")
print(f"Minutos descanso: {resultado3['minutos_descanso']}")
print(f"Horas laboradas: {resultado3['minutos_laborados'] / 60:.2f}")
print(f"Expected: 480 minutos laborados (visita NO_PAGADA no cuenta)")
print(f"Status: {'[PASS]' if resultado3['minutos_laborados'] == 480 else '[FAIL]'}")

print("\n" + "=" * 80)
print("RESUMEN DE PRUEBAS DE VISITAS PAGADAS")
print("=" * 80)
print("Test 1: Visita PENDIENTE - No cuenta como laborados")
print("Test 2: Visita PAGADA - Cuenta como laborados")
print("Test 3: Visita NO_PAGADA - No cuenta como laborados")
print("\nPara validar visitas como pagadas, usar la interfaz web de RRHH.")

session.commit()
print("\nPruebas completadas. Datos de prueba guardados en la base de datos.")
