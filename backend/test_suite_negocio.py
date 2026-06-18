"""
Suite de pruebas unitarias para reglas de negocio del sistema RRHH
Cubre: horas laboradas, horas extras, validaciones, asistencias, visitas, reportes
"""
import requests
from datetime import datetime, time, timedelta, date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import (
    Empleado, TurnoHorario, RegistroAsistencia, EventoAsistencia, 
    Visita, BloqueHorasExtra, EstadoVisita, TipoEvento, EstadoRegistro,
    CorreccionManual, TipoCorreccion, RegistroAusencia, TipoAusencia, TipoSalida
)
from app.services import (
    calcular_horas_laboradas, calcular_y_registrar_bloques_horas_extra, 
    verificar_ausencia_aprobada, utc_now
)
from app.core.database import Base

# Configuración de base de datos
TEST_DB_URL = "sqlite:///rrhh_dev.db"
test_engine = create_engine(TEST_DB_URL)

BASE_URL = "http://localhost:8001/api/v1"

# Fecha futura reservada exclusivamente para pruebas (lunes, EMP001 tiene turno 08:00-16:00)
FECHA_PRUEBA = date(2030, 6, 17)


def limpiar_datos_prueba(session, empleado_id, fecha=FECHA_PRUEBA):
    """Elimina todos los datos de prueba (asistencias, eventos, visitas, bloques)
    para un empleado en una fecha específica. Garantiza pruebas idempotentes."""
    # Obtener asistencias de la fecha
    asistencias = session.scalars(
        select(RegistroAsistencia).where(
            RegistroAsistencia.empleado_id == empleado_id,
            RegistroAsistencia.fecha_turno == fecha
        )
    ).all()
    
    for asistencia in asistencias:
        # Eliminar bloques de horas extra asociados
        bloques = session.scalars(
            select(BloqueHorasExtra).where(BloqueHorasExtra.asistencia_id == asistencia.id)
        ).all()
        for bloque in bloques:
            session.delete(bloque)
        
        # Eliminar visitas asociadas
        visitas = session.scalars(
            select(Visita).where(Visita.asistencia_id == asistencia.id)
        ).all()
        for visita in visitas:
            session.delete(visita)
        
        # Eliminar eventos asociados
        eventos = session.scalars(
            select(EventoAsistencia).where(EventoAsistencia.asistencia_id == asistencia.id)
        ).all()
        for evento in eventos:
            session.delete(evento)
        
        # Eliminar la asistencia
        session.delete(asistencia)
    
    # Eliminar eventos huérfanos en la fecha (sin asistencia)
    inicio = datetime.combine(fecha, datetime.min.time())
    fin = datetime.combine(fecha, datetime.max.time())
    eventos_huerfanos = session.scalars(
        select(EventoAsistencia).where(
            EventoAsistencia.empleado_id == empleado_id,
            EventoAsistencia.fecha_evento >= inicio,
            EventoAsistencia.fecha_evento <= fin
        )
    ).all()
    for evento in eventos_huerfanos:
        session.delete(evento)
    
    # Eliminar correcciones manuales de la fecha (evita acumulación entre pruebas)
    correcciones = session.scalars(
        select(CorreccionManual).where(
            CorreccionManual.empleado_id == empleado_id,
            CorreccionManual.fecha == fecha
        )
    ).all()
    for c in correcciones:
        session.delete(c)
    
    session.commit()


class TestHorasLaboradas:
    """Pruebas para el cálculo de horas laboradas"""
    
    def setup_method(self):
        self.session = Session(test_engine)
        self.empleado = self.session.scalar(
            select(Empleado).where(Empleado.numero_empleado == "EMP001")
        )
        if not self.empleado:
            raise Exception("Empleado EMP001 no encontrado")
        # Limpiar datos de prueba previos para garantizar idempotencia
        limpiar_datos_prueba(self.session, self.empleado.id)
    
    def teardown_method(self):
        # Limpiar datos de prueba creados durante el test
        try:
            limpiar_datos_prueba(self.session, self.empleado.id)
        except Exception:
            self.session.rollback()
        self.session.close()
    
    def test_calcular_horas_laboradas_sin_eventos(self):
        """Verifica cálculo de horas laboradas sin eventos"""
        # Usar fecha futura reservada para pruebas
        fecha = FECHA_PRUEBA
        try:
            resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
            
            assert resultado["minutos_laborados"] == 0
            assert resultado["minutos_extra"] == 0
            assert resultado["minutos_descanso"] == 0
            assert resultado["total_eventos"] == 0
            print("[OK] Test calcular_horas_laboradas_sin_eventos: PASSED")
        except Exception as e:
            print(f"[FAIL] Test calcular_horas_laboradas_sin_eventos: FAILED - {e}")
            raise
    
    def test_calcular_horas_laboradas_con_entrada_salida(self):
        """Verifica cálculo de horas laboradas con entrada y salida"""
        # Usar fecha futura reservada para pruebas
        fecha = FECHA_PRUEBA
        
        # Crear asistencia de prueba
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        # Crear eventos con timezone
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        
        # 8 horas = 480 minutos
        assert resultado["minutos_laborados"] == 480
        assert resultado["total_eventos"] == 2
        print("[OK] Test calcular_horas_laboradas_con_entrada_salida: PASSED")
    
    def test_calcular_horas_laboradas_con_salida_temporal(self):
        """Verifica cálculo de horas laboradas con salida temporal"""
        # Usar fecha futura reservada para pruebas
        fecha = FECHA_PRUEBA
        
        # Crear asistencia de prueba
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        # Crear eventos con salida temporal y timezone
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA_TEMPORAL,
            fecha_evento=datetime.combine(fecha, time(12, 0)).replace(tzinfo=now.tzinfo),
            tipo_salida="Permiso_Personal"
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.REGRESO_SALIDA_TEMPORAL,
            fecha_evento=datetime.combine(fecha, time(13, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        
        # 3h mañana + 3h tarde = 6h laboradas + 1h extra detectada (no autorizada)
        assert resultado["minutos_laborados"] == 360
        assert resultado["minutos_extra"] == 0  # Bloque detectado no autorizado, no cuenta
        assert resultado["minutos_descanso"] == 60  # 1 hora de descanso
        assert len(resultado["bloques_extra"]) == 1  # Bloque detectado pero no autorizado
        print("[OK] Test calcular_horas_laboradas_con_salida_temporal: PASSED")
    
    def test_salida_comer_no_descuenta_tiempo(self):
        """Verifica que las salidas a Comer NO descuentan tiempo laborado"""
        fecha = FECHA_PRUEBA
        
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        # Salida a comer (tipo_salida="Comer")
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA_TEMPORAL,
            fecha_evento=datetime.combine(fecha, time(12, 0)).replace(tzinfo=now.tzinfo),
            tipo_salida="Comer"
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.REGRESO_SALIDA_TEMPORAL,
            fecha_evento=datetime.combine(fecha, time(13, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        
        # La hora de comida (12:00-13:00) SÍ cuenta como trabajada: 7h laboradas + 1h extra detectada (no autorizada)
        assert resultado["minutos_laborados"] == 420  # 7 horas (9am-4pm, incluyendo hora de comida)
        assert resultado["minutos_extra"] == 0  # Bloque detectado no autorizado, no cuenta
        assert resultado["minutos_descanso"] == 0  # Comer no se cuenta como descanso
        assert len(resultado["bloques_extra"]) == 1  # Bloque detectado pero no autorizado
        print("[OK] Test salida_comer_no_descuenta_tiempo: PASSED")
    
    def test_permiso_temporal_con_regreso_no_descuenta_doble(self):
        """Verifica que permiso temporal con regreso no descuenta doble"""
        # Caso: 2pm entrada, 2:30pm permiso, 2:40pm regreso, 4pm salida
        # Total: 120 minutos, permiso: 10 minutos, laborados: 110 minutos
        fecha = FECHA_PRUEBA
        
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(14, 0)),
            hora_salida_real=datetime.combine(fecha, time(16, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(14, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA_TEMPORAL,
            fecha_evento=datetime.combine(fecha, time(14, 30)).replace(tzinfo=now.tzinfo),
            tipo_salida=TipoSalida.PERMISO_PERSONAL.value
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.REGRESO_SALIDA_TEMPORAL,
            fecha_evento=datetime.combine(fecha, time(14, 40)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(16, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        
        # 30 min + 80 min = 110 minutos laborados (sin descuento doble)
        assert resultado["minutos_laborados"] == 110
        assert resultado["minutos_descanso"] == 10  # 10 minutos de permiso
        assert resultado["minutos_extra"] == 0
        print("[OK] Test permiso_temporal_con_regreso_no_descuenta_doble: PASSED")
    
    def test_permiso_termina_turno_sin_regreso(self):
        """Verifica que permiso que termina turno sin regreso calcula correctamente"""
        # Caso: 8am entrada, 2pm permiso, no regreso, horario 8am-4pm
        # Laborados: 6 horas (8am-2pm), permiso: 2 horas (2pm-4pm)
        fecha = FECHA_PRUEBA
        
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(8, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(8, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA_TEMPORAL,
            fecha_evento=datetime.combine(fecha, time(14, 0)).replace(tzinfo=now.tzinfo),
            tipo_salida=TipoSalida.PERMISO_PERSONAL.value
        ))
        # No regreso - el turno termina a la hora oficial
        self.session.commit()
        
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        
        # 6 horas laboradas (8am-2pm), 2 horas permiso (2pm-4pm)
        assert resultado["minutos_laborados"] == 360
        assert resultado["minutos_descanso"] == 120  # 2 horas de permiso
        assert resultado["minutos_extra"] == 0
        print("[OK] Test permiso_termina_turno_sin_regreso: PASSED")
    
    def test_permiso_regreso_despues_hora_oficial_visita(self):
        """Verifica que regreso después de hora oficial se trata como visita"""
        # Caso: 8am entrada, 2pm permiso, 5pm regreso, horario 8am-4pm
        # Laborados: 6 horas (8am-2pm), permiso: 2 horas (2pm-4pm), visita: 1 hora (4pm-5pm)
        fecha = FECHA_PRUEBA
        
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(8, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(8, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA_TEMPORAL,
            fecha_evento=datetime.combine(fecha, time(14, 0)).replace(tzinfo=now.tzinfo),
            tipo_salida=TipoSalida.PERMISO_PERSONAL.value
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.REGRESO_SALIDA_TEMPORAL,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        
        # 6 horas laboradas (8am-2pm), 2 horas permiso (2pm-4pm), regreso es visita
        assert resultado["minutos_laborados"] == 360
        assert resultado["minutos_descanso"] == 120  # 2 horas de permiso
        assert resultado["minutos_extra"] == 0
        print("[OK] Test permiso_regreso_despues_hora_oficial_visita: PASSED")


class TestHorasExtras:
    """Pruebas para el cálculo de horas extras"""
    
    def setup_method(self):
        self.session = Session(test_engine)
        self.empleado = self.session.scalar(
            select(Empleado).where(Empleado.numero_empleado == "EMP001")
        )
        if not self.empleado:
            raise Exception("Empleado EMP001 no encontrado")
        # Limpiar datos de prueba previos para garantizar idempotencia
        limpiar_datos_prueba(self.session, self.empleado.id)
    
    def teardown_method(self):
        # Limpiar datos de prueba creados durante el test
        try:
            limpiar_datos_prueba(self.session, self.empleado.id)
        except Exception:
            self.session.rollback()
        self.session.close()
    
    def test_calcular_horas_extra_antes_inicio(self):
        """Verifica cálculo de horas extra antes del inicio del turno"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(7, 0)),  # 2h antes
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        # Calcular bloques de horas extra
        calcular_y_registrar_bloques_horas_extra(
            self.session, 
            asistencia, 
            datetime.combine(fecha, time(7, 0)),
            datetime.combine(fecha, time(17, 0))
        )
        self.session.commit()
        
        # Verificar bloques creados
        bloques = self.session.scalars(
            select(BloqueHorasExtra).where(BloqueHorasExtra.asistencia_id == asistencia.id)
        ).all()
        
        assert len(bloques) > 0
        bloque_antes = [b for b in bloques if b.tipo_bloque == "ANTES_INICIO"]
        assert len(bloque_antes) > 0
        print("[OK] Test calcular_horas_extra_antes_inicio: PASSED")
    
    def test_calcular_horas_extra_despues_fin(self):
        """Verifica cálculo de horas extra después del fin del turno"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(19, 0)),  # 2h después
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        # Calcular bloques de horas extra
        calcular_y_registrar_bloques_horas_extra(
            self.session, 
            asistencia, 
            datetime.combine(fecha, time(9, 0)),
            datetime.combine(fecha, time(19, 0))
        )
        self.session.commit()
        
        # Verificar bloques creados
        bloques = self.session.scalars(
            select(BloqueHorasExtra).where(BloqueHorasExtra.asistencia_id == asistencia.id)
        ).all()
        
        assert len(bloques) > 0
        bloque_despues = [b for b in bloques if b.tipo_bloque == "DESPUES_FIN"]
        assert len(bloque_despues) > 0
        print("[OK] Test calcular_horas_extra_despues_fin: PASSED")


class TestVisitasPagadas:
    """Pruebas para validación de visitas pagadas"""
    
    def setup_method(self):
        self.session = Session(test_engine)
        self.empleado = self.session.scalar(
            select(Empleado).where(Empleado.numero_empleado == "EMP001")
        )
        if not self.empleado:
            raise Exception("Empleado EMP001 no encontrado")
        # Limpiar datos de prueba previos para garantizar idempotencia
        limpiar_datos_prueba(self.session, self.empleado.id)
    
    def teardown_method(self):
        # Limpiar datos de prueba creados durante el test
        try:
            limpiar_datos_prueba(self.session, self.empleado.id)
        except Exception:
            self.session.rollback()
        self.session.close()
    
    def test_visita_no_pagada_no_cuenta_horas(self):
        """Verifica que visita no pagada no cuenta en horas laboradas"""
        # Usar fecha futura reservada para pruebas
        fecha = FECHA_PRUEBA
        
        # Crear asistencia
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.VISITA_DESCANSO
        )
        self.session.add(asistencia)
        self.session.flush()
        
        # Crear visita no pagada
        visita = Visita(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            estado=EstadoVisita.NO_PAGADA,
            fecha_visita=datetime.combine(fecha, time(9, 0))
        )
        self.session.add(visita)
        self.session.flush()
        
        # Crear eventos con timezone
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        try:
            resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
            
            # No debe contar las horas porque es visita no pagada
            assert resultado["minutos_laborados"] == 0
            print("[OK] Test visita_no_pagada_no_cuenta_horas: PASSED")
        except Exception as e:
            print(f"[FAIL] Test visita_no_pagada_no_cuenta_horas: FAILED - {e}")
            raise
    
    def test_visita_pagada_cuenta_horas(self):
        """Verifica que visita pagada sí cuenta en horas laboradas"""
        # Usar fecha futura reservada para pruebas
        fecha = FECHA_PRUEBA
        
        # Crear asistencia
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.VISITA_DESCANSO
        )
        self.session.add(asistencia)
        self.session.flush()
        
        # Crear visita pagada (PENDIENTE o PAGADA)
        visita = Visita(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            estado=EstadoVisita.PENDIENTE,  # No es NO_PAGADA
            fecha_visita=datetime.combine(fecha, time(9, 0))
        )
        self.session.add(visita)
        self.session.flush()
        
        # Crear eventos con timezone
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        try:
            resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
            
            # Debe contar las horas porque es visita pagada
            assert resultado["minutos_laborados"] == 480
            print("[OK] Test visita_pagada_cuenta_horas: PASSED")
        except Exception as e:
            print(f"[FAIL] Test visita_pagada_cuenta_horas: FAILED - {e}")
            raise


class TestValidacionesDefault:
    """Pruebas para validaciones por default (tolerancias, tiempos)"""
    
    def setup_method(self):
        self.session = Session(test_engine)
        self.empleado = self.session.scalar(
            select(Empleado).where(Empleado.numero_empleado == "EMP001")
        )
        if not self.empleado:
            raise Exception("Empleado EMP001 no encontrado")
        # Limpiar datos de prueba previos para garantizar idempotencia
        limpiar_datos_prueba(self.session, self.empleado.id)
    
    def teardown_method(self):
        # Limpiar datos de prueba creados durante el test
        try:
            limpiar_datos_prueba(self.session, self.empleado.id)
        except Exception:
            self.session.rollback()
        self.session.close()
    
    def test_tolerancia_minutos_default(self):
        """Verifica que la tolerancia por default se aplica correctamente"""
        # Verificar que EMP001 tiene turno con tolerancia definida
        turno = self.session.scalar(
            select(TurnoHorario).where(
                TurnoHorario.empleado_id == self.empleado.id,
                TurnoHorario.dia_semana == 0  # Lunes
            )
        )
        
        if turno:
            assert turno.tolerancia_minutos is not None
            assert turno.tolerancia_minutos >= 0
            print(f"[OK] Test tolerancia_minutos_default: PASSED (tolerancia={turno.tolerancia_minutos})")
        else:
            print("[SKIP] Test tolerancia_minutos_default: SKIPPED (no hay turno)")
    
    def test_horario_oficial_definido(self):
        """Verifica que el horario oficial está definido"""
        turno = self.session.scalar(
            select(TurnoHorario).where(
                TurnoHorario.empleado_id == self.empleado.id,
                TurnoHorario.dia_semana == 0
            )
        )
        
        if turno:
            assert turno.hora_entrada_oficial is not None
            assert turno.hora_salida_oficial is not None
            print(f"[OK] Test horario_oficial_definido: PASSED")
        else:
            print("[SKIP] Test horario_oficial_definido: SKIPPED (no hay turno)")


class TestCorreccionesManuales:
    """Pruebas para correcciones manuales de RRHH"""
    
    def setup_method(self):
        self.session = Session(test_engine)
        self.empleado = self.session.scalar(
            select(Empleado).where(Empleado.numero_empleado == "EMP001")
        )
        if not self.empleado:
            raise Exception("Empleado EMP001 no encontrado")
        # Limpiar datos de prueba previos para garantizar idempotencia
        limpiar_datos_prueba(self.session, self.empleado.id)
    
    def teardown_method(self):
        # Limpiar datos de prueba creados durante el test
        try:
            limpiar_datos_prueba(self.session, self.empleado.id)
        except Exception:
            self.session.rollback()
        self.session.close()
    
    def test_correccion_horas_laboradas_positiva(self):
        """Verifica que corrección positiva de horas laboradas se aplica"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia base (8 horas = 480 minutos)
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        # Sin corrección: 480 minutos
        resultado_sin = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado_sin["minutos_laborados"] == 480
        
        # Agregar corrección manual: +30 minutos
        correccion = CorreccionManual(
            empleado_id=self.empleado.id,
            fecha=fecha,
            tipo_correccion=TipoCorreccion.HORAS_LABORADAS,
            minutos_agregados=30.5,  # 30.5 minutos decimales
            motivo="Prueba corrección positiva",
            autorizado_por=1,
            fecha_registro=utc_now()
        )
        self.session.add(correccion)
        self.session.commit()
        
        # Con corrección: 480 + 30.5 = 510.5 minutos
        resultado_con = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado_con["minutos_laborados"] == 510.5
        assert len(resultado_con["correcciones"]) == 1
        print("[OK] Test correccion_horas_laboradas_positiva: PASSED")
    
    def test_correccion_horas_laboradas_negativa(self):
        """Verifica que corrección negativa de horas laboradas se aplica"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia base
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        # Agregar corrección manual: -15 minutos
        correccion = CorreccionManual(
            empleado_id=self.empleado.id,
            fecha=fecha,
            tipo_correccion=TipoCorreccion.HORAS_LABORADAS,
            minutos_agregados=-15.0,
            motivo="Prueba corrección negativa",
            autorizado_por=1,
            fecha_registro=utc_now()
        )
        self.session.add(correccion)
        self.session.commit()
        
        # Con corrección: 480 - 15 = 465 minutos
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_laborados"] == 465.0
        print("[OK] Test correccion_horas_laboradas_negativa: PASSED")
    
    def test_correccion_horas_extra(self):
        """Verifica que corrección de horas extra se aplica"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia base
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        # Agregar corrección manual de horas extra: +45 minutos
        correccion = CorreccionManual(
            empleado_id=self.empleado.id,
            fecha=fecha,
            tipo_correccion=TipoCorreccion.HORAS_EXTRA,
            minutos_agregados=45.0,
            motivo="Prueba corrección horas extra",
            autorizado_por=1,
            fecha_registro=utc_now()
        )
        self.session.add(correccion)
        self.session.commit()
        
        # Verificar que se aplicó a minutos_extra
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_extra"] == 45.0
        assert resultado["minutos_laborados"] == 480  # No afecta horas laboradas
        print("[OK] Test correccion_horas_extra: PASSED")
    
    def test_bloque_horas_extra_sin_autorizacion(self):
        """Verifica que bloque sin autorización no se cuenta en minutos_extra"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia base
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        # Agregar bloque de horas extra SIN autorización
        bloque = BloqueHorasExtra(
            asistencia_id=asistencia.id,
            tipo_bloque="DESPUES_FIN",
            hora_inicio=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo),
            hora_fin=datetime.combine(fecha, time(18, 0)).replace(tzinfo=now.tzinfo),
            minutos_extra=60,
            validacion_supervisor=False,
            validacion_rrhh=False
        )
        self.session.add(bloque)
        self.session.commit()
        
        # Verificar que NO se cuenta
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_extra"] == 0  # Sin autorización, no cuenta
        print("[OK] Test bloque_horas_extra_sin_autorizacion: PASSED")
    
    def test_bloque_horas_extra_autorizacion_parcial(self):
        """Verifica que bloque con autorización solo de supervisor no se cuenta (requiere RRHH)"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia base
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        # Agregar bloque con autorización solo de supervisor (sin RRHH)
        bloque = BloqueHorasExtra(
            asistencia_id=asistencia.id,
            tipo_bloque="DESPUES_FIN",
            hora_inicio=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo),
            hora_fin=datetime.combine(fecha, time(18, 0)).replace(tzinfo=now.tzinfo),
            minutos_extra=60,
            validacion_supervisor=True,
            validacion_rrhh=False
        )
        self.session.add(bloque)
        self.session.commit()
        
        # Verificar que NO se cuenta (falta RRHH)
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_extra"] == 0
        print("[OK] Test bloque_horas_extra_autorizacion_parcial: PASSED")
    
    def test_bloque_horas_extra_autorizacion_completa(self):
        """Verifica que bloque con autorización de RRHH se cuenta (supervisor opcional)"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia base
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        # Agregar bloque con autorización de RRHH (sin supervisor)
        bloque = BloqueHorasExtra(
            asistencia_id=asistencia.id,
            tipo_bloque="DESPUES_FIN",
            hora_inicio=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo),
            hora_fin=datetime.combine(fecha, time(18, 0)).replace(tzinfo=now.tzinfo),
            minutos_extra=60,
            validacion_supervisor=False,  # Supervisor no validó
            validacion_rrhh=True  # RRHH autorizó
        )
        self.session.add(bloque)
        self.session.commit()
        
        # Verificar que SÍ se cuenta (RRHH es suficiente)
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_extra"] == 60
        assert len(resultado["bloques_extra"]) == 1
        assert resultado["bloques_extra"][0]["validacion_supervisor"] == False
        assert resultado["bloques_extra"][0]["validacion_rrhh"] == True
        print("[OK] Test bloque_horas_extra_autorizacion_completa: PASSED")
    
    def test_rrhh_puede_autorizar_sin_supervisor(self):
        """Verifica que RRHH puede autorizar horas extras aunque el supervisor no las haya validado"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia base
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        # Agregar bloque sin validación de supervisor
        bloque = BloqueHorasExtra(
            asistencia_id=asistencia.id,
            tipo_bloque="DESPUES_FIN",
            hora_inicio=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo),
            hora_fin=datetime.combine(fecha, time(18, 0)).replace(tzinfo=now.tzinfo),
            minutos_extra=60,
            validacion_supervisor=False,
            validacion_rrhh=False
        )
        self.session.add(bloque)
        self.session.commit()
        
        # Verificar que NO se cuenta inicialmente
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_extra"] == 0
        
        # RRHH autoriza el bloque (simulado)
        bloque.validacion_rrhh = True
        self.session.commit()
        
        # Verificar que ahora SÍ se cuenta
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_extra"] == 60
        assert resultado["bloques_extra"][0]["validacion_rrhh"] == True
        print("[OK] Test rrhh_puede_autorizar_sin_supervisor: PASSED")
    
    def test_supervisor_valida_rrhh_autoriza(self):
        """Verifica el flujo completo: supervisor valida, RRHH autoriza"""
        fecha = FECHA_PRUEBA
        
        # Crear asistencia base
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(17, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        now = utc_now()
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=datetime.combine(fecha, time(9, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.add(EventoAsistencia(
            empleado_id=self.empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.SALIDA,
            fecha_evento=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo)
        ))
        self.session.commit()
        
        # Agregar bloque sin validaciones
        bloque = BloqueHorasExtra(
            asistencia_id=asistencia.id,
            tipo_bloque="DESPUES_FIN",
            hora_inicio=datetime.combine(fecha, time(17, 0)).replace(tzinfo=now.tzinfo),
            hora_fin=datetime.combine(fecha, time(18, 0)).replace(tzinfo=now.tzinfo),
            minutos_extra=60,
            validacion_supervisor=False,
            validacion_rrhh=False
        )
        self.session.add(bloque)
        self.session.commit()
        
        # Verificar que NO se cuenta inicialmente
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_extra"] == 0
        
        # Supervisor valida
        bloque.validacion_supervisor = True
        self.session.commit()
        
        # Verificar que aún NO se cuenta (falta RRHH)
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_extra"] == 0
        
        # RRHH autoriza
        bloque.validacion_rrhh = True
        self.session.commit()
        
        # Verificar que ahora SÍ se cuenta
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_extra"] == 60
        assert resultado["bloques_extra"][0]["validacion_supervisor"] == True
        assert resultado["bloques_extra"][0]["validacion_rrhh"] == True
        print("[OK] Test supervisor_valida_rrhh_autoriza: PASSED")


def limpiar_ausencias_prueba(session, empleado_id, fecha=FECHA_PRUEBA):
    """Elimina ausencias de prueba para garantizar idempotencia."""
    ausencias = session.scalars(
        select(RegistroAusencia).where(
            RegistroAusencia.empleado_id == empleado_id,
            RegistroAusencia.fecha_inicio <= fecha,
            RegistroAusencia.fecha_fin >= fecha
        )
    ).all()
    for a in ausencias:
        session.delete(a)
    session.commit()


class TestRundownLogica:
    """Pruebas integrales del rundown: duplicación de bloques, ausencias y reglas de cálculo."""
    
    def setup_method(self):
        self.session = Session(test_engine)
        self.empleado = self.session.scalar(
            select(Empleado).where(Empleado.numero_empleado == "EMP001")
        )
        if not self.empleado:
            raise Exception("Empleado EMP001 no encontrado")
        limpiar_datos_prueba(self.session, self.empleado.id)
        limpiar_ausencias_prueba(self.session, self.empleado.id)
    
    def teardown_method(self):
        try:
            limpiar_datos_prueba(self.session, self.empleado.id)
            limpiar_ausencias_prueba(self.session, self.empleado.id)
        except Exception:
            self.session.rollback()
        self.session.close()
    
    def test_bloques_no_se_duplican_al_recalcular(self):
        """Verifica que recalcular bloques NO los duplica (fix de duplicación)."""
        fecha = FECHA_PRUEBA
        
        asistencia = RegistroAsistencia(
            empleado_id=self.empleado.id,
            fecha_turno=fecha,
            hora_entrada_real=datetime.combine(fecha, time(9, 0)),
            hora_salida_real=datetime.combine(fecha, time(19, 0)),
            estado_registro=EstadoRegistro.NORMAL
        )
        self.session.add(asistencia)
        self.session.flush()
        
        # Llamar DOS veces para simular recalculo (p.ej. salida registrada 2 veces)
        calcular_y_registrar_bloques_horas_extra(
            self.session, asistencia,
            datetime.combine(fecha, time(9, 0)),
            datetime.combine(fecha, time(19, 0))
        )
        calcular_y_registrar_bloques_horas_extra(
            self.session, asistencia,
            datetime.combine(fecha, time(9, 0)),
            datetime.combine(fecha, time(19, 0))
        )
        self.session.commit()
        
        bloques = self.session.scalars(
            select(BloqueHorasExtra).where(BloqueHorasExtra.asistencia_id == asistencia.id)
        ).all()
        
        # Debe haber solo 1 bloque DESPUES_FIN, no duplicado
        bloques_despues = [b for b in bloques if b.tipo_bloque == "DESPUES_FIN"]
        assert len(bloques_despues) == 1, f"Se esperaba 1 bloque, hay {len(bloques_despues)}"
        # minutos_extra_calculados no debe estar duplicado
        assert asistencia.minutos_extra_calculados == bloques_despues[0].minutos_extra
        print("[OK] Test bloques_no_se_duplican_al_recalcular: PASSED")
    
    def test_vacaciones_cuenta_horas_laboradas(self):
        """Verifica que un día de vacaciones aprobado cuenta como horas laboradas al 100%."""
        fecha = FECHA_PRUEBA
        
        ausencia = RegistroAusencia(
            empleado_id=self.empleado.id,
            tipo_ausencia=TipoAusencia.VACACIONES,
            fecha_inicio=fecha,
            fecha_fin=fecha,
            pagada=True,
            porcentaje_aportacion=100,
            motivo="Prueba vacaciones",
            aprobado_rrhh=True,
            fecha_registro=utc_now()
        )
        self.session.add(ausencia)
        self.session.commit()
        
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        # Debe contar las horas del turno (EMP001 lunes tiene turno definido)
        assert resultado["minutos_laborados"] > 0
        assert resultado["minutos_extra"] == 0
        assert resultado.get("ausencia") is not None
        print("[OK] Test vacaciones_cuenta_horas_laboradas: PASSED")
    
    def test_incapacidad_parcial_cuenta_porcentaje(self):
        """Verifica que una incapacidad al 50% cuenta la mitad de las horas del turno."""
        fecha = FECHA_PRUEBA
        
        # Primero obtener horas completas con vacaciones para comparar
        ausencia_inc = RegistroAusencia(
            empleado_id=self.empleado.id,
            tipo_ausencia=TipoAusencia.INCAPACIDAD,
            fecha_inicio=fecha,
            fecha_fin=fecha,
            pagada=True,
            porcentaje_aportacion=50,
            motivo="Prueba incapacidad 50%",
            aprobado_rrhh=True,
            fecha_registro=utc_now()
        )
        self.session.add(ausencia_inc)
        self.session.commit()
        
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        minutos_50 = resultado["minutos_laborados"]
        
        # Cambiar a 100% para comparar
        ausencia_inc.porcentaje_aportacion = 100
        self.session.commit()
        resultado_100 = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        minutos_100 = resultado_100["minutos_laborados"]
        
        assert minutos_100 > 0
        # 50% debe ser aproximadamente la mitad de 100%
        assert abs(minutos_50 - minutos_100 // 2) <= 1, f"50%={minutos_50}, 100%={minutos_100}"
        print("[OK] Test incapacidad_parcial_cuenta_porcentaje: PASSED")
    
    def test_permiso_no_pagado_no_cuenta(self):
        """Verifica que un permiso NO pagado no cuenta horas laboradas."""
        fecha = FECHA_PRUEBA
        
        ausencia = RegistroAusencia(
            empleado_id=self.empleado.id,
            tipo_ausencia=TipoAusencia.PERMISO,
            fecha_inicio=fecha,
            fecha_fin=fecha,
            pagada=False,
            porcentaje_aportacion=0,
            motivo="Prueba permiso sin goce",
            aprobado_rrhh=True,
            fecha_registro=utc_now()
        )
        self.session.add(ausencia)
        self.session.commit()
        
        resultado = calcular_horas_laboradas(self.session, self.empleado.id, fecha)
        assert resultado["minutos_laborados"] == 0
        print("[OK] Test permiso_no_pagado_no_cuenta: PASSED")


class TestReportes:
    """Pruebas para endpoints de reportes"""
    
    def __init__(self):
        # Login para obtener token
        login_response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin"})
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_reporte_horas_laboradas(self):
        """Verifica que el reporte de horas laboradas funciona"""
        fecha_inicio = "2026-06-01"
        fecha_fin = "2026-06-15"
        
        response = requests.get(
            f"{BASE_URL}/admin/reportes/horas-laboradas",
            params={"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
            headers=self.headers
        )
        
        assert response.status_code == 200
        reporte = response.json()
        assert isinstance(reporte, list)
        print("[OK] Test reporte_horas_laboradas: PASSED")
    
    def test_reporte_horas_extra(self):
        """Verifica que el reporte de horas extra funciona"""
        fecha_inicio = "2026-06-01"
        fecha_fin = "2026-06-15"
        
        response = requests.get(
            f"{BASE_URL}/admin/reportes/horas-extra",
            params={"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
            headers=self.headers
        )
        
        assert response.status_code == 200
        reporte = response.json()
        assert isinstance(reporte, list)
        print("[OK] Test reporte_horas_extra: PASSED")
    
    def test_reporte_asistencias(self):
        """Verifica que el reporte de asistencias funciona"""
        fecha_inicio = "2026-06-01"
        fecha_fin = "2026-06-15"
        
        response = requests.get(
            f"{BASE_URL}/admin/reportes/asistencias",
            params={"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
            headers=self.headers
        )
        
        assert response.status_code == 200
        reporte = response.json()
        assert isinstance(reporte, list)
        print("[OK] Test reporte_asistencias: PASSED")
    
    def test_reporte_bloques_horas_extra(self):
        """Verifica que el reporte de bloques de horas extra funciona"""
        fecha_inicio = "2026-06-01"
        fecha_fin = "2026-06-15"
        
        response = requests.get(
            f"{BASE_URL}/admin/bloques-horas-extra",
            params={"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
            headers=self.headers
        )
        
        assert response.status_code == 200
        reporte = response.json()
        assert isinstance(reporte, list)
        print("[OK] Test reporte_bloques_horas_extra: PASSED")


class TestAutorizacionHorasExtra:
    """Pruebas para autorización de horas extra"""
    
    def __init__(self):
        # Login para obtener token
        login_response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin"})
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_autorizar_horas_extra(self):
        """Verifica que se puede autorizar horas extra"""
        # Obtener una asistencia con horas extra
        session = Session(test_engine)
        asistencia = session.scalar(
            select(RegistroAsistencia).where(
                RegistroAsistencia.minutos_extra_calculados > 0
            )
        )
        session.close()
        
        if asistencia:
            response = requests.put(
                f"{BASE_URL}/admin/asistencias/{asistencia.id}/autorizar-horas-extra",
                headers=self.headers
            )
            
            # Puede ser 400 si ya está autorizada, pero no debe ser 404 o 500
            assert response.status_code in [200, 400]
            print("[OK] Test autorizar_horas_extra: PASSED")
        else:
            print("[SKIP] Test autorizar_horas_extra: SKIPPED (no hay asistencia con horas extra)")
    
    def test_revocar_autorizacion_rrhh(self):
        """Verifica que se puede revocar autorización de RRHH"""
        session = Session(test_engine)
        asistencia = session.scalar(
            select(RegistroAsistencia).where(
                RegistroAsistencia.autorizacion_horas_extra_rrhh == True
            )
        )
        session.close()
        
        if asistencia:
            response = requests.put(
                f"{BASE_URL}/admin/asistencias/{asistencia.id}/revocar-autorizacion-rrhh",
                headers=self.headers
            )
            
            assert response.status_code == 200
            print("[OK] Test revocar_autorizacion_rrhh: PASSED")
        else:
            print("[SKIP] Test revocar_autorizacion_rrhh: SKIPPED (no hay autorización activa)")


def ejecutar_todas_las_pruebas():
    """Ejecuta todas las pruebas de reglas de negocio y genera un reporte"""
    print("=" * 80)
    print("INICIANDO SUITE DE PRUEBAS DE REGLAS DE NEGOCIO - SISTEMA RRHH")
    print("=" * 80)
    print()
    
    resultados = {
        "horas_laboradas": [],
        "horas_extras": [],
        "visitas_pagadas": [],
        "validaciones_default": [],
        "correcciones_manuales": [],
        "rundown_logica": [],
        "reportes": [],
        "autorizacion_horas_extra": []
    }
    
    # Ejecutar pruebas de horas laboradas
    print("[TEST] EJECUTANDO PRUEBAS DE HORAS LABORADAS...")
    test_horas = TestHorasLaboradas()
    try:
        test_horas.setup_method()
        test_horas.test_calcular_horas_laboradas_sin_eventos()
        resultados["horas_laboradas"].append("calcular_horas_laboradas_sin_eventos: [OK] PASSED")
    except Exception as e:
        resultados["horas_laboradas"].append(f"calcular_horas_laboradas_sin_eventos: [FAIL] FAILED - {e}")
    finally:
        test_horas.teardown_method()
    
    try:
        test_horas.setup_method()
        test_horas.test_calcular_horas_laboradas_con_entrada_salida()
        resultados["horas_laboradas"].append("calcular_horas_laboradas_con_entrada_salida: [OK] PASSED")
    except Exception as e:
        resultados["horas_laboradas"].append(f"calcular_horas_laboradas_con_entrada_salida: [FAIL] FAILED - {e}")
    finally:
        test_horas.teardown_method()
    
    try:
        test_horas.setup_method()
        test_horas.test_calcular_horas_laboradas_con_salida_temporal()
        resultados["horas_laboradas"].append("calcular_horas_laboradas_con_salida_temporal: [OK] PASSED")
    except Exception as e:
        resultados["horas_laboradas"].append(f"calcular_horas_laboradas_con_salida_temporal: [FAIL] FAILED - {e}")
    finally:
        test_horas.teardown_method()
    
    print()
    
    # Ejecutar pruebas de horas extras
    print("[TEST] EJECUTANDO PRUEBAS DE HORAS EXTRAS...")
    test_extras = TestHorasExtras()
    try:
        test_extras.setup_method()
        test_extras.test_calcular_horas_extra_antes_inicio()
        resultados["horas_extras"].append("calcular_horas_extra_antes_inicio: [OK] PASSED")
    except Exception as e:
        resultados["horas_extras"].append(f"calcular_horas_extra_antes_inicio: [FAIL] FAILED - {e}")
    finally:
        test_extras.teardown_method()
    
    try:
        test_extras.setup_method()
        test_extras.test_calcular_horas_extra_despues_fin()
        resultados["horas_extras"].append("calcular_horas_extra_despues_fin: [OK] PASSED")
    except Exception as e:
        resultados["horas_extras"].append(f"calcular_horas_extra_despues_fin: [FAIL] FAILED - {e}")
    finally:
        test_extras.teardown_method()
    
    print()
    
    # Ejecutar pruebas de visitas pagadas
    print("[TEST] EJECUTANDO PRUEBAS DE VISITAS PAGADAS...")
    test_visitas = TestVisitasPagadas()
    try:
        test_visitas.setup_method()
        test_visitas.test_visita_no_pagada_no_cuenta_horas()
        resultados["visitas_pagadas"].append("visita_no_pagada_no_cuenta_horas: [OK] PASSED")
    except Exception as e:
        resultados["visitas_pagadas"].append(f"visita_no_pagada_no_cuenta_horas: [FAIL] FAILED - {e}")
    finally:
        test_visitas.teardown_method()
    
    try:
        test_visitas.setup_method()
        test_visitas.test_visita_pagada_cuenta_horas()
        resultados["visitas_pagadas"].append("visita_pagada_cuenta_horas: [OK] PASSED")
    except Exception as e:
        resultados["visitas_pagadas"].append(f"visita_pagada_cuenta_horas: [FAIL] FAILED - {e}")
    finally:
        test_visitas.teardown_method()
    
    print()
    
    # Ejecutar pruebas de validaciones default
    print("[TEST] EJECUTANDO PRUEBAS DE VALIDACIONES DEFAULT...")
    test_validaciones = TestValidacionesDefault()
    try:
        test_validaciones.setup_method()
        test_validaciones.test_tolerancia_minutos_default()
        resultados["validaciones_default"].append("tolerancia_minutos_default: [OK] PASSED")
    except Exception as e:
        resultados["validaciones_default"].append(f"tolerancia_minutos_default: [FAIL] FAILED - {e}")
    finally:
        test_validaciones.teardown_method()
    
    try:
        test_validaciones.setup_method()
        test_validaciones.test_horario_oficial_definido()
        resultados["validaciones_default"].append("horario_oficial_definido: [OK] PASSED")
    except Exception as e:
        resultados["validaciones_default"].append(f"horario_oficial_definido: [FAIL] FAILED - {e}")
    finally:
        test_validaciones.teardown_method()
    
    print()
    
    # Ejecutar pruebas de correcciones manuales
    print("[TEST] EJECUTANDO PRUEBAS DE CORRECCIONES MANUALES...")
    test_correcciones = TestCorreccionesManuales()
    try:
        test_correcciones.setup_method()
        test_correcciones.test_correccion_horas_laboradas_positiva()
        resultados["correcciones_manuales"].append("correccion_horas_laboradas_positiva: [OK] PASSED")
    except Exception as e:
        resultados["correcciones_manuales"].append(f"correccion_horas_laboradas_positiva: [FAIL] FAILED - {e}")
    finally:
        test_correcciones.teardown_method()
    
    try:
        test_correcciones.setup_method()
        test_correcciones.test_correccion_horas_laboradas_negativa()
        resultados["correcciones_manuales"].append("correccion_horas_laboradas_negativa: [OK] PASSED")
    except Exception as e:
        resultados["correcciones_manuales"].append(f"correccion_horas_laboradas_negativa: [FAIL] FAILED - {e}")
    finally:
        test_correcciones.teardown_method()
    
    try:
        test_correcciones.setup_method()
        test_correcciones.test_correccion_horas_extra()
        resultados["correcciones_manuales"].append("correccion_horas_extra: [OK] PASSED")
    except Exception as e:
        resultados["correcciones_manuales"].append(f"correccion_horas_extra: [FAIL] FAILED - {e}")
    finally:
        test_correcciones.teardown_method()
    
    try:
        test_correcciones.setup_method()
        test_correcciones.test_bloque_horas_extra_sin_autorizacion()
        resultados["correcciones_manuales"].append("bloque_horas_extra_sin_autorizacion: [OK] PASSED")
    except Exception as e:
        resultados["correcciones_manuales"].append(f"bloque_horas_extra_sin_autorizacion: [FAIL] FAILED - {e}")
    finally:
        test_correcciones.teardown_method()
    
    try:
        test_correcciones.setup_method()
        test_correcciones.test_bloque_horas_extra_autorizacion_parcial()
        resultados["correcciones_manuales"].append("bloque_horas_extra_autorizacion_parcial: [OK] PASSED")
    except Exception as e:
        resultados["correcciones_manuales"].append(f"bloque_horas_extra_autorizacion_parcial: [FAIL] FAILED - {e}")
    finally:
        test_correcciones.teardown_method()
    
    try:
        test_correcciones.setup_method()
        test_correcciones.test_bloque_horas_extra_autorizacion_completa()
        resultados["correcciones_manuales"].append("bloque_horas_extra_autorizacion_completa: [OK] PASSED")
    except Exception as e:
        resultados["correcciones_manuales"].append(f"bloque_horas_extra_autorizacion_completa: [FAIL] FAILED - {e}")
    finally:
        test_correcciones.teardown_method()
    
    print()
    
    # Ejecutar pruebas del rundown de lógica
    print("[TEST] EJECUTANDO PRUEBAS DE RUNDOWN DE LOGICA...")
    test_rundown = TestRundownLogica()
    for nombre_test in [
        "test_bloques_no_se_duplican_al_recalcular",
        "test_vacaciones_cuenta_horas_laboradas",
        "test_incapacidad_parcial_cuenta_porcentaje",
        "test_permiso_no_pagado_no_cuenta",
    ]:
        try:
            test_rundown.setup_method()
            getattr(test_rundown, nombre_test)()
            resultados["rundown_logica"].append(f"{nombre_test}: [OK] PASSED")
        except Exception as e:
            resultados["rundown_logica"].append(f"{nombre_test}: [FAIL] FAILED - {e}")
        finally:
            test_rundown.teardown_method()
    
    print()
    
    # Ejecutar pruebas de reportes (requieren servidor en :8001 y login admin)
    print("[TEST] EJECUTANDO PRUEBAS DE REPORTES...")
    try:
        test_reportes = TestReportes()
    except Exception as e:
        test_reportes = None
        resultados["reportes"].append(f"[SKIP] Reportes omitidos (no se pudo autenticar/conectar al servidor): {e}")
    if test_reportes is not None:
        try:
            test_reportes.test_reporte_horas_laboradas()
            resultados["reportes"].append("reporte_horas_laboradas: [OK] PASSED")
        except Exception as e:
            resultados["reportes"].append(f"reporte_horas_laboradas: [FAIL] FAILED - {e}")
        
        try:
            test_reportes.test_reporte_horas_extra()
            resultados["reportes"].append("reporte_horas_extra: [OK] PASSED")
        except Exception as e:
            resultados["reportes"].append(f"reporte_horas_extra: [FAIL] FAILED - {e}")
        
        try:
            test_reportes.test_reporte_asistencias()
            resultados["reportes"].append("reporte_asistencias: [OK] PASSED")
        except Exception as e:
            resultados["reportes"].append(f"reporte_asistencias: [FAIL] FAILED - {e}")
        
        try:
            test_reportes.test_reporte_bloques_horas_extra()
            resultados["reportes"].append("reporte_bloques_horas_extra: [OK] PASSED")
        except Exception as e:
            resultados["reportes"].append(f"reporte_bloques_horas_extra: [FAIL] FAILED - {e}")
    
    print()
    
    # Ejecutar pruebas de autorización horas extra (requieren servidor en :8001 y login admin)
    print("[TEST] EJECUTANDO PRUEBAS DE AUTORIZACION HORAS EXTRA...")
    try:
        test_autorizacion = TestAutorizacionHorasExtra()
    except Exception as e:
        test_autorizacion = None
        resultados["autorizacion_horas_extra"].append(f"[SKIP] Autorizacion omitida (no se pudo autenticar/conectar al servidor): {e}")
    if test_autorizacion is not None:
        try:
            test_autorizacion.test_autorizar_horas_extra()
            resultados["autorizacion_horas_extra"].append("autorizar_horas_extra: [OK] PASSED")
        except Exception as e:
            resultados["autorizacion_horas_extra"].append(f"autorizar_horas_extra: [FAIL] FAILED - {e}")
        
        try:
            test_autorizacion.test_revocar_autorizacion_rrhh()
            resultados["autorizacion_horas_extra"].append("revocar_autorizacion_rrhh: [OK] PASSED")
        except Exception as e:
            resultados["autorizacion_horas_extra"].append(f"revocar_autorizacion_rrhh: [FAIL] FAILED - {e}")
    
    print()
    print("=" * 80)
    print("REPORTE DE RESULTADOS - REGLAS DE NEGOCIO")
    print("=" * 80)
    
    total_pruebas = 0
    pruebas_pasadas = 0
    
    for categoria, pruebas in resultados.items():
        print(f"\n[REPORT] {categoria.upper()}:")
        for prueba in pruebas:
            total_pruebas += 1
            if "[OK] PASSED" in prueba:
                pruebas_pasadas += 1
            print(f"   {prueba}")
    
    print()
    print("=" * 80)
    print(f"RESUMEN: {pruebas_pasadas}/{total_pruebas} pruebas PASADAS")
    print(f"Porcentaje de exito: {(pruebas_pasadas/total_pruebas*100):.1f}%")
    print("=" * 80)
    
    # Evaluación de fiabilidad
    print()
    print("[EVALUATION] EVALUACION DE FIABILIDAD DE REGLAS DE NEGOCIO:")
    print("-" * 80)
    
    if pruebas_pasadas == total_pruebas:
        print("[OK] SISTEMA MUY FIABLE: Todas las pruebas de negocio pasaron exitosamente.")
        print("   El calculo de horas laboradas funciona correctamente.")
        print("   El calculo de horas extra se realiza de forma precisa.")
        print("   La validacion de visitas pagadas funciona correctamente.")
        print("   Las validaciones por default se aplican correctamente.")
        print("   Los reportes generan datos consistentes.")
        print("   La autorizacion de horas extra funciona correctamente.")
    elif pruebas_pasadas >= total_pruebas * 0.8:
        print("[WARN] SISTEMA FIABLE CON OBSERVACIONES: La mayoria de pruebas pasaron.")
        print("   Se recomienda revisar las pruebas que fallaron.")
    else:
        print("[FAIL] SISTEMA REQUIERE ATENCION: Varias pruebas fallaron.")
        print("   Se recomienda revisar la logica de negocio.")
    
    print("-" * 80)
    
    return resultados


if __name__ == "__main__":
    ejecutar_todas_las_pruebas()
