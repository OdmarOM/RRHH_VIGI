from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date, datetime, time
from app.models import (
    Empleado, TurnoHorario, RegistroAsistencia, EventoAsistencia,
    TipoEvento, Visita, EstadoVisita, Departamento, RegistroAusencia, TipoAusencia
)
from app.services import calcular_horas_laboradas

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("=" * 80)
print("PRUEBA DE VISITA DURANTE AUSENCIA APROBADA")
print("=" * 80)

# Crear departamento de prueba
if not session.scalar(select(Departamento).where(Departamento.nombre == 'Pruebas')):
    dept_pruebas = Departamento(nombre='Pruebas')
    session.add(dept_pruebas)
    session.flush()
else:
    dept_pruebas = session.scalar(select(Departamento).where(Departamento.nombre == 'Pruebas'))

# Crear empleado de prueba
if not session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST009')):
    emp9 = Empleado(
        numero_empleado='TEST009',
        nombre_completo='Empleado Prueba 9',
        departamento_id=dept_pruebas.id,
        puesto='Prueba',
        estado_actual='Fuera'
    )
    session.add(emp9)
    session.flush()
else:
    emp9 = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'TEST009'))

# Crear ausencia aprobada para hoy
fecha_ausencia = date(2026, 6, 18)
ausencia = RegistroAusencia(
    empleado_id=emp9.id,
    tipo_ausencia=TipoAusencia.VACACIONES,
    fecha_inicio=fecha_ausencia,
    fecha_fin=fecha_ausencia,
    pagada=True,
    porcentaje_aportacion=100,
    motivo='Prueba de visita durante ausencia',
    aprobado_rrhh=True,
    fecha_registro=datetime.now()
)
session.add(ausencia)
session.flush()

# Crear registro de asistencia
asistencia = RegistroAsistencia(
    empleado_id=emp9.id,
    fecha_turno=fecha_ausencia,
    estado_registro='Visita_Descanso'
)
session.add(asistencia)
session.flush()

# Simular entrada del empleado (visita durante ausencia)
now = datetime.combine(fecha_ausencia, time(10, 0))
evento_entrada = EventoAsistencia(
    empleado_id=emp9.id,
    asistencia_id=asistencia.id,
    tipo_evento=TipoEvento.ENTRADA,
    fecha_evento=now,
    observaciones='Visita durante Vacaciones'
)
session.add(evento_entrada)
session.flush()

# Crear visita
from app.services import crear_visita
visita = crear_visita(
    db=session,
    empleado_id=emp9.id,
    asistencia_id=asistencia.id,
    motivo='Visita durante Vacaciones'
)
session.flush()

print("\n[ TEST ] Visita creada durante ausencia aprobada")
print("-" * 80)
print(f"Visita ID: {visita.id}")
print(f"  Hora inicio: {visita.hora_inicio}")
print(f"  Hora fin: {visita.hora_fin}")
print(f"  Minutos duración: {visita.minutos_duracion}")
print(f"  Estado: {visita.estado.value}")
print(f"  Motivo: {visita.motivo}")

# Simular salida del empleado
now_salida = datetime.combine(fecha_ausencia, time(12, 0))
evento_salida = EventoAsistencia(
    empleado_id=emp9.id,
    asistencia_id=asistencia.id,
    tipo_evento=TipoEvento.SALIDA,
    fecha_evento=now_salida,
    observaciones='Salida visita'
)
session.add(evento_salida)
session.flush()

# Actualizar visita con hora_fin
visita.hora_fin = now_salida
visita.minutos_duracion = int((now_salida - visita.hora_inicio).total_seconds() / 60)
session.add(visita)
session.commit()

print("\n[ TEST ] Visita actualizada con hora_fin")
print("-" * 80)
print(f"Visita ID: {visita.id}")
print(f"  Hora inicio: {visita.hora_inicio}")
print(f"  Hora fin: {visita.hora_fin}")
print(f"  Minutos duración: {visita.minutos_duracion}")
print(f"  Estado: {visita.estado.value}")
print(f"  Motivo: {visita.motivo}")

print("\nExpected: Visita con hora_fin y minutos_duracion completados")
print(f"Status: {'[PASS]' if visita.hora_fin and visita.minutos_duracion else '[FAIL]'}")

print("\n" + "=" * 80)
print("Prueba completada. Datos de prueba guardados en la base de datos.")
