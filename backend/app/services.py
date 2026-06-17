from datetime import datetime, timedelta, date
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.time import utc_now
from app.models import BloqueHorasExtra, CorreccionManual, DetallePlantillaTurno, Empleado, EstadoEmpleado, EstadoRegistro, EstadoVisita, EventoAsistencia, ObservacionCaseta, PlantillaTurno, RegistroAsistencia, RegistroAusencia, SupervisorDepartamento, TipoEvento, TipoSalida, TurnoHorario, UsuarioSistema, Visita


def crear_visita(db: Session, empleado_id: int, asistencia_id: int) -> Visita:
    """Crea una visita para una entrada fuera de horario."""
    now = utc_now()
    
    # Usar now como hora_inicio para evitar problemas de timezone
    hora_inicio = now
    
    minutos_duracion = None
    
    visita = Visita(
        empleado_id=empleado_id,
        asistencia_id=asistencia_id,
        fecha_visita=now,
        hora_inicio=hora_inicio,
        hora_fin=None,
        minutos_duracion=minutos_duracion,
        estado=EstadoVisita.PENDIENTE
    )
    db.add(visita)
    db.commit()
    db.refresh(visita)
    return visita


def calcular_y_registrar_bloques_horas_extra(db: Session, asistencia: RegistroAsistencia, hora_entrada: datetime, hora_salida: datetime):
    """Calcula y registra bloques de horas extra separados (antes del inicio y después del fin del turno)."""
    empleado = db.get(Empleado, asistencia.empleado_id)
    if not empleado:
        return
    
    # Obtener horario oficial del empleado
    turno = get_empleado_turno(db, empleado, asistencia.fecha_turno.weekday())
    if not turno or not turno["hora_entrada_oficial"] or not turno["hora_salida_oficial"]:
        return
    
    now = utc_now()
    # Asegurar que hora_entrada y hora_salida tengan timezone
    if hora_entrada.tzinfo is None:
        hora_entrada = hora_entrada.replace(tzinfo=now.tzinfo)
    if hora_salida.tzinfo is None:
        hora_salida = hora_salida.replace(tzinfo=now.tzinfo)
    
    hora_entrada_oficial = datetime.combine(asistencia.fecha_turno, turno["hora_entrada_oficial"], tzinfo=now.tzinfo)
    hora_salida_oficial = datetime.combine(asistencia.fecha_turno, turno["hora_salida_oficial"], tzinfo=now.tzinfo)
    
    # Eliminar bloques existentes para evitar duplicación al recalcular
    bloques_existentes = db.scalars(
        select(BloqueHorasExtra).where(BloqueHorasExtra.asistencia_id == asistencia.id)
    ).all()
    for b in bloques_existentes:
        db.delete(b)
    db.flush()
    
    # Bloque 1: Horas extra antes del inicio del turno
    if hora_entrada < hora_entrada_oficial:
        hora_fin_bloque_1 = min(hora_salida, hora_entrada_oficial)
        minutos_extra_1 = int((hora_fin_bloque_1 - hora_entrada).total_seconds() / 60)
        
        if minutos_extra_1 > 0:
            bloque = BloqueHorasExtra(
                asistencia_id=asistencia.id,
                tipo_bloque="ANTES_INICIO",
                hora_inicio=hora_entrada,
                hora_fin=hora_fin_bloque_1,
                minutos_extra=minutos_extra_1
            )
            db.add(bloque)
    
    # Bloque 2: Horas extra después del fin del turno
    if hora_salida > hora_salida_oficial:
        hora_inicio_bloque_2 = max(hora_entrada, hora_salida_oficial)
        minutos_extra_2 = int((hora_salida - hora_inicio_bloque_2).total_seconds() / 60)
        
        if minutos_extra_2 > 0:
            bloque = BloqueHorasExtra(
                asistencia_id=asistencia.id,
                tipo_bloque="DESPUES_FIN",
                hora_inicio=hora_inicio_bloque_2,
                hora_fin=hora_salida,
                minutos_extra=minutos_extra_2
            )
            db.add(bloque)
    
    # Actualizar minutos_extra_calculados con el total
    bloques = db.scalars(
        select(BloqueHorasExtra).where(BloqueHorasExtra.asistencia_id == asistencia.id)
    ).all()
    total_minutos_extra = sum(b.minutos_extra for b in bloques)
    asistencia.minutos_extra_calculados = total_minutos_extra
    
    db.commit()


def verificar_ausencia_aprobada(db: Session, empleado_id: int, fecha: date) -> dict | None:
    """Verifica si un empleado tiene una ausencia aprobada en la fecha especificada.
    Retorna un dict con tipo_ausencia y otros detalles, o None si no hay ausencia."""
    from app.models import TipoAusencia
    
    ausencia = db.scalar(
        select(RegistroAusencia).where(
            RegistroAusencia.empleado_id == empleado_id,
            RegistroAusencia.fecha_inicio <= fecha,
            RegistroAusencia.fecha_fin >= fecha,
            RegistroAusencia.aprobado_rrhh == True
        )
    )
    
    if ausencia:
        return {
            "tipo_ausencia": ausencia.tipo_ausencia.value,
            "pagada": ausencia.pagada,
            "porcentaje_aportacion": ausencia.porcentaje_aportacion,
            "motivo": ausencia.motivo
        }
    return None


def procesar_visitas_vencidas(db: Session):
    """Marca como NO_PAGADA las visitas que no han sido resueltas después de 2 días."""
    from app.models import EstadoVisita
    
    limite_dias = 2
    fecha_limite = utc_now() - timedelta(days=limite_dias)
    
    visitas_vencidas = db.scalars(
        select(Visita).where(
            Visita.estado == EstadoVisita.PENDIENTE,
            Visita.fecha_visita < fecha_limite
        )
    ).all()
    
    for visita in visitas_vencidas:
        visita.estado = EstadoVisita.NO_PAGADA
        db.add(ObservacionCaseta(
            asistencia_id=visita.asistencia_id,
            tipo_observacion=f"Visita marcada como NO PAGADA automáticamente después de {limite_dias} días sin resolución",
            fecha_registro=utc_now()
        ))
    
    db.commit()
    return len(visitas_vencidas)


def calcular_horas_laboradas(db: Session, empleado_id: int, fecha: date) -> dict:
    """Calcula las horas laboradas de un empleado en una fecha específica.
    
    Lógica de bloques:
    - Caso 1: Bloque completamente fuera de horario = visita (requiere validación RRHH)
    - Caso 2: Entra antes de X, sale en horario = extra previa + laborada
    - Caso 3: Entra en horario, sale en horario = solo laborada
    - Caso 4: Entra en horario, sale después de Y = laborada + extra posterior
    - Caso 5: Entra antes de X, sale después de Y = extra previa + laborada + extra posterior
    
    Regla de turno cumplido: Después de cumplir el turno, bloques posteriores = visitas
    Ausencias: Todos los eventos del día = visitas (sujetas a validación RRHH)
    """
    now = utc_now()
    
    # Verificar si hay ausencia aprobada (vacaciones/incapacidad/permiso)
    ausencia = verificar_ausencia_aprobada(db, empleado_id, fecha)
    if ausencia:
        # Si hay ausencia, calcular horas según tipo y porcentaje
        # Vacaciones: siempre pagadas (100%)
        # Incapacidades: según porcentaje_aportacion (0-100%)
        # Permisos: según campo pagada (true/false)
        # Y procesar eventos del día como visitas
        
        tipo_ausencia = ausencia["tipo_ausencia"]
        pagada = ausencia["pagada"]
        porcentaje = ausencia["porcentaje_aportacion"]
        
        # Obtener eventos del día para procesar como visitas
        fecha_inicio = datetime.combine(fecha, datetime.min.time()).replace(tzinfo=now.tzinfo)
        fecha_fin = datetime.combine(fecha, datetime.max.time()).replace(tzinfo=now.tzinfo)
        
        eventos = db.scalars(
            select(EventoAsistencia)
            .where(EventoAsistencia.empleado_id == empleado_id)
            .where(EventoAsistencia.fecha_evento >= fecha_inicio)
            .where(EventoAsistencia.fecha_evento <= fecha_fin)
            .order_by(EventoAsistencia.fecha_evento)
        ).all()
        
        # Procesar eventos como bloques de visitas
        bloques_visitas = []
        hora_entrada_actual = None
        
        for evento in eventos:
            if evento.tipo_evento == TipoEvento.ENTRADA:
                hora_entrada_actual = evento.fecha_evento
            elif evento.tipo_evento == TipoEvento.SALIDA and hora_entrada_actual:
                hora_salida = evento.fecha_evento
                if hora_salida.tzinfo is None:
                    hora_salida = hora_salida.replace(tzinfo=now.tzinfo)
                if hora_entrada_actual.tzinfo is None:
                    hora_entrada_actual = hora_entrada_actual.replace(tzinfo=now.tzinfo)
                
                minutos = int((hora_salida - hora_entrada_actual).total_seconds() / 60)
                bloques_visitas.append({
                    "tipo": "Visita_Ausencia",
                    "hora_inicio": hora_entrada_actual.isoformat(),
                    "hora_fin": hora_salida.isoformat(),
                    "minutos": minutos,
                    "motivo_ausencia": tipo_ausencia
                })
                hora_entrada_actual = None
        
        if tipo_ausencia == "Vacaciones":
            # Vacaciones siempre cuentan como horas laboradas al 100%
            # Obtener turno para calcular horas del día
            empleado = db.get(Empleado, empleado_id)
            turno = get_empleado_turno(db, empleado, fecha.weekday())
            if turno and turno["hora_entrada_oficial"] and turno["hora_salida_oficial"]:
                hora_entrada = datetime.combine(fecha, turno["hora_entrada_oficial"], tzinfo=now.tzinfo)
                hora_salida = datetime.combine(fecha, turno["hora_salida_oficial"], tzinfo=now.tzinfo)
                minutos_laborados = int((hora_salida - hora_entrada).total_seconds() / 60)
            else:
                minutos_laborados = 0
            
            # Aplicar correcciones manuales
            correcciones = db.scalars(
                select(CorreccionManual).where(
                    CorreccionManual.empleado_id == empleado_id,
                    CorreccionManual.fecha == fecha
                )
            ).all()
            
            for correccion in correcciones:
                if correccion.tipo_correccion.value == "Horas_Laboradas":
                    minutos_laborados += correccion.minutos_agregados
            
            return {
                "minutos_laborados": minutos_laborados,
                "minutos_extra": 0,
                "minutos_descanso": 0,
                "total_eventos": len(eventos),
                "eventos": [
                    {
                        "tipo": e.tipo_evento.value,
                        "fecha": e.fecha_evento.isoformat(),
                        "observaciones": e.observaciones
                    }
                    for e in eventos
                ],
                "ausencia": ausencia,
                "bloques_visitas": bloques_visitas,  # Bloques de visitas detectados
                "bloques_extra": [],
                "correcciones": [
                    {
                        "tipo": c.tipo_correccion.value,
                        "minutos": c.minutos_agregados,
                        "motivo": c.motivo
                    }
                    for c in correcciones
                ]
            }
        elif tipo_ausencia == "Incapacidad":
            # Incapacidad: según porcentaje de aportación
            empleado = db.get(Empleado, empleado_id)
            turno = get_empleado_turno(db, empleado, fecha.weekday())
            if turno and turno["hora_entrada_oficial"] and turno["hora_salida_oficial"]:
                hora_entrada = datetime.combine(fecha, turno["hora_entrada_oficial"], tzinfo=now.tzinfo)
                hora_salida = datetime.combine(fecha, turno["hora_salida_oficial"], tzinfo=now.tzinfo)
                minutos_completos = int((hora_salida - hora_entrada).total_seconds() / 60)
                minutos_laborados = int(minutos_completos * porcentaje / 100)
            else:
                minutos_laborados = 0
            
            # Aplicar correcciones manuales
            correcciones = db.scalars(
                select(CorreccionManual).where(
                    CorreccionManual.empleado_id == empleado_id,
                    CorreccionManual.fecha == fecha
                )
            ).all()
            
            for correccion in correcciones:
                if correccion.tipo_correccion.value == "Horas_Laboradas":
                    minutos_laborados += correccion.minutos_agregados
            
            return {
                "minutos_laborados": minutos_laborados,
                "minutos_extra": 0,
                "minutos_descanso": 0,
                "total_eventos": len(eventos),
                "eventos": [
                    {
                        "tipo": e.tipo_evento.value,
                        "fecha": e.fecha_evento.isoformat(),
                        "observaciones": e.observaciones
                    }
                    for e in eventos
                ],
                "ausencia": ausencia,
                "bloques_visitas": bloques_visitas,  # Bloques de visitas detectados
                "bloques_extra": [],
                "correcciones": [
                    {
                        "tipo": c.tipo_correccion.value,
                        "minutos": c.minutos_agregados,
                        "motivo": c.motivo
                    }
                    for c in correcciones
                ]
            }
        elif tipo_ausencia == "Permiso":
            # Permiso: según campo pagada
            if pagada:
                empleado = db.get(Empleado, empleado_id)
                turno = get_empleado_turno(db, empleado, fecha.weekday())
                if turno and turno["hora_entrada_oficial"] and turno["hora_salida_oficial"]:
                    hora_entrada = datetime.combine(fecha, turno["hora_entrada_oficial"], tzinfo=now.tzinfo)
                    hora_salida = datetime.combine(fecha, turno["hora_salida_oficial"], tzinfo=now.tzinfo)
                    minutos_laborados = int((hora_salida - hora_entrada).total_seconds() / 60)
                else:
                    minutos_laborados = 0
            else:
                minutos_laborados = 0
            
            # Aplicar correcciones manuales
            correcciones = db.scalars(
                select(CorreccionManual).where(
                    CorreccionManual.empleado_id == empleado_id,
                    CorreccionManual.fecha == fecha
                )
            ).all()
            
            for correccion in correcciones:
                if correccion.tipo_correccion.value == "Horas_Laboradas":
                    minutos_laborados += correccion.minutos_agregados
            
            return {
                "minutos_laborados": minutos_laborados,
                "minutos_extra": 0,
                "minutos_descanso": 0,
                "total_eventos": len(eventos),
                "eventos": [
                    {
                        "tipo": e.tipo_evento.value,
                        "fecha": e.fecha_evento.isoformat(),
                        "observaciones": e.observaciones
                    }
                    for e in eventos
                ],
                "ausencia": ausencia,
                "bloques_visitas": bloques_visitas,  # Bloques de visitas detectados
                "bloques_extra": [],
                "correcciones": [
                    {
                        "tipo": c.tipo_correccion.value,
                        "minutos": c.minutos_agregados,
                        "motivo": c.motivo
                    }
                    for c in correcciones
                ]
            }
    
    # Obtener todos los eventos del empleado en la fecha
    # Asegurar que las fechas de comparación tengan timezone
    fecha_inicio = datetime.combine(fecha, datetime.min.time()).replace(tzinfo=now.tzinfo)
    fecha_fin = datetime.combine(fecha, datetime.max.time()).replace(tzinfo=now.tzinfo)
    
    eventos = db.scalars(
        select(EventoAsistencia)
        .where(EventoAsistencia.empleado_id == empleado_id)
        .where(EventoAsistencia.fecha_evento >= fecha_inicio)
        .where(EventoAsistencia.fecha_evento <= fecha_fin)
        .order_by(EventoAsistencia.fecha_evento)
    ).all()
    
    if not eventos:
        # Fallback: usar hora_entrada_real y hora_salida_real del RegistroAsistencia
        asistencia = db.scalar(
            select(RegistroAsistencia).where(
                RegistroAsistencia.empleado_id == empleado_id,
                RegistroAsistencia.fecha_turno == fecha
            )
        )
        
        # Obtener horario oficial del turno
        empleado = db.get(Empleado, empleado_id)
        turno = get_empleado_turno(db, empleado, fecha.weekday())
        hora_entrada_oficial = None
        hora_salida_oficial = None
        tolerancia_minutos = 0
        if turno and turno["hora_entrada_oficial"] and turno["hora_salida_oficial"]:
            hora_entrada_oficial = datetime.combine(fecha, turno["hora_entrada_oficial"], tzinfo=now.tzinfo)
            hora_salida_oficial = datetime.combine(fecha, turno["hora_salida_oficial"], tzinfo=now.tzinfo)
            tolerancia_minutos = turno.get("tolerancia_minutos", 0)
        
        minutos_laborados = 0
        bloques_extra = []
        
        if asistencia and asistencia.hora_entrada_real and asistencia.hora_salida_real:
            # Asegurar que ambos tengan timezone
            hora_entrada = asistencia.hora_entrada_real
            hora_salida = asistencia.hora_salida_real
            if hora_entrada.tzinfo is None:
                hora_entrada = hora_entrada.replace(tzinfo=now.tzinfo)
            if hora_salida.tzinfo is None:
                hora_salida = hora_salida.replace(tzinfo=now.tzinfo)
            
            # Aplicar lógica de los 5 casos
            if hora_entrada_oficial and hora_salida_oficial:
                # Caso 1: Bloque completamente antes de X o después de Y = visita
                if hora_salida <= hora_entrada_oficial or hora_entrada >= hora_salida_oficial:
                    # Bloque completamente fuera de horario = visita (no se cuenta)
                    pass
                # Caso 2: Entra antes de X, sale en horario
                elif hora_entrada < hora_entrada_oficial and hora_salida <= hora_salida_oficial:
                    minutos_laborados = int((hora_salida - hora_entrada_oficial).total_seconds() / 60)
                    minutos_extra_previa = int((hora_entrada_oficial - hora_entrada).total_seconds() / 60)
                    bloques_extra.append({
                        "tipo": "Extra_Previa",
                        "hora_inicio": hora_entrada.isoformat(),
                        "hora_fin": hora_entrada_oficial.isoformat(),
                        "minutos": minutos_extra_previa
                    })
                # Caso 3: Entra en horario, sale en horario
                elif hora_entrada >= hora_entrada_oficial and hora_salida <= hora_salida_oficial:
                    # Verificar si está dentro de tolerancia de entrada
                    limite_entrada_tolerancia = hora_entrada_oficial + timedelta(minutes=tolerancia_minutos)
                    if hora_entrada <= limite_entrada_tolerancia:
                        # Está dentro de tolerancia, usar hora oficial
                        minutos_laborados = int((hora_salida - hora_entrada_oficial).total_seconds() / 60)
                    else:
                        # Fuera de tolerancia, usar hora real
                        minutos_laborados = int((hora_salida - hora_entrada).total_seconds() / 60)
                # Caso 4: Entra en horario, sale después de Y
                elif hora_entrada >= hora_entrada_oficial and hora_salida > hora_salida_oficial:
                    # Verificar si está dentro de tolerancia de entrada
                    limite_entrada_tolerancia = hora_entrada_oficial + timedelta(minutes=tolerancia_minutos)
                    if hora_entrada <= limite_entrada_tolerancia:
                        # Está dentro de tolerancia, usar hora oficial
                        minutos_laborados = int((hora_salida_oficial - hora_entrada_oficial).total_seconds() / 60)
                    else:
                        # Fuera de tolerancia, usar hora real
                        minutos_laborados = int((hora_salida_oficial - hora_entrada).total_seconds() / 60)
                    minutos_extra_posterior = int((hora_salida - hora_salida_oficial).total_seconds() / 60)
                    bloques_extra.append({
                        "tipo": "Extra_Posterior",
                        "hora_inicio": hora_salida_oficial.isoformat(),
                        "hora_fin": hora_salida.isoformat(),
                        "minutos": minutos_extra_posterior
                    })
                # Caso 5: Entra antes de X, sale después de Y
                elif hora_entrada < hora_entrada_oficial and hora_salida > hora_salida_oficial:
                    minutos_laborados = int((hora_salida_oficial - hora_entrada_oficial).total_seconds() / 60)
                    minutos_extra_previa = int((hora_entrada_oficial - hora_entrada).total_seconds() / 60)
                    minutos_extra_posterior = int((hora_salida - hora_salida_oficial).total_seconds() / 60)
                    bloques_extra.append({
                        "tipo": "Extra_Previa",
                        "hora_inicio": hora_entrada.isoformat(),
                        "hora_fin": hora_entrada_oficial.isoformat(),
                        "minutos": minutos_extra_previa
                    })
                    bloques_extra.append({
                        "tipo": "Extra_Posterior",
                        "hora_inicio": hora_salida_oficial.isoformat(),
                        "hora_fin": hora_salida.isoformat(),
                        "minutos": minutos_extra_posterior
                    })
            else:
                # Sin horario oficial, contar todo
                minutos_laborados = int((hora_salida - hora_entrada).total_seconds() / 60)
        
        # Aplicar correcciones manuales
        correcciones = db.scalars(
            select(CorreccionManual).where(
                CorreccionManual.empleado_id == empleado_id,
                CorreccionManual.fecha == fecha
            )
        ).all()
        
        for correccion in correcciones:
            if correccion.tipo_correccion.value == "Horas_Laboradas":
                minutos_laborados += correccion.minutos_agregados
            elif correccion.tipo_correccion.value == "Permiso":
                # Los permisos descuentan de las horas laboradas (RRHH agrega minutos positivos que se restan)
                minutos_laborados -= correccion.minutos_agregados
        
        return {
            "minutos_laborados": minutos_laborados,
            "minutos_extra": 0,
            "minutos_descanso": 0,
            "total_eventos": 0,
            "eventos": [],
            "bloques_extra": bloques_extra,
            "correcciones": [
                {
                    "tipo": c.tipo_correccion.value,
                    "minutos": c.minutos_agregados,
                    "motivo": c.motivo
                }
                for c in correcciones
            ]
        }
    
    # Obtener horario oficial del turno para limitar cálculo
    empleado = db.get(Empleado, empleado_id)
    turno = get_empleado_turno(db, empleado, fecha.weekday())
    hora_entrada_oficial = None
    hora_salida_oficial = None
    tolerancia_entrada_previa = 0  # Tolerancia para entrada antes de la hora oficial
    if turno and turno["hora_entrada_oficial"] and turno["hora_salida_oficial"]:
        hora_entrada_oficial = datetime.combine(fecha, turno["hora_entrada_oficial"], tzinfo=now.tzinfo)
        hora_salida_oficial = datetime.combine(fecha, turno["hora_salida_oficial"], tzinfo=now.tzinfo)
        tolerancia_entrada_previa = turno.get("tolerancia_entrada_previa_minutos", 0)
    
    minutos_laborados = 0
    minutos_descanso = 0
    turno_cumplido = False  # Rastrear si ya se cumplió el turno
    turno_terminado_por_permiso = False  # Rastrear si el turno terminó por permiso sin regreso
    bloques_extra = []  # Bloques de horas extra creados
    hora_entrada_actual = None
    hora_salida_temporal = None
    tipo_salida_temporal_actual = None
    eventos_detalle = []
    
    for evento in eventos:
        eventos_detalle.append({
            "tipo": evento.tipo_evento.value,
            "fecha": evento.fecha_evento.isoformat(),
            "observaciones": evento.observaciones
        })
        
        # Verificar si el evento está asociado a una visita no pagada
        visita_no_pagada = False
        if evento.asistencia:
            visita = db.scalar(
                select(Visita).where(
                    Visita.asistencia_id == evento.asistencia.id,
                    Visita.estado == EstadoVisita.NO_PAGADA
                )
            )
            if visita:
                visita_no_pagada = True
        
        # Si es visita no pagada, no contar las horas
        if visita_no_pagada:
            continue
        
        if evento.tipo_evento == TipoEvento.ENTRADA:
            hora_entrada_actual = evento.fecha_evento
        elif evento.tipo_evento == TipoEvento.SALIDA and hora_entrada_actual:
            # Procesar bloque entrada-salida según los 5 casos
            hora_salida = evento.fecha_evento
            if hora_salida.tzinfo is None:
                hora_salida = hora_salida.replace(tzinfo=now.tzinfo)
            if hora_entrada_actual.tzinfo is None:
                hora_entrada_actual = hora_entrada_actual.replace(tzinfo=now.tzinfo)
            
            if hora_entrada_oficial and hora_salida_oficial:
                # Si ya se cumplió el turno, este bloque es visita
                if turno_cumplido:
                    # Bloque posterior al turno = visita (no se cuenta)
                    pass
                else:
                    # Determinar caso según posición del bloque
                    # Caso 1: Bloque completamente antes de X o después de Y = visita
                    if hora_salida <= hora_entrada_oficial or hora_entrada_actual >= hora_salida_oficial:
                        # Bloque completamente fuera de horario = visita
                        pass
                    # Caso 2: Entra antes de X, sale en horario (antes de Y)
                    elif hora_entrada_actual < hora_entrada_oficial and hora_salida <= hora_salida_oficial:
                        # Extra previa: entrada_real -> X
                        minutos_extra_previa = int((hora_entrada_oficial - hora_entrada_actual).total_seconds() / 60)
                        # Laborada: X -> salida_real
                        minutos_laborados_bloque = int((hora_salida - hora_entrada_oficial).total_seconds() / 60)
                        minutos_laborados += minutos_laborados_bloque
                        # Crear bloque de extra previa (requiere validación)
                        bloques_extra.append({
                            "tipo": "Extra_Previa",
                            "hora_inicio": hora_entrada_actual.isoformat(),
                            "hora_fin": hora_entrada_oficial.isoformat(),
                            "minutos": minutos_extra_previa
                        })
                    # Caso 3: Entra en horario, sale en horario = solo laborada
                    elif hora_entrada_actual >= hora_entrada_oficial and hora_salida <= hora_salida_oficial:
                        # Verificar si está dentro de tolerancia de entrada
                        limite_entrada_tolerancia = hora_entrada_oficial + timedelta(minutes=turno.get("tolerancia_minutos", 0))
                        if hora_entrada_actual <= limite_entrada_tolerancia:
                            # Está dentro de tolerancia, usar hora oficial
                            minutos = int((hora_salida - hora_entrada_oficial).total_seconds() / 60)
                        else:
                            # Fuera de tolerancia, usar hora real
                            minutos = int((hora_salida - hora_entrada_actual).total_seconds() / 60)
                        minutos_laborados += minutos
                    # Caso 4: Entra en horario, sale después de Y
                    elif hora_entrada_actual >= hora_entrada_oficial and hora_salida > hora_salida_oficial:
                        # Verificar si está dentro de tolerancia de entrada
                        limite_entrada_tolerancia = hora_entrada_oficial + timedelta(minutes=turno.get("tolerancia_minutos", 0))
                        if hora_entrada_actual <= limite_entrada_tolerancia:
                            # Está dentro de tolerancia, usar hora oficial
                            minutos_laborados_bloque = int((hora_salida_oficial - hora_entrada_oficial).total_seconds() / 60)
                        else:
                            # Fuera de tolerancia, usar hora real
                            minutos_laborados_bloque = int((hora_salida_oficial - hora_entrada_actual).total_seconds() / 60)
                        minutos_laborados += minutos_laborados_bloque
                        # Extra posterior: Y -> salida_real
                        minutos_extra_posterior = int((hora_salida - hora_salida_oficial).total_seconds() / 60)
                        # Crear bloque de extra posterior (requiere validación)
                        bloques_extra.append({
                            "tipo": "Extra_Posterior",
                            "hora_inicio": hora_salida_oficial.isoformat(),
                            "hora_fin": hora_salida.isoformat(),
                            "minutos": minutos_extra_posterior
                        })
                        turno_cumplido = True  # Turno cumplido
                    # Caso 5: Entra antes de X, sale después de Y
                    elif hora_entrada_actual < hora_entrada_oficial and hora_salida > hora_salida_oficial:
                        # Extra previa: entrada_real -> X
                        minutos_extra_previa = int((hora_entrada_oficial - hora_entrada_actual).total_seconds() / 60)
                        # Laborada: X -> Y
                        minutos_laborados_bloque = int((hora_salida_oficial - hora_entrada_oficial).total_seconds() / 60)
                        minutos_laborados += minutos_laborados_bloque
                        # Extra posterior: Y -> salida_real
                        minutos_extra_posterior = int((hora_salida - hora_salida_oficial).total_seconds() / 60)
                        # Crear bloques de extra (requieren validación)
                        bloques_extra.append({
                            "tipo": "Extra_Previa",
                            "hora_inicio": hora_entrada_actual.isoformat(),
                            "hora_fin": hora_entrada_oficial.isoformat(),
                            "minutos": minutos_extra_previa
                        })
                        bloques_extra.append({
                            "tipo": "Extra_Posterior",
                            "hora_inicio": hora_salida_oficial.isoformat(),
                            "hora_fin": hora_salida.isoformat(),
                            "minutos": minutos_extra_posterior
                        })
                        turno_cumplido = True  # Turno cumplido
            else:
                # Sin horario oficial, contar todo como laborada
                minutos = int((hora_salida - hora_entrada_actual).total_seconds() / 60)
                minutos_laborados += minutos
            hora_entrada_actual = None
        elif evento.tipo_evento == TipoEvento.SALIDA_TEMPORAL and hora_entrada_actual:
            # Guardar la hora de salida temporal para calcular tiempo de descanso
            hora_salida_temporal = evento.fecha_evento
            tipo_salida_temporal_actual = evento.tipo_salida
            # Sumar minutos laborados hasta la salida temporal
            # Asegurar que ambos tengan timezone
            if hora_salida_temporal.tzinfo is None:
                hora_salida_temporal = hora_salida_temporal.replace(tzinfo=now.tzinfo)
            if hora_entrada_actual.tzinfo is None:
                hora_entrada_actual = hora_entrada_actual.replace(tzinfo=now.tzinfo)
            minutos = int((hora_salida_temporal - hora_entrada_actual).total_seconds() / 60)
            minutos_laborados += minutos
            hora_entrada_actual = None
        elif evento.tipo_evento == TipoEvento.REGRESO_SALIDA_TEMPORAL:
            # Calcular minutos durante la salida temporal
            if hora_salida_temporal:
                # Asegurar que ambos tengan timezone
                hora_regreso = evento.fecha_evento
                if hora_regreso.tzinfo is None:
                    hora_regreso = hora_regreso.replace(tzinfo=now.tzinfo)
                if hora_salida_temporal.tzinfo is None:
                    hora_salida_temporal = hora_salida_temporal.replace(tzinfo=now.tzinfo)
                
                # Si el regreso es después de la hora de salida oficial, tratar como visita
                if hora_salida_oficial and hora_regreso >= hora_salida_oficial and tipo_salida_temporal_actual == TipoSalida.PERMISO_PERSONAL.value:
                    # El permiso se extendió hasta la hora de salida oficial
                    # El regreso es una visita, no contar
                    minutos_ausente = int((hora_salida_oficial - hora_salida_temporal).total_seconds() / 60)
                    minutos_descanso = minutos_ausente
                    # No reanudar conteo, el turno terminó a la hora de salida oficial
                    hora_entrada_actual = None
                    turno_cumplido = True
                    turno_terminado_por_permiso = True
                else:
                    minutos_ausente = int((hora_regreso - hora_salida_temporal).total_seconds() / 60)
                    # Las salidas a Comer NO descuentan tiempo laborado: el tiempo se cuenta como trabajado
                    if tipo_salida_temporal_actual == TipoSalida.COMER.value:
                        minutos_laborados += minutos_ausente
                    else:
                        minutos_descanso = minutos_ausente
                    # Reanudar conteo desde el regreso
                    hora_entrada_actual = evento.fecha_evento
                hora_salida_temporal = None
                tipo_salida_temporal_actual = None
    
    # Si hay una salida temporal abierta de permiso al final del ciclo de eventos
    # significa que el empleado no regresó, el turno termina a la hora oficial
    if hora_salida_temporal and tipo_salida_temporal_actual == TipoSalida.PERMISO_PERSONAL.value:
        if hora_salida_oficial:
            # Calcular minutos de permiso hasta la hora oficial
            if hora_salida_temporal.tzinfo is None:
                hora_salida_temporal = hora_salida_temporal.replace(tzinfo=now.tzinfo)
            minutos_ausente = int((hora_salida_oficial - hora_salida_temporal).total_seconds() / 60)
            if minutos_ausente > 0:
                minutos_descanso = minutos_ausente
                turno_terminado_por_permiso = True
                turno_cumplido = True
        hora_salida_temporal = None
        tipo_salida_temporal_actual = None
    
    # Aplicar correcciones manuales de RRHH
    correcciones = db.scalars(
        select(CorreccionManual).where(
            CorreccionManual.empleado_id == empleado_id,
            CorreccionManual.fecha == fecha
        )
    ).all()
    
    for correccion in correcciones:
        if correccion.tipo_correccion.value == "Horas_Laboradas":
            minutos_laborados += correccion.minutos_agregados
        elif correccion.tipo_correccion.value == "Permiso":
            # Los permisos descuentan de las horas laboradas (RRHH agrega minutos positivos que se restan)
            minutos_laborados -= correccion.minutos_agregados
    
    # Restar minutos de descanso (salidas temporales por permiso) de las horas laboradas
    # Solo si el turno terminó por permiso sin regreso (los minutos ya no se contaron en los bloques)
    if turno_terminado_por_permiso:
        minutos_laborados -= minutos_descanso
    
    return {
        "minutos_laborados": minutos_laborados,
        "minutos_extra": 0,  # No se calculan aquí, van en reporte de horas extra
        "minutos_descanso": minutos_descanso,
        "total_eventos": len(eventos),
        "eventos": eventos_detalle,
        "bloques_extra": bloques_extra,  # Bloques de horas extra detectados
        "correcciones": [
            {
                "tipo": c.tipo_correccion.value,
                "minutos": c.minutos_agregados,
                "motivo": c.motivo
            }
            for c in correcciones
        ]
    }


def get_or_create_today_asistencia(db: Session, empleado: Empleado) -> RegistroAsistencia:
    now = utc_now()
    asistencia = db.scalar(
        select(RegistroAsistencia).where(
            RegistroAsistencia.empleado_id == empleado.id,
            RegistroAsistencia.fecha_turno == now.date(),
        )
    )
    if asistencia:
        return asistencia
    asistencia = RegistroAsistencia(empleado_id=empleado.id, fecha_turno=now.date())
    db.add(asistencia)
    db.flush()
    return asistencia


def get_empleado_turno(db: Session, empleado: Empleado, dia_semana: int):
    """Obtiene el horario del empleado para un día específico.
    Primero busca en turnos individuales, si no tiene, busca en plantilla si está asignada."""
    # Primero buscar turnos individuales
    turno_individual = db.scalar(
        select(TurnoHorario).where(
            TurnoHorario.empleado_id == empleado.id,
            TurnoHorario.dia_semana == dia_semana
        )
    )
    if turno_individual:
        return {
            "hora_entrada_oficial": turno_individual.hora_entrada_oficial,
            "hora_salida_oficial": turno_individual.hora_salida_oficial,
            "tolerancia_minutos": turno_individual.tolerancia_minutos,
            "tolerancia_entrada_previa_minutos": turno_individual.tolerancia_entrada_previa_minutos,
            "tolerancia_salida_posterior_minutos": turno_individual.tolerancia_salida_posterior_minutos,
            "tolerancia_salida_previa_minutos": turno_individual.tolerancia_salida_previa_minutos,
            "es_descanso": turno_individual.es_descanso
        }
    
    # Si no tiene turnos individuales, buscar en plantilla
    if empleado.plantilla_turno_id:
        plantilla = db.get(PlantillaTurno, empleado.plantilla_turno_id)
        if plantilla:
            detalle = db.scalar(
                select(DetallePlantillaTurno).where(
                    DetallePlantillaTurno.plantilla_id == plantilla.id,
                    DetallePlantillaTurno.dia_semana == dia_semana
                )
            )
            if detalle:
                return {
                    "hora_entrada_oficial": detalle.hora_entrada_oficial,
                    "hora_salida_oficial": detalle.hora_salida_oficial,
                    "tolerancia_minutos": detalle.tolerancia_minutos,
                    "tolerancia_entrada_previa_minutos": detalle.tolerancia_entrada_previa_minutos,
                    "tolerancia_salida_posterior_minutos": detalle.tolerancia_salida_posterior_minutos,
                    "tolerancia_salida_previa_minutos": detalle.tolerancia_salida_previa_minutos,
                    "es_descanso": detalle.es_descanso
                }
    
    return None


def get_employee_info(db: Session, gafete: str) -> dict:
    now = utc_now()
    empleado = db.scalar(select(Empleado).where(Empleado.numero_empleado == gafete, Empleado.activo.is_(True)))
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado o inactivo")

    asistencia = get_or_create_today_asistencia(db, empleado)
    turno = get_empleado_turno(db, empleado, now.weekday())

    # Verificar ausencias programadas
    ausencias = db.scalars(
        select(RegistroAusencia).where(
            RegistroAusencia.empleado_id == empleado.id,
            RegistroAusencia.fecha_inicio <= now.date(),
            RegistroAusencia.fecha_fin >= now.date(),
            RegistroAusencia.aprobado_rrhh == True
        )
    ).all()

    horario_info = None
    fuera_horario = False
    if turno and not turno["es_descanso"] and turno["hora_entrada_oficial"]:
        limite_entrada = datetime.combine(now.date(), turno["hora_entrada_oficial"], tzinfo=now.tzinfo) + timedelta(minutes=turno["tolerancia_minutos"])
        # No marcar fuera de horario si hay ausencias programadas (vacaciones, incapacidad)
        # No marcar fuera de horario si ya tiene entrada registrada (pase aceptado)
        if not ausencias and not asistencia.hora_entrada_real:
            fuera_horario = now > limite_entrada
        horario_info = {
            "hora_entrada_oficial": turno["hora_entrada_oficial"].strftime("%H:%M") if turno["hora_entrada_oficial"] else None,
            "hora_salida_oficial": turno["hora_salida_oficial"].strftime("%H:%M") if turno["hora_salida_oficial"] else None,
            "tolerancia_minutos": turno["tolerancia_minutos"],
            "limite_entrada": limite_entrada.isoformat(),
            "es_descanso": turno["es_descanso"]
        }
    elif turno and turno["es_descanso"]:
        horario_info = {
            "es_descanso": True,
            "mensaje": "Día de descanso"
        }
    else:
        horario_info = {
            "mensaje": "Sin horario asignado",
            "hora_entrada_oficial": None,
            "hora_salida_oficial": None,
            "tolerancia_minutos": 15,
            "es_descanso": False
        }

    return {
        "empleado_id": empleado.id,
        "asistencia_id": asistencia.id,
        "estado_empleado": empleado.estado_actual,
        "estado_registro": asistencia.estado_registro,
        "mensaje": "Colaborador encontrado",
        "pase_espera_expira": asistencia.pase_espera_expira,
        "nombre_completo": empleado.nombre_completo,
        "numero_empleado": empleado.numero_empleado,
        "puesto": empleado.puesto,
        "horario": horario_info,
        "fuera_horario": fuera_horario,
        "ausencias_programadas": [
            {
                "tipo": ausencia.tipo_ausencia.value,
                "fecha_inicio": ausencia.fecha_inicio.isoformat(),
                "fecha_fin": ausencia.fecha_fin.isoformat(),
                "pagada": ausencia.pagada,
                "porcentaje_aportacion": ausencia.porcentaje_aportacion,
                "motivo": ausencia.motivo
            }
            for ausencia in ausencias
        ]
    }


def scan_employee(db: Session, gafete: str) -> RegistroAsistencia:
    now = utc_now()
    empleado = db.scalar(select(Empleado).where(Empleado.numero_empleado == gafete, Empleado.activo.is_(True)))
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado o inactivo")

    if empleado.estado_actual == EstadoEmpleado.LABORANDO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Colaborador está laborando; debe registrar salida")

    # Verificar si tiene ausencia aprobada hoy
    ausencia_hoy = verificar_ausencia_aprobada(db, empleado.id, now.date())
    if ausencia_hoy:
        # Si tiene ausencia aprobada, la entrada se toma como visita
        asistencia = get_or_create_today_asistencia(db, empleado)
        asistencia.hora_entrada_real = now
        asistencia.estado_registro = EstadoRegistro.VISITA_DESCANSO
        empleado.estado_actual = EstadoEmpleado.LABORANDO
        # Registrar evento de entrada como visita
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=now,
            observaciones=f"Visita durante {ausencia_hoy['tipo_ausencia']}"
        ))
        # Crear registro en tabla visitas para que aparezca en panel RRHH
        crear_visita(db, empleado.id, asistencia.id)
        db.add(ObservacionCaseta(
            asistencia_id=asistencia.id,
            tipo_observacion=f"Colaborador tiene {ausencia_hoy['tipo_ausencia']} aprobada. Entrada registrada como visita.",
            fecha_registro=now
        ))
        db.commit()
        db.refresh(asistencia)
        return asistencia

    # Si está en EN_ESPERA_PASE, verificar si tiene validación de supervisor
    if empleado.estado_actual == EstadoEmpleado.EN_ESPERA_PASE:
        asistencia = get_or_create_today_asistencia(db, empleado)
        if asistencia.validacion_supervisor:
            # Si ya tiene validación, permitir la entrada (hora ya fue registrada al llegar tarde)
            empleado.estado_actual = EstadoEmpleado.LABORANDO
            asistencia.estado_registro = EstadoRegistro.RETARDO_APROBADO
            # Registrar evento de entrada
            db.add(EventoAsistencia(
                empleado_id=empleado.id,
                asistencia_id=asistencia.id,
                tipo_evento=TipoEvento.ENTRADA,
                fecha_evento=now,
                observaciones="Entrada con pase digital aprobado"
            ))
            db.commit()
            db.refresh(asistencia)
            return asistencia
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Colaborador está en espera de pase digital; requiere aprobación de supervisor")

    asistencia = get_or_create_today_asistencia(db, empleado)
    turno = get_empleado_turno(db, empleado, now.weekday())

    if not turno or turno["es_descanso"] or not turno["hora_entrada_oficial"]:
        asistencia.hora_entrada_real = now
        asistencia.estado_registro = EstadoRegistro.VISITA_DESCANSO
        empleado.estado_actual = EstadoEmpleado.LABORANDO
        # Registrar evento de entrada
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=now,
            observaciones="Visita en día de descanso"
        ))
        # Crear registro en tabla visitas para que aparezca en panel RRHH
        crear_visita(db, empleado.id, asistencia.id)
        db.commit()
        db.refresh(asistencia)
        return asistencia

    # Detectar turno nocturno (hora de entrada después de mediodía, probablemente cruza medianoche)
    es_turno_nocturno = turno["hora_entrada_oficial"].hour >= 12

    # Para turnos nocturnos, asociar a la fecha de entrada real
    if es_turno_nocturno:
        asistencia.fecha_entrada_turno = now.date()

    hora_entrada_oficial = datetime.combine(now.date(), turno["hora_entrada_oficial"], tzinfo=now.tzinfo)
    hora_salida_oficial = datetime.combine(now.date(), turno["hora_salida_oficial"], tzinfo=now.tzinfo)
    tolerancia_entrada_previa = turno.get("tolerancia_entrada_previa_minutos", 15)
    tolerancia_entrada_posterior = turno.get("tolerancia_minutos", 15)
    
    # Calcular límites de tolerancia
    limite_entrada_previa = hora_entrada_oficial - timedelta(minutes=tolerancia_entrada_previa)
    limite_entrada_posterior = hora_entrada_oficial + timedelta(minutes=tolerancia_entrada_posterior)
    
    # Caso especial: Si entra después del fin del turno -> Registrar como visita
    if now > hora_salida_oficial:
        asistencia.hora_entrada_real = now
        asistencia.estado_registro = EstadoRegistro.VISITA_DESCANSO
        empleado.estado_actual = EstadoEmpleado.LABORANDO
        # Registrar evento de entrada como visita
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=now,
            observaciones="Visita después del fin del turno"
        ))
        # Crear registro en tabla visitas para que aparezca en panel RRHH
        crear_visita(db, empleado.id, asistencia.id)
        db.commit()
        db.refresh(asistencia)
        return asistencia
    
    # Caso 1: Llegó antes del inicio de turno (dentro de tolerancia previa) -> Registrar como visita
    if now < hora_entrada_oficial and now >= limite_entrada_previa:
        asistencia.hora_entrada_real = now
        asistencia.estado_registro = EstadoRegistro.VISITA_DESCANSO
        empleado.estado_actual = EstadoEmpleado.LABORANDO
        # Registrar evento de entrada como visita
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=now,
            observaciones="Visita antes de turno (dentro de tolerancia)"
        ))
        # Crear registro en tabla visitas para que aparezca en panel RRHH
        crear_visita(db, empleado.id, asistencia.id)
        db.commit()
        db.refresh(asistencia)
        return asistencia
    
    # Caso 2: Llegó después del inicio de turno (dentro de tolerancia posterior) -> Considerar como entrada a tiempo
    if now > hora_entrada_oficial and now <= limite_entrada_posterior:
        asistencia.hora_entrada_real = hora_entrada_oficial  # Registrar como si hubiera llegado a tiempo
        asistencia.estado_registro = EstadoRegistro.NORMAL
        empleado.estado_actual = EstadoEmpleado.LABORANDO
        # Registrar evento de entrada normal
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=now,
            observaciones="Entrada dentro de tolerancia posterior"
        ))
        db.commit()
        db.refresh(asistencia)
        return asistencia
    
    # Caso 3: Llegó muy tarde (fuera de tolerancia posterior) -> Requiere aprobación
    if now > limite_entrada_posterior and not asistencia.validacion_supervisor:
        asistencia.hora_entrada_real = now
        asistencia.pase_espera_expira = now + timedelta(minutes=30)
        asistencia.estado_registro = EstadoRegistro.INCIDENCIA
        empleado.estado_actual = EstadoEmpleado.EN_ESPERA_PASE
        # Registrar evento de entrada con retardo
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=now,
            observaciones="Entrada con retardo (fuera de tolerancia)"
        ))
        db.add(ObservacionCaseta(asistencia_id=asistencia.id, tipo_observacion="Retardo requiere pase digital", fecha_registro=now))
        db.commit()
        db.refresh(asistencia)
        return asistencia

    # Caso 4: Llegó muy temprano (fuera de tolerancia previa) -> Registrar como visita en día de descanso
    if now < limite_entrada_previa:
        asistencia.hora_entrada_real = now
        asistencia.estado_registro = EstadoRegistro.VISITA_DESCANSO
        empleado.estado_actual = EstadoEmpleado.LABORANDO
        # Registrar evento de entrada
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=now,
            observaciones="Visita muy temprana (fuera de tolerancia)"
        ))
        # Crear registro en tabla visitas para que aparezca en panel RRHH
        crear_visita(db, empleado.id, asistencia.id)
        db.commit()
        db.refresh(asistencia)
        return asistencia

    # Caso 5: Entrada exacta o dentro de tiempo normal
    asistencia.hora_entrada_real = now
    asistencia.estado_registro = EstadoRegistro.NORMAL
    empleado.estado_actual = EstadoEmpleado.LABORANDO
    # Registrar evento de entrada normal
    db.add(EventoAsistencia(
        empleado_id=empleado.id,
        asistencia_id=asistencia.id,
        tipo_evento=TipoEvento.ENTRADA,
        fecha_evento=now,
        observaciones="Entrada normal"
    ))
    db.commit()
    db.refresh(asistencia)
    return asistencia


def supervisor_can_access(db: Session, user: UsuarioSistema, empleado: Empleado) -> bool:
    return db.scalar(
        select(SupervisorDepartamento).where(
            SupervisorDepartamento.usuario_id == user.id,
            SupervisorDepartamento.departamento_id == empleado.departamento_id,
        )
    ) is not None


def approve_late_pass(db: Session, user: UsuarioSistema, asistencia_id: int) -> RegistroAsistencia:
    asistencia = db.get(RegistroAsistencia, asistencia_id)
    if not asistencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia no encontrada")
    empleado = db.get(Empleado, asistencia.empleado_id)
    if not supervisor_can_access(db, user, empleado):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Colaborador fuera de departamentos asignados")
    now = utc_now()

    # Manejar comparación de datetimes con/without timezone
    pase_expira = asistencia.pase_espera_expira

    if pase_expira:
        if pase_expira.tzinfo is None:
            # Si es naive, asumir que es hora local (UTC-06:00) y convertir a UTC
            from datetime import timezone, timedelta
            # Asumir que la hora guardada es UTC-06:00
            local_tz = timezone(timedelta(hours=-6))
            pase_expira = pase_expira.replace(tzinfo=local_tz)
        # Asegurar que now también tenga timezone
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

    # Verificar si el pase ha expirado (con margen de 1 minuto para evitar problemas de sincronización)
    from datetime import timedelta
    margen_expiracion = timedelta(minutes=1)

    if not pase_expira or now > (pase_expira + margen_expiracion):
        # Pase expirado: limpiar pase y marcar como FALTA
        asistencia.pase_espera_expira = None
        asistencia.estado_registro = EstadoRegistro.FALTA
        empleado.estado_actual = EstadoEmpleado.FUERA
        db.add(ObservacionCaseta(asistencia_id=asistencia.id, tipo_observacion="Pase expirado, marcado como falta", fecha_registro=now))
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pase expirado; marcado como falta")
    # Pase aprobado: no cambiar hora de entrada (ya fue registrada al llegar)
    # Cambiar estado del empleado a LABORANDO inmediatamente
    asistencia.validacion_supervisor = True
    asistencia.estado_registro = EstadoRegistro.RETARDO_APROBADO
    asistencia.pase_espera_expira = None  # Limpiar el pase expirado
    empleado.estado_actual = EstadoEmpleado.LABORANDO
    db.commit()
    db.refresh(asistencia)
    return asistencia
