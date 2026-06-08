from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.time import utc_now
from app.models import DetallePlantillaTurno, Empleado, EstadoEmpleado, EstadoRegistro, ObservacionCaseta, PlantillaTurno, RegistroAsistencia, RegistroAusencia, SupervisorDepartamento, TurnoHorario, UsuarioSistema


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
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"DEBUG - get_empleado_turno: empleado_id={empleado.id}, dia_semana={dia_semana}")
    
    # Primero buscar turnos individuales
    turno_individual = db.scalar(
        select(TurnoHorario).where(
            TurnoHorario.empleado_id == empleado.id,
            TurnoHorario.dia_semana == dia_semana
        )
    )
    if turno_individual:
        logger.info(f"DEBUG - Turno individual encontrado: es_descanso={turno_individual.es_descanso}, hora_entrada={turno_individual.hora_entrada_oficial}")
        return {
            "hora_entrada_oficial": turno_individual.hora_entrada_oficial,
            "hora_salida_oficial": turno_individual.hora_salida_oficial,
            "tolerancia_minutos": turno_individual.tolerancia_minutos,
            "es_descanso": turno_individual.es_descanso
        }
    
    # Si no tiene turnos individuales, buscar en plantilla
    if empleado.plantilla_turno_id:
        plantilla = db.get(PlantillaTurno, empleado.plantilla_turno_id)
        if plantilla:
            logger.info(f"DEBUG - Plantilla encontrada: {plantilla.nombre} (id={plantilla.id})")
            detalle = db.scalar(
                select(DetallePlantillaTurno).where(
                    DetallePlantillaTurno.plantilla_id == plantilla.id,
                    DetallePlantillaTurno.dia_semana == dia_semana
                )
            )
            if detalle:
                logger.info(f"DEBUG - Detalle plantilla encontrado: es_descanso={detalle.es_descanso}, hora_entrada={detalle.hora_entrada_oficial}")
                return {
                    "hora_entrada_oficial": detalle.hora_entrada_oficial,
                    "hora_salida_oficial": detalle.hora_salida_oficial,
                    "tolerancia_minutos": detalle.tolerancia_minutos,
                    "es_descanso": detalle.es_descanso
                }
            else:
                logger.info(f"DEBUG - No se encontró detalle para dia_semana={dia_semana} en plantilla")
        else:
            logger.info(f"DEBUG - Plantilla no encontrada con id={empleado.plantilla_turno_id}")
    else:
        logger.info(f"DEBUG - Empleado no tiene plantilla_turno_id")
    
    logger.info(f"DEBUG - No se encontró turno, retornando None")
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

    # Si está en EN_ESPERA_PASE, verificar si tiene validación de supervisor
    if empleado.estado_actual == EstadoEmpleado.EN_ESPERA_PASE:
        asistencia = get_or_create_today_asistencia(db, empleado)
        if asistencia.validacion_supervisor:
            # Si ya tiene validación, permitir la entrada (hora ya fue registrada al llegar tarde)
            empleado.estado_actual = EstadoEmpleado.LABORANDO
            asistencia.estado_registro = EstadoRegistro.RETARDO_APROBADO
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
        db.commit()
        db.refresh(asistencia)
        return asistencia

    # Detectar turno nocturno (hora de entrada después de mediodía, probablemente cruza medianoche)
    es_turno_nocturno = turno["hora_entrada_oficial"].hour >= 12

    # Para turnos nocturnos, asociar a la fecha de entrada real
    if es_turno_nocturno:
        asistencia.fecha_entrada_turno = now.date()

    limite = datetime.combine(now.date(), turno["hora_entrada_oficial"], tzinfo=now.tzinfo) + timedelta(minutes=turno["tolerancia_minutos"])
    if now > limite and not asistencia.validacion_supervisor:
        # Registrar hora de entrada real (para contar horas laboradas desde este momento)
        asistencia.hora_entrada_real = now
        asistencia.pase_espera_expira = now + timedelta(minutes=30)
        asistencia.estado_registro = EstadoRegistro.INCIDENCIA
        empleado.estado_actual = EstadoEmpleado.EN_ESPERA_PASE
        db.add(ObservacionCaseta(asistencia_id=asistencia.id, tipo_observacion="Retardo requiere pase digital", fecha_registro=now))
        db.commit()
        db.refresh(asistencia)
        return asistencia

    asistencia.hora_entrada_real = now
    asistencia.estado_registro = EstadoRegistro.NORMAL
    empleado.estado_actual = EstadoEmpleado.LABORANDO
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
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    asistencia = db.get(RegistroAsistencia, asistencia_id)
    if not asistencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia no encontrada")
    empleado = db.get(Empleado, asistencia.empleado_id)
    if not supervisor_can_access(db, user, empleado):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Colaborador fuera de departamentos asignados")
    now = utc_now()

    # Manejar comparación de datetimes con/without timezone
    pase_expira = asistencia.pase_espera_expira
    logger.info(f"DEBUG - Asistencia ID: {asistencia_id}")
    logger.info(f"DEBUG - pase_espera_expira original: {pase_expira}")
    logger.info(f"DEBUG - now original: {now}")
    logger.info(f"DEBUG - pase_expira.tzinfo: {pase_expira.tzinfo if pase_expira else None}")
    logger.info(f"DEBUG - now.tzinfo: {now.tzinfo}")

    if pase_expira:
        if pase_expira.tzinfo is None:
            # Si es naive, asumir que es hora local (UTC-06:00) y convertir a UTC
            from datetime import timezone, timedelta
            # Asumir que la hora guardada es UTC-06:00
            local_tz = timezone(timedelta(hours=-6))
            pase_expira = pase_expira.replace(tzinfo=local_tz)
            logger.info(f"DEBUG - pase_expira con timezone local: {pase_expira}")
        # Asegurar que now también tenga timezone
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
            logger.info(f"DEBUG - now con timezone: {now}")

    # Verificar si el pase ha expirado (con margen de 1 minuto para evitar problemas de sincronización)
    from datetime import timedelta
    margen_expiracion = timedelta(minutes=1)

    logger.info(f"DEBUG - Comparación: now={now}, pase_expira={pase_expira}, margen={margen_expiracion}")
    logger.info(f"DEBUG - now > (pase_expira + margen): {now > (pase_expira + margen_expiracion) if pase_expira else 'N/A'}")

    if not pase_expira or now > (pase_expira + margen_expiracion):
        # Pase expirado: limpiar pase y marcar como FALTA
        logger.info(f"DEBUG - Pase marcado como expirado")
        asistencia.pase_espera_expira = None
        asistencia.estado_registro = EstadoRegistro.FALTA
        empleado.estado_actual = EstadoEmpleado.FUERA
        db.add(ObservacionCaseta(asistencia_id=asistencia.id, tipo_observacion="Pase expirado, marcado como falta", fecha_registro=now))
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pase expirado; marcado como falta")
    # Pase aprobado: no cambiar hora de entrada (ya fue registrada al llegar)
    # Cambiar estado del empleado a LABORANDO inmediatamente
    logger.info(f"DEBUG - Pase aprobado exitosamente")
    asistencia.validacion_supervisor = True
    asistencia.estado_registro = EstadoRegistro.RETARDO_APROBADO
    asistencia.pase_espera_expira = None  # Limpiar el pase expirado
    empleado.estado_actual = EstadoEmpleado.LABORANDO
    db.commit()
    db.refresh(asistencia)
    return asistencia
