import pytest
from datetime import datetime, time, date
from app.models import RegistroAsistencia, BloqueHorasExtra, EstadoRegistro
from app.services import calcular_y_registrar_bloques_horas_extra


def test_bloque_extra_antes_inicio(db_session, test_data):
    """Prueba: Bloque de horas extra antes del inicio del turno"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Entrada 07:30 (30 minutos antes del turno que inicia a las 08:00)
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(7, 30)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    # Calcular bloques de horas extra
    calcular_y_registrar_bloques_horas_extra(db_session, registro, registro.hora_entrada_real, registro.hora_salida_real)
    
    # Verificar que se creó un bloque ANTES_INICIO
    bloques = db_session.query(BloqueHorasExtra).filter(
        BloqueHorasExtra.asistencia_id == registro.id
    ).all()
    
    assert len(bloques) == 1
    assert bloques[0].tipo_bloque == "ANTES_INICIO"
    # Debería haber minutos extra (el valor exacto depende de la lógica de tolerancia)
    assert bloques[0].minutos_extra > 0


def test_bloque_extra_despues_fin(db_session, test_data):
    """Prueba: Bloque de horas extra después del fin del turno"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Salida 17:30 (30 minutos después del turno que termina a las 17:00)
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(8, 0)),
        hora_salida_real=datetime.combine(fecha, time(17, 30)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    calcular_y_registrar_bloques_horas_extra(db_session, registro, registro.hora_entrada_real, registro.hora_salida_real)
    
    bloques = db_session.query(BloqueHorasExtra).filter(
        BloqueHorasExtra.asistencia_id == registro.id
    ).all()
    
    assert len(bloques) == 1
    assert bloques[0].tipo_bloque == "DESPUES_FIN"
    # Debería haber minutos extra (el valor exacto depende de la lógica de tolerancia)
    assert bloques[0].minutos_extra > 0


def test_bloque_extra_dentro_horario(db_session, test_data):
    """Prueba: No se crea bloque extra si está dentro del horario"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    # Entrada y salida dentro del horario
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(8, 0)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    calcular_y_registrar_bloques_horas_extra(db_session, registro, registro.hora_entrada_real, registro.hora_salida_real)
    
    bloques = db_session.query(BloqueHorasExtra).filter(
        BloqueHorasExtra.asistencia_id == registro.id
    ).all()
    
    # No debería haber bloques extra
    assert len(bloques) == 0


def test_validacion_supervisor(db_session, test_data):
    """Prueba: Validación de supervisor para bloque de horas extra"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(7, 30)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    calcular_y_registrar_bloques_horas_extra(db_session, registro, registro.hora_entrada_real, registro.hora_salida_real)
    
    bloque = db_session.query(BloqueHorasExtra).filter(
        BloqueHorasExtra.asistencia_id == registro.id
    ).first()
    
    # Validar por supervisor
    bloque.validacion_supervisor = True
    db_session.commit()
    
    # Verificar que se guardó
    db_session.refresh(bloque)
    assert bloque.validacion_supervisor == True


def test_validacion_rrhh(db_session, test_data):
    """Prueba: Validación de RRHH para bloque de horas extra"""
    empleado = test_data["empleado"]
    fecha = date(2026, 6, 22)
    
    registro = RegistroAsistencia(
        empleado_id=empleado.id,
        fecha_turno=fecha,
        hora_entrada_real=datetime.combine(fecha, time(7, 30)),
        hora_salida_real=datetime.combine(fecha, time(17, 0)),
        estado_registro=EstadoRegistro.NORMAL
    )
    db_session.add(registro)
    db_session.commit()
    
    calcular_y_registrar_bloques_horas_extra(db_session, registro, registro.hora_entrada_real, registro.hora_salida_real)
    
    bloque = db_session.query(BloqueHorasExtra).filter(
        BloqueHorasExtra.asistencia_id == registro.id
    ).first()
    
    # Validar por supervisor y RRHH
    bloque.validacion_supervisor = True
    bloque.validacion_rrhh = True
    db_session.commit()
    
    db_session.refresh(bloque)
    assert bloque.validacion_supervisor == True
    assert bloque.validacion_rrhh == True
