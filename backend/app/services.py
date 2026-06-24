from datetime import datetime, timedelta, date
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.time import utc_now
from app.models import BloqueHorasExtra, CorreccionManual, DetallePlantillaTurno, Empleado, EstadoEmpleado, EstadoRegistro, EstadoVisita, EventoAsistencia, ObservacionCaseta, PlantillaTurno, RegistroAsistencia, RegistroAusencia, SalidaTemporal, SupervisorDepartamento, TipoEvento, TipoSalida, TurnoHorario, UsuarioSistema, Visita


def crear_visita(db: Session, empleado_id: int, asistencia_id: int, hora_fin: datetime = None, minutos_duracion: int = None, motivo: str = None, hora_inicio: datetime = None) -> Visita:
    """Crea una visita para una entrada fuera de horario."""
    now = utc_now()
    
    # Usar hora_inicio proporcionado o now como default
    if hora_inicio is None:
        hora_inicio = now
    
    # Usar hora_inicio como fecha_visita para mantener consistencia
    fecha_visita = hora_inicio
    
    visita = Visita(
        empleado_id=empleado_id,
        asistencia_id=asistencia_id,
        fecha_visita=fecha_visita,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        minutos_duracion=minutos_duracion,
        estado=EstadoVisita.PENDIENTE,
        motivo=motivo
    )
    db.add(visita)
    db.commit()
    db.refresh(visita)
    return visita


def calcular_y_registrar_bloques_horas_extra(db: Session, asistencia: RegistroAsistencia, hora_entrada: datetime, hora_salida: datetime):
    """Calcula y registra bloques de horas extra separados (antes del inicio y después del fin del turno).
    Maneja 3 casos:
    1. Solo antes del turno: Bloque extra antes + Bloque laborado
    2. Solo después del turno: Bloque laborado + Bloque extra después
    3. Ambos extremos: Bloque extra antes + Bloque laborado + Bloque extra después
    """
    empleado = db.get(Empleado, asistencia.empleado_id)
    if not empleado:
        return
    
    # Obtener horario oficial del empleado
    turno = get_empleado_turno(db, empleado, asistencia.fecha_turno.weekday(), asistencia.fecha_turno)
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
    
    # Verificar si hay salida anticipada
    if hora_salida < hora_salida_oficial:
        asistencia.salida_anticipada = True
    
    # Verificar si toda la asistencia está fuera del horario oficial
    # Caso: Toda la asistencia está después del fin del turno -> Es visita, no hora extra
    if hora_entrada >= hora_salida_oficial:
        # No crear bloques extra, marcar como visita
        db.commit()
        return
    
    # Caso: Toda la asistencia está antes del inicio del turno -> Es visita, no hora extra
    if hora_salida <= hora_entrada_oficial:
        # No crear bloques extra, marcar como visita
        db.commit()
        return
    
    # Caso 1: Entrada antes del inicio del turno
    if hora_entrada < hora_entrada_oficial:
        # Bloque extra antes del inicio
        hora_fin_bloque_extra_antes = min(hora_salida, hora_entrada_oficial)
        minutos_extra_antes = int((hora_fin_bloque_extra_antes - hora_entrada).total_seconds() / 60)
        
        if minutos_extra_antes > 0:
            bloque = BloqueHorasExtra(
                asistencia_id=asistencia.id,
                tipo_bloque="ANTES_INICIO",
                hora_inicio=hora_entrada,
                hora_fin=hora_fin_bloque_extra_antes,
                minutos_extra=minutos_extra_antes
            )
            db.add(bloque)
    
    # Caso 2: Salida después del fin del turno
    if hora_salida > hora_salida_oficial:
        # Bloque extra después del fin
        hora_inicio_bloque_extra_despues = max(hora_entrada, hora_salida_oficial)
        minutos_extra_despues = int((hora_salida - hora_inicio_bloque_extra_despues).total_seconds() / 60)
        
        if minutos_extra_despues > 0:
            bloque = BloqueHorasExtra(
                asistencia_id=asistencia.id,
                tipo_bloque="DESPUES_FIN",
                hora_inicio=hora_inicio_bloque_extra_despues,
                hora_fin=hora_salida,
                minutos_extra=minutos_extra_despues
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
    
    FÓRMULA MAESTRA:
    - Suma de bloques de horas laboradas (dentro de horario oficial)
    - + Suma de tiempo de visitas validadas por RRHH
    - - Tiempo de permisos en horario laboral
    """
    now = utc_now()
    empleado = db.get(Empleado, empleado_id)
    turno = get_empleado_turno(db, empleado, fecha.weekday(), fecha)
    
    # Verificar si hay ausencia aprobada (vacaciones/incapacidad/permiso)
    ausencia = verificar_ausencia_aprobada(db, empleado_id, fecha)
    if ausencia:
        # Si hay ausencia, calcular horas según tipo y porcentaje
        tipo_ausencia = ausencia["tipo_ausencia"]
        pagada = ausencia["pagada"]
        porcentaje = ausencia["porcentaje_aportacion"]
        
        # Obtener turno para calcular horas del día
        minutos_completos = 0
        if turno and turno["hora_entrada_oficial"] and turno["hora_salida_oficial"]:
            hora_entrada = datetime.combine(fecha, turno["hora_entrada_oficial"], tzinfo=now.tzinfo)
            hora_salida = datetime.combine(fecha, turno["hora_salida_oficial"], tzinfo=now.tzinfo)
            minutos_completos = int((hora_salida - hora_entrada).total_seconds() / 60)
        
        # Calcular según tipo de ausencia
        if tipo_ausencia == "Vacaciones":
            minutos_laborados = minutos_completos  # 100%
        elif tipo_ausencia == "Incapacidad":
            minutos_laborados = int(minutos_completos * porcentaje / 100)
        elif tipo_ausencia == "Permiso":
            minutos_laborados = minutos_completos if pagada else 0
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
            "ausencia": ausencia,
            "correcciones": [
                {
                    "tipo": c.tipo_correccion.value,
                    "minutos": c.minutos_agregados,
                    "motivo": c.motivo
                }
                for c in correcciones
            ]
        }
    
    # FÓRMULA MAESTRA:
    # 1. Suma de bloques de horas laboradas (dentro de horario oficial)
    # 2. + Suma de tiempo de visitas validadas por RRHH
    # 3. - Tiempo de permisos en horario laboral
    
    # Obtener horario oficial del turno
    hora_entrada_oficial = None
    hora_salida_oficial = None
    if turno and turno["hora_entrada_oficial"] and turno["hora_salida_oficial"]:
        hora_entrada_oficial = datetime.combine(fecha, turno["hora_entrada_oficial"], tzinfo=now.tzinfo)
        hora_salida_oficial = datetime.combine(fecha, turno["hora_salida_oficial"], tzinfo=now.tzinfo)
    
    # 1. Calcular bloques de horas laboradas (dentro de horario oficial)
    minutos_laborados = 0
    
    # Obtener TODAS las asistencias del día (puede haber múltiples por entradas/salidas)
    asistencias = db.scalars(
        select(RegistroAsistencia).where(
            RegistroAsistencia.empleado_id == empleado_id,
            RegistroAsistencia.fecha_turno == fecha,
            RegistroAsistencia.hora_entrada_real.is_not(None),
            RegistroAsistencia.hora_salida_real.is_not(None)
        )
    ).all()
    
    for asistencia in asistencias:
        hora_entrada = asistencia.hora_entrada_real
        hora_salida = asistencia.hora_salida_real
        if hora_entrada.tzinfo is None:
            hora_entrada = hora_entrada.replace(tzinfo=now.tzinfo)
        if hora_salida.tzinfo is None:
            hora_salida = hora_salida.replace(tzinfo=now.tzinfo)
        
        if hora_entrada_oficial and hora_salida_oficial:
            # Calcular tiempo dentro del horario oficial
            inicio_laborado = max(hora_entrada, hora_entrada_oficial)
            fin_laborado = min(hora_salida, hora_salida_oficial)
            
            if fin_laborado > inicio_laborado:
                minutos_laborados += int((fin_laborado - inicio_laborado).total_seconds() / 60)
        else:
            # Sin horario oficial, contar todo
            minutos_laborados += int((hora_salida - hora_entrada).total_seconds() / 60)
    
    # 2. Sumar tiempo de visitas validadas por RRHH
    fecha_inicio = datetime.combine(fecha, datetime.min.time()).replace(tzinfo=now.tzinfo)
    fecha_fin = datetime.combine(fecha, datetime.max.time()).replace(tzinfo=now.tzinfo)
    
    visitas_pagadas = db.scalars(
        select(Visita).where(
            Visita.empleado_id == empleado_id,
            Visita.fecha_visita >= fecha_inicio,
            Visita.fecha_visita <= fecha_fin,
            Visita.estado == EstadoVisita.PAGADA,
            Visita.fecha_autorizacion.is_not(None)
        )
    ).all()
    
    for visita in visitas_pagadas:
        if visita.minutos_duracion:
            minutos_laborados += visita.minutos_duracion
    
    # 3. Restar tiempo de permisos en horario laboral
    # Obtener salidas temporales de permiso personal en el día
    fecha_inicio = datetime.combine(fecha, datetime.min.time()).replace(tzinfo=now.tzinfo)
    fecha_fin = datetime.combine(fecha, datetime.max.time()).replace(tzinfo=now.tzinfo)
    
    salidas_temporales = db.scalars(
        select(SalidaTemporal)
        .join(RegistroAsistencia, SalidaTemporal.asistencia_id == RegistroAsistencia.id)
        .where(
            RegistroAsistencia.empleado_id == empleado_id,
            RegistroAsistencia.fecha_turno == fecha,
            SalidaTemporal.tipo_salida == TipoSalida.PERMISO_PERSONAL,
            SalidaTemporal.descuenta_tiempo == True
        )
    ).all()
    
    minutos_permisos = 0
    for salida in salidas_temporales:
        if salida.minutos_descontados:
            minutos_permisos += salida.minutos_descontados
    
    minutos_laborados -= minutos_permisos
    
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
        "minutos_laborados": max(0, minutos_laborados),
        "minutos_extra": 0,
        "minutos_descanso": minutos_permisos,
        "ausencia": None,
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
        # Si la asistencia ya tiene salida registrada, crear una nueva para la nueva entrada
        if asistencia.hora_salida_real:
            nueva_asistencia = RegistroAsistencia(empleado_id=empleado.id, fecha_turno=now.date())
            db.add(nueva_asistencia)
            db.flush()
            return nueva_asistencia
        return asistencia
    asistencia = RegistroAsistencia(empleado_id=empleado.id, fecha_turno=now.date())
    db.add(asistencia)
    db.flush()
    return asistencia


def get_empleado_turno(db: Session, empleado: Empleado, dia_semana: int, fecha: date | None = None):
    """Obtiene el horario del empleado para un día específico.
    Primero busca en turnos individuales, si no tiene, busca en plantilla si está asignada.
    Si la plantilla es rotativa, alterna según semana par/impar."""
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
            # Si la plantilla es rotativa, determinar cuál usar según semana par/impar
            if plantilla.es_rotativa:
                if fecha is None:
                    fecha = utc_now().date()
                semana_numero = fecha.isocalendar()[1]  # Número de semana del año
                if semana_numero % 2 == 0:
                    plantilla = plantilla.plantilla_semana_par
                else:
                    plantilla = plantilla.plantilla_semana_impar
            
            # Si después de la rotación no hay plantilla válida, retornar None
            if not plantilla:
                return None
            
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
    turno = get_empleado_turno(db, empleado, asistencia.fecha_turno.weekday(), asistencia.fecha_turno)

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

    # Verificar pivote de 12 horas para detectar abandonos
    if empleado.estado_actual == EstadoEmpleado.LABORANDO:
        # Obtener asistencia del día actual
        asistencia_actual = db.scalar(
            select(RegistroAsistencia).where(
                RegistroAsistencia.empleado_id == empleado.id,
                RegistroAsistencia.fecha_turno == now.date()
            )
        )
        
        if asistencia_actual and asistencia_actual.hora_entrada_real and not asistencia_actual.hora_salida_real:
            # Obtener turno del empleado
            turno = get_empleado_turno(db, empleado, asistencia_actual.fecha_turno.weekday(), asistencia_actual.fecha_turno)
            
            if turno and turno["hora_salida_oficial"]:
                hora_salida_oficial = datetime.combine(
                    asistencia_actual.fecha_turno, 
                    turno["hora_salida_oficial"], 
                    tzinfo=now.tzinfo
                )
                
                # Verificar si han pasado más de 12 horas desde la hora oficial de fin de turno
                horas_pasadas = (now - hora_salida_oficial).total_seconds() / 3600
                
                if horas_pasadas > 12:
                    # Cierre por abandono
                    asistencia_actual.hora_salida_real = hora_salida_oficial
                    asistencia_actual.estado_registro = EstadoRegistro.INCIDENCIA
                    asistencia_actual.omision_salida_detectada = True
                    asistencia_actual.hora_cierre_automatico = now
                    empleado.estado_actual = EstadoEmpleado.FUERA
                    
                    # Registrar evento de cierre automático
                    db.add(EventoAsistencia(
                        empleado_id=empleado.id,
                        asistencia_id=asistencia_actual.id,
                        tipo_evento=TipoEvento.SALIDA,
                        fecha_evento=now,
                        observaciones="Cierre automático por abandono (más de 12 horas desde fin de turno)"
                    ))
                    
                    # Agregar observación
                    db.add(ObservacionCaseta(
                        asistencia_id=asistencia_actual.id,
                        tipo_observacion="Cierre automático por abandono - Marcado para RRHH",
                        fecha_registro=now
                    ))
                    
                    db.commit()
                    db.refresh(asistencia_actual)
                    # Permitir nueva entrada después del cierre automático
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Colaborador está laborando; debe registrar salida")
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Colaborador está laborando; debe registrar salida")
        else:
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
    turno = get_empleado_turno(db, empleado, asistencia.fecha_turno.weekday(), asistencia.fecha_turno)

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
    
    # Caso especial: Si entra después del fin del turno -> Registrar como entrada (se decidirá en salida)
    if now > hora_salida_oficial:
        asistencia.hora_entrada_real = now
        asistencia.estado_registro = EstadoRegistro.NORMAL
        empleado.estado_actual = EstadoEmpleado.LABORANDO
        # Registrar evento de entrada (se decidirá si es visita o extra en la salida)
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=now,
            observaciones="Entrada después del fin del turno (se decidirá en salida)"
        ))
        db.commit()
        db.refresh(asistencia)
        return asistencia
    
    # Caso 1: Llegó antes del inicio de turno (dentro de tolerancia previa) -> Registrar como entrada (se decidirá en salida)
    if now < hora_entrada_oficial and now >= limite_entrada_previa:
        asistencia.hora_entrada_real = now
        asistencia.estado_registro = EstadoRegistro.NORMAL
        empleado.estado_actual = EstadoEmpleado.LABORANDO
        # Registrar evento de entrada (se decidirá si es visita o extra en la salida)
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=now,
            observaciones="Entrada antes de turno (dentro de tolerancia, se decidirá en salida)"
        ))
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
