import pytest
from datetime import datetime, time, date, timedelta
from app.models import RegistroAsistencia, SalidaTemporal, EstadoRegistro, TipoSalida
from app.services import calcular_horas_laboradas


def test_salida_temporal_dentro_turno(db_session, test_data):
    """Prueba: Salida temporal dentro del turno"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Registro principal
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(8, 0)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    # Salida temporal de 12:00 a 13:00
    salida = SalidaTemporal(
        asistencia_id=registro.id,
        tipo_salida=TipoSalida.PERMISO_PERSONAL,
        hora_salida=datetime.combine(fecha, time(12, 0)),
        hora_regreso=datetime.combine(fecha, time(13, 0))
    )
    db_session.add(salida)
    db_session.commit()
    
    # Verificar que la salida temporal se creó correctamente
    assert salida.id is not None
    assert salida.asistencia_id == registro.id
    assert salida.tipo_salida == TipoSalida.PERMISO_PERSONAL


def test_salida_temporal_fuera_turno(db_session, test_data):
    """Prueba: Salida temporal fuera del turno no se descuenta"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(8, 0)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    # Salida temporal fuera del turno (18:00-19:00)
    salida = SalidaTemporal(
        asistencia_id=registro.id,
        tipo_salida=TipoSalida.PERMISO_PERSONAL,
        hora_salida=datetime.combine(fecha, time(18, 0)),
        hora_regreso=datetime.combine(fecha, time(19, 0))
    )
    db_session.add(salida)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # No debería descuentar porque está fuera del turno
    assert resultado["minutos_laborados"] == 540


def test_multiples_salidas_temporales(db_session, test_data):
    """Prueba: Múltiples salidas temporales en el mismo día"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(8, 0)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    # Dos salidas temporales
    salida1 = SalidaTemporal(
        asistencia_id=registro.id,
        tipo_salida=TipoSalida.PERMISO_PERSONAL,
        hora_salida=datetime.combine(fecha, time(10, 0)),
        hora_regreso=datetime.combine(fecha, time(10, 30))
    )
    
    salida2 = SalidaTemporal(
        asistencia_id=registro.id,
        tipo_salida=TipoSalida.PERMISO_PERSONAL,
        hora_salida=datetime.combine(fecha, time(15, 0)),
        hora_regreso=datetime.combine(fecha, time(15, 30))
    )
    
    db_session.add_all([salida1, salida2])
    db_session.commit()
    
    # Verificar que las salidas temporales se crearon correctamente
    assert salida1.id is not None
    assert salida2.id is not None
    assert salida1.asistencia_id == registro.id
    assert salida2.asistencia_id == registro.id


def test_salida_temporal_sin_regreso(db_session, test_data):
    """Prueba: Salida temporal sin regreso (abandono)"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(8, 0)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    # Salida temporal sin regreso
    salida = SalidaTemporal(
        asistencia_id=registro.id,
        tipo_salida=TipoSalida.PERMISO_PERSONAL,
        hora_salida=datetime.combine(fecha, time(12, 0)),
        hora_regreso=None
    )
    db_session.add(salida)
    db_session.commit()
    
    # Verificar que la salida temporal se creó correctamente sin regreso
    assert salida.id is not None
    assert salida.hora_regreso is None
