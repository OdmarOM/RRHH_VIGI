import pytest
from datetime import datetime, time, date
from app.models import RegistroAsistencia, RegistroAusencia, EstadoRegistro, TipoAusencia
from app.services import verificar_ausencia_aprobada, calcular_horas_laboradas


def test_ausencia_no_pagada_no_cuenta(db_session, test_data):
    """Prueba: Ausencia no pagada no se cuenta en horas laboradas"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Crear ausencia no pagada
    ausencia = RegistroAusencia(
        empleado_id=empleado.id,
        fecha_inicio=fecha,
        fecha_fin=fecha,
        tipo_ausencia=TipoAusencia.PERMISO,
        pagada=False,
        porcentaje_aportacion=0,
        aprobado_rrhh=True,
        fecha_registro=datetime.now()
    )
    db_session.add(ausencia)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # No debería contar horas
    assert resultado["minutos_laborados"] == 0


def test_ausencia_pagada_cuenta_parcial(db_session, test_data):
    """Prueba: Ausencia pagada cuenta según porcentaje de aportación"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Crear ausencia pagada al 100%
    ausencia = RegistroAusencia(
        empleado_id=empleado.id,
        fecha_inicio=fecha,
        fecha_fin=fecha,
        tipo_ausencia=TipoAusencia.VACACIONES,
        pagada=True,
        porcentaje_aportacion=100,
        aprobado_rrhh=True,
        fecha_registro=datetime.now()
    )
    db_session.add(ausencia)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # Debería contar 9 horas (100% del día laboral)
    assert resultado["minutos_laborados"] == 540


def test_ausencia_50_aportacion(db_session, test_data):
    """Prueba: Ausencia pagada al 50%"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    ausencia = RegistroAusencia(
        empleado_id=empleado.id,
        fecha_inicio=fecha,
        fecha_fin=fecha,
        tipo_ausencia=TipoAusencia.INCAPACIDAD,
        pagada=True,
        porcentaje_aportacion=50,
        aprobado_rrhh=True,
        fecha_registro=datetime.now()
    )
    db_session.add(ausencia)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # Debería contar 4.5 horas (50% de 9 horas)
    assert resultado["minutos_laborados"] == 270


def test_ausencia_no_aprobada(db_session, test_data):
    """Prueba: Ausencia no aprobada no se cuenta"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    ausencia = RegistroAusencia(
        empleado_id=empleado.id,
        fecha_inicio=fecha,
        fecha_fin=fecha,
        tipo_ausencia=TipoAusencia.PERMISO,
        pagada=True,
        porcentaje_aportacion=100,
        aprobado_rrhh=False,
        fecha_registro=datetime.now()
    )
    db_session.add(ausencia)
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # No debería contar porque no está aprobada
    assert resultado["minutos_laborados"] == 0


def test_verificar_ausencia_aprobada(db_session, test_data):
    """Prueba: Función verificar_ausencia_aprobada"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    ausencia = RegistroAusencia(
        empleado_id=empleado.id,
        fecha_inicio=fecha,
        fecha_fin=fecha,
        tipo_ausencia=TipoAusencia.VACACIONES,
        pagada=True,
        porcentaje_aportacion=100,
        aprobado_rrhh=True,
        fecha_registro=datetime.now()
    )
    db_session.add(ausencia)
    db_session.commit()
    
    resultado = verificar_ausencia_aprobada(db_session, empleado.id, fecha)
    
    assert resultado is not None
    assert resultado["tipo_ausencia"] == TipoAusencia.VACACIONES
    assert resultado["pagada"] == True
    assert resultado["porcentaje_aportacion"] == 100


def test_ausencia_con_registro_normal(db_session, test_data):
    """Prueba: Ausencia + registro normal en el mismo día"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Ausencia por la mañana
    ausencia = RegistroAusencia(
        empleado_id=empleado.id,
        fecha_inicio=fecha,
        fecha_fin=fecha,
        tipo_ausencia=TipoAusencia.PERMISO,
        pagada=True,
        porcentaje_aportacion=100,
        aprobado_rrhh=True,
        fecha_registro=datetime.now()
    )
    
    # Registro por la tarde (no debería contar si hay ausencia aprobada)
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(13, 0)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    
    db_session.add_all([ausencia, registro])
    db_session.commit()
    
    resultado = calcular_horas_laboradas(db_session, empleado.id, fecha)
    
    # Debería contar la ausencia (9h) y no el registro
    assert resultado["minutos_laborados"] == 540
