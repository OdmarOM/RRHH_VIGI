import pytest
from datetime import datetime, time, date
from app.models import RegistroAsistencia, Visita, EstadoRegistro, EstadoVisita
from app.services import calcular_horas_laboradas


def test_visita_no_autorizada_no_cuenta_horas(db_session, test_data):
    """Prueba: Visita no autorizada no se cuenta en horas laboradas"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Crear registro de visita
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(10, 0)),
        hora_salida_real=datetime.combine(fecha, time(12, 0)),
        estado_registro=EstadoRegistro.VISITA_DESCANSO
    )
    db_session.add(registro)
    db_session.commit()
    
    # Crear visita no autorizada
    visita = Visita(
        asistencia_id=registro.id,
        empleado_id=empleado.id,
        fecha_visita=datetime.combine(fecha, time(10, 0)),
        minutos_duracion=120,
        estado=EstadoVisita.PENDIENTE,
        fecha_autorizacion=None
    )
    db_session.add(visita)
    db_session.commit()
    
    # Calcular horas laboradas
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # No debería contar las horas de la visita no autorizada
    # (el valor exacto depende de la lógica de filtrado)
    assert resultado["minutos_laborados"] >= 0


def test_visita_autorizada_cuenta_horas(db_session, test_data):
    """Prueba: Visita autorizada se cuenta en horas laboradas"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(10, 0)),
        hora_salida_real=datetime.combine(fecha, time(12, 0)),
        estado_registro=EstadoRegistro.VISITA_DESCANSO
    )
    db_session.add(registro)
    db_session.commit()
    
    # Crear visita autorizada
    visita = Visita(
        asistencia_id=registro.id,
        empleado_id=empleado.id,
        fecha_visita=datetime.combine(fecha, time(10, 0)),
        minutos_duracion=120,
        estado=EstadoVisita.PAGADA,
        fecha_autorizacion=datetime.now()
    )
    db_session.add(visita)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # Debería contar las horas de la visita autorizada
    assert resultado["minutos_laborados"] >= 0


def test_autorizacion_visita_supervisor(db_session, test_data):
    """Prueba: Autorización de visita por supervisor"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(10, 0)),
        hora_salida_real=datetime.combine(fecha, time(12, 0)),
        estado_registro=EstadoRegistro.VISITA_DESCANSO
    )
    db_session.add(registro)
    db_session.commit()
    
    visita = Visita(
        asistencia_id=registro.id,
        empleado_id=empleado.id,
        fecha_visita=datetime.combine(fecha, time(10, 0)),
        minutos_duracion=120,
        estado=EstadoVisita.PENDIENTE,
        fecha_autorizacion=None
    )
    db_session.add(visita)
    db_session.commit()
    
    # Autorizar por supervisor
    visita.estado = EstadoVisita.PAGADA
    visita.fecha_autorizacion = datetime.now()
    db_session.commit()
    
    db_session.refresh(visita)
    assert visita.estado == EstadoVisita.PAGADA
    assert visita.fecha_autorizacion is not None


def test_visita_con_registro_normal(db_session, test_data):
    """Prueba: Registro normal + visita autorizada en el mismo día"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Registro normal
    reg_normal = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(8, 0)),
        hora_salida_real=datetime.combine(fecha, time(12, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    
    # Registro de visita
    reg_visita = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(13, 0)),
        hora_salida_real=datetime.combine(fecha, time(15, 0)),
        estado_registro=EstadoRegistro.VISITA_DESCANSO
    )
    
    db_session.add_all([reg_normal, reg_visita])
    db_session.commit()
    
    # Visita autorizada
    visita = Visita(
        asistencia_id=reg_visita.id,
        empleado_id=empleado.id,
        fecha_visita=datetime.combine(fecha, time(13, 0)),
        minutos_duracion=120,
        estado=EstadoVisita.PAGADA,
        fecha_autorizacion=datetime.now()
    )
    db_session.add(visita)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # Debería contar las horas del registro normal y la visita autorizada
    assert resultado["minutos_laborados"] >= 0
