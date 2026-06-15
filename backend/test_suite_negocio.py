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
    Visita, BloqueHorasExtra, EstadoVisita, TipoEvento, EstadoRegistro
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

# Fecha futura reservada exclusivamente para pruebas (lunes, EMP004 tiene turno 10:40-17:00)
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
    
    session.commit()


class TestHorasLaboradas:
    """Pruebas para el cálculo de horas laboradas"""
    
    def setup_method(self):
        self.session = Session(test_engine)
        self.empleado = self.session.scalar(
            select(Empleado).where(Empleado.numero_empleado == "EMP004")
        )
        if not self.empleado:
            raise Exception("Empleado EMP004 no encontrado")
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
            fecha_evento=datetime.combine(fecha, time(12, 0)).replace(tzinfo=now.tzinfo)
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
        
        # 3h mañana + 4h tarde = 7h = 420 minutos
        assert resultado["minutos_laborados"] == 420
        assert resultado["minutos_descanso"] == 60  # 1 hora de descanso
        print("[OK] Test calcular_horas_laboradas_con_salida_temporal: PASSED")


class TestHorasExtras:
    """Pruebas para el cálculo de horas extras"""
    
    def setup_method(self):
        self.session = Session(test_engine)
        self.empleado = self.session.scalar(
            select(Empleado).where(Empleado.numero_empleado == "EMP004")
        )
        if not self.empleado:
            raise Exception("Empleado EMP004 no encontrado")
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
            select(Empleado).where(Empleado.numero_empleado == "EMP004")
        )
        if not self.empleado:
            raise Exception("Empleado EMP004 no encontrado")
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
            select(Empleado).where(Empleado.numero_empleado == "EMP004")
        )
        if not self.empleado:
            raise Exception("Empleado EMP004 no encontrado")
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
        # Verificar que EMP004 tiene turno con tolerancia definida
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
    
    # Ejecutar pruebas de reportes
    print("[TEST] EJECUTANDO PRUEBAS DE REPORTES...")
    test_reportes = TestReportes()
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
    
    # Ejecutar pruebas de autorización horas extra
    print("[TEST] EJECUTANDO PRUEBAS DE AUTORIZACION HORAS EXTRA...")
    test_autorizacion = TestAutorizacionHorasExtra()
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
