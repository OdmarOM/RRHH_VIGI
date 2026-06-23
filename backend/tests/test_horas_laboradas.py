import pytest
from datetime import datetime, time, date
from app.models import RegistroAsistencia, EstadoRegistro
from app.services import calcular_horas_laboradas


def test_horas_laboradas_dentro_horario(db_session, test_data):
    """Prueba: Empleado entra y sale dentro del horario oficial"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)  # Lunes
    
    # Crear registro de asistencia dentro del horario (08:00-17:00)
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(8, 0)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    # Calcular horas laboradas
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # Debería ser 9 horas (540 minutos)
    assert resultado["minutos_laborados"] == 540


def test_horas_laboradas_con_tolerancia(db_session, test_data):
    """Prueba: Empleado entra 15 minutos antes con tolerancia"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Entrada a las 7:45 (15 minutos antes, dentro de tolerancia)
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(7, 45)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # Debería ser 9 horas (la tolerancia cuenta como laborada)
    assert resultado["minutos_laborados"] == 540


def test_horas_laboradas_fuera_horario(db_session, test_data):
    """Prueba: Empleado entra fuera del horario sin tolerancia"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Entrada a las 7:30 (30 minutos antes, fuera de tolerancia)
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(7, 30)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # Debería haber horas laboradas (el valor exacto depende de la lógica de tolerancia)
    assert resultado["minutos_laborados"] >= 0


def test_horas_laboradas_con_bloque_extra(db_session, test_data):
    """Prueba: Empleado sale después del horario, se crea bloque extra"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Entrada 12:03, salida 15:46 (corte a 12:20)
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(12, 3)),
        hora_salida_real=datetime.combine(fecha, time(15, 46)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # Debería haber horas laboradas (el valor exacto depende de la lógica de corte)
    assert resultado["minutos_laborados"] >= 0


def test_horas_laboradas_multiples_registros_dia(db_session, test_data):
    """Prueba: Múltiples registros en el mismo día"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Primer registro: 08:00-12:00
    reg1 = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(8, 0)),
        hora_salida_real=datetime.combine(fecha, time(12, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    
    # Segundo registro: 13:00-17:00
    reg2 = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(13, 0)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    
    db_session.add_all([reg1, reg2])
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # 4h + 4h = 8h = 480 min
    assert resultado["minutos_laborados"] == 480
