from datetime import datetime, time, timedelta, date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Empleado, EventoAsistencia, RegistroAsistencia, TipoEvento, TipoSalida
from app.services import calcular_horas_laboradas, utc_now

engine = create_engine('sqlite:///rrhh_dev.db')
db = Session(engine)

emp = db.scalar(select(Empleado).where(Empleado.numero_empleado == 'EMP001'))
fecha = date(2030, 6, 17)

# Limpiar datos
asistencias = db.scalars(
    select(RegistroAsistencia).where(
        RegistroAsistencia.empleado_id == emp.id,
        RegistroAsistencia.fecha_turno == fecha
    )
).all()
for a in asistencias:
    eventos = db.scalars(select(EventoAsistencia).where(EventoAsistencia.asistencia_id == a.id)).all()
    for e in eventos:
        db.delete(e)
    db.delete(a)
db.commit()

# Crear asistencia
asistencia = RegistroAsistencia(
    empleado_id=emp.id,
    fecha_turno=fecha,
    hora_entrada_real=datetime.combine(fecha, time(9, 0)),
    hora_salida_real=datetime.combine(fecha, time(17, 0))
)
db.add(asistencia)
db.flush()

now = utc_now()
# Eventos
db.add(EventoAsistencia(
    empleado_id=emp.id,
    asistencia_id=asistencia.id,
    tipo_evento=TipoEvento.ENTRADA,
    fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
))
db.add(EventoAsistencia(
    empleado_id=emp.id,
    asistencia_id=asistencia.id,
    tipo_evento=TipoEvento.SALIDA_TEMPORAL,
    fecha_evento=datetime.combine(fecha, time(12, 0)).replace(tzinfo=now.tzinfo),
    tipo_salida=TipoSalida.PERMISO_PERSONAL.value
))
db.add(EventoAsistencia(
    empleado_id=emp.id,
    asistencia_id=asistencia.id,
    tipo_evento=TipoEvento.REGRESO_SALIDA_TEMPORAL,
    fecha_evento=datetime.combine(fecha, time(13, 0)).replace(tzinfo=now.tzinfo)
))
db.add(EventoAsistencia(
    empleado_id=emp.id,
    asistencia_id=asistencia.id,
    tipo_evento=TipoEvento.SALIDA,
    fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
))
db.commit()

resultado = calcular_horas_laboradas(db, emp.id, fecha)
print(f'minutos_laborados: {resultado["minutos_laborados"]}')
print(f'minutos_descanso: {resultado["minutos_descanso"]}')
print(f'minutos_extra: {resultado["minutos_extra"]}')
print(f'eventos: {len(resultado["eventos"])}')
print(f'bloques_extra: {resultado["bloques_extra"]}')
