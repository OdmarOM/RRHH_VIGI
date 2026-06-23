from fastapi import APIRouter, Depends, HTTPException, status, Header, Form, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.core.time import utc_now
from app.models import Empleado, EstadoEmpleado, EstadoFila, EstadoRegistro, EstadoSalida, EstadoVisita, EventoAsistencia, FilaExterno, ObservacionCaseta, RegistroAsistencia, RegistroAusencia, SalidaTemporal, TipoEvento, TipoSalida, TurnoHorario, UsuarioSistema, Visita
from app.schemas import EntradaRequest, EventoAsistenciaOut, FilaExternoAsignar, FilaExternoCreate, FilaExternoOut, RegresoSalidaTemporalRequest, SalidaTemporalCreate, SalidaTemporalOut, ScanResponse, VisitaOut, VisitaUpdate
from app.services import calcular_horas_laboradas, crear_visita, get_employee_info, get_or_create_today_asistencia, scan_employee
from datetime import datetime
import shutil


router = APIRouter(prefix="/caseta", tags=["caseta"])


@router.get("/ausencias-activas/{empleado_id}")
def verificar_ausencias_activas(empleado_id: int, db: Session = Depends(get_db)):
    """Verifica si el empleado tiene ausencias programadas en la fecha actual"""
    now = utc_now()
    ausencias = db.scalars(
        select(RegistroAusencia).where(
            RegistroAusencia.empleado_id == empleado_id,
            RegistroAusencia.fecha_inicio <= now.date(),
            RegistroAusencia.fecha_fin >= now.date(),
            RegistroAusencia.aprobado_rrhh == True
        )
    ).all()
    return {
        "tiene_ausencia": len(ausencias) > 0,
        "ausencias": [
            {
                "tipo": ausencia.tipo_ausencia.value,
                "fecha_inicio": ausencia.fecha_inicio.isoformat(),
                "fecha_fin": ausencia.fecha_fin.isoformat(),
                "motivo": ausencia.motivo
            }
            for ausencia in ausencias
        ]
    }


@router.post("/escanear/{gafete}")
def escanear(gafete: str, db: Session = Depends(get_db)):
    return get_employee_info(db, gafete)


@router.get("/test-horario/{gafete}")
def test_horario(gafete: str, db: Session = Depends(get_db)):
    from app.services import get_empleado_turno, utc_now
    empleado = db.scalar(select(Empleado).where(Empleado.numero_empleado == gafete, Empleado.activo.is_(True)))
    if not empleado:
        return {"error": "Colaborador no encontrado"}
    now = utc_now()
    # Obtener asistencia del día actual para usar su fecha
    asistencia = db.scalar(
        select(RegistroAsistencia).where(
            RegistroAsistencia.empleado_id == empleado.id,
            RegistroAsistencia.fecha_turno == now.date()
        )
    )
    fecha_turno = asistencia.fecha_turno if asistencia else now.date()
    turno = get_empleado_turno(db, empleado, fecha_turno.weekday())
    return {
        "empleado_id": empleado.id,
        "numero_empleado": empleado.numero_empleado,
        "plantilla_turno_id": empleado.plantilla_turno_id,
        "dia_semana": fecha_turno.weekday(),
        "turno": turno
    }


@router.post("/entrada")
def entrada(payload: EntradaRequest, authorization: str | None = Header(None), db: Session = Depends(get_db)):
    empleado = db.get(Empleado, payload.empleado_id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    
    # Usar scan_employee para validar horarios y manejar retardos
    # scan_employee ya maneja ausencias programadas y las registra como visitas
    asistencia = scan_employee(db, empleado.numero_empleado)
    
    # Asignar vigilante si hay token
    vigilante_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        decoded = decode_token(token)
        if decoded:
            username = decoded.get("sub")
            vigilante = db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == username))
            if vigilante:
                vigilante_id = vigilante.id
                asistencia.vigilante_id = vigilante_id
                db.commit()
    
    # Agregar observaciones si las hay
    if payload.observaciones:
        for obs in payload.observaciones:
            db.add(ObservacionCaseta(
                asistencia_id=asistencia.id,
                tipo_observacion=obs,
                fecha_registro=utc_now()
            ))
        db.commit()
    
    # Determinar mensaje según estado del registro
    mensaje = "Entrada registrada"
    if asistencia.estado_registro == EstadoRegistro.INCIDENCIA:
        mensaje = "Retardo detectado, requiere aprobación de supervisor"
    elif asistencia.estado_registro == EstadoRegistro.VISITA_DESCANSO:
        mensaje = "Entrada registrada como VISITA (ausencia programada activa)"
    
    return {
        "ok": True,
        "estado_registro": asistencia.estado_registro,
        "mensaje": mensaje
    }


@router.post("/salida-temporal", response_model=SalidaTemporalOut)
def salida_temporal(payload: SalidaTemporalCreate, db: Session = Depends(get_db)):
    empleado = db.get(Empleado, payload.empleado_id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    if empleado.estado_actual != EstadoEmpleado.LABORANDO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Colaborador no está Laborando; no puede salir temporalmente")

    asistencia = db.scalar(
        select(RegistroAsistencia).where(
            RegistroAsistencia.empleado_id == payload.empleado_id,
            RegistroAsistencia.fecha_turno == utc_now().date()
        )
    )
    if not asistencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia del día no encontrada")

    # Solo los permisos personales descuentan tiempo laborado.
    # Mandados de trabajo y salidas a comer NO descuentan tiempo.
    descuenta_tiempo = payload.tipo_salida == TipoSalida.PERMISO_PERSONAL

    salida = SalidaTemporal(
        asistencia_id=asistencia.id,
        tipo_salida=payload.tipo_salida,
        hora_salida=utc_now(),
        descuenta_tiempo=descuenta_tiempo
    )
    empleado.estado_actual = EstadoEmpleado.SALIDA_TEMPORAL
    db.add(salida)
    db.flush()
    
    # Registrar evento de salida temporal
    db.add(EventoAsistencia(
        empleado_id=empleado.id,
        asistencia_id=asistencia.id,
        tipo_evento=TipoEvento.SALIDA_TEMPORAL,
        fecha_evento=salida.hora_salida,
        observaciones=f"Salida temporal: {payload.tipo_salida.value}",
        tipo_salida=payload.tipo_salida.value
    ))
    
    db.commit()
    db.refresh(salida)
    return salida


@router.post("/salida-temporal/{id}/regreso", response_model=SalidaTemporalOut)
def regreso_salida_temporal(id: int, db: Session = Depends(get_db)):
    from app.services import get_empleado_turno
    from datetime import timedelta

    salida = db.get(SalidaTemporal, id)
    if not salida:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salida temporal no encontrada")
    if salida.estado_salida == EstadoSalida.CERRADA:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Salida ya cerrada")

    now = utc_now()
    asistencia = salida.asistencia
    empleado = asistencia.empleado

    # Obtener horario oficial del empleado
    # Usar la fecha de la asistencia o la fecha actual si fecha_turno es None
    fecha_turno = asistencia.fecha_turno if asistencia.fecha_turno else now.date()
    turno = get_empleado_turno(db, empleado, fecha_turno.weekday())
    hora_salida_oficial = None
    if turno and turno["hora_salida_oficial"]:
        hora_salida_oficial = datetime.combine(
            fecha_turno,
            turno["hora_salida_oficial"],
            )
        # Asegurar que hora_salida_oficial tenga timezone
        if hora_salida_oficial.tzinfo is None:
            hora_salida_oficial = hora_salida_oficial.replace(tzinfo=now.tzinfo)

    # Calcular minutos descontados según tipo de salida
    if salida.tipo_salida == TipoSalida.PERMISO_PERSONAL:
        # Asegurar que salida.hora_salida tenga timezone
        hora_salida_con_tz = salida.hora_salida
        if hora_salida_con_tz.tzinfo is None:
            hora_salida_con_tz = hora_salida_con_tz.replace(tzinfo=now.tzinfo)
        
        # REGLA ANTIFRAUDE: Si el regreso es después de la hora de salida oficial, 
        # cortar el permiso personal exactamente en la hora oficial
        if hora_salida_oficial and now > hora_salida_oficial:
            salida.minutos_descontados = int((hora_salida_oficial - hora_salida_con_tz).total_seconds() / 60)
            salida.hora_regreso = hora_salida_oficial  # Cortar el permiso en la hora oficial
        else:
            salida.minutos_descontados = int((now - hora_salida_con_tz).total_seconds() / 60)
            salida.hora_regreso = now
    else:
        salida.minutos_descontados = 0
        salida.hora_regreso = now

    # Manejar retorno antes o después del fin de turno
    if hora_salida_oficial and now > hora_salida_oficial:
        # Retorno después del fin de turno
        # Cortar conteo a hora oficial
        # El regreso se registra como visita
        salida.hora_regreso = hora_salida_oficial
        salida.estado_salida = EstadoSalida.CERRADA

        # Crear nueva asistencia como visita
        nueva_visita = RegistroAsistencia(
            empleado_id=empleado.id,
            fecha_turno=now.date(),
            hora_entrada_real=now,
            estado_registro=EstadoRegistro.VISITA_DESCANSO
        )
        db.add(nueva_visita)
        db.flush()
        empleado.estado_actual = EstadoEmpleado.LABORANDO

        # Crear registro en tabla visitas para que aparezca en panel RRHH
        from app.services import crear_visita
        crear_visita(db, empleado.id, nueva_visita.id)

        db.add(ObservacionCaseta(
            asistencia_id=asistencia.id,
            tipo_observacion=f"Retorno después de fin de turno ({hora_salida_oficial.strftime('%H:%M')}). Creada visita nueva.",
            fecha_registro=now
        ))
    else:
        # Retorno antes del fin de turno
        # Reanudar conteo de horas
        salida.hora_regreso = now
        salida.estado_salida = EstadoSalida.CERRADA
        empleado.estado_actual = EstadoEmpleado.LABORANDO

    db.commit()
    db.refresh(salida)
    return salida


@router.post("/regreso-salida-temporal")
def regreso_salida_temporal_por_empleado(payload: RegresoSalidaTemporalRequest, db: Session = Depends(get_db)):
    from app.services import get_empleado_turno
    from datetime import timedelta

    empleado_id = payload.empleado_id

    empleado = db.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")

    if empleado.estado_actual != EstadoEmpleado.SALIDA_TEMPORAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Colaborador no está en salida temporal")

    # Buscar la salida temporal activa del colaborador
    salida = db.scalar(
        select(SalidaTemporal)
        .join(RegistroAsistencia, SalidaTemporal.asistencia_id == RegistroAsistencia.id)
        .where(RegistroAsistencia.empleado_id == empleado_id)
        .where(SalidaTemporal.estado_salida == EstadoSalida.ABIERTA)
        .order_by(SalidaTemporal.hora_salida.desc())
    )

    if not salida:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salida temporal activa no encontrada")

    # Obtener la asistencia asociada
    asistencia = db.get(RegistroAsistencia, salida.asistencia_id)
    if not asistencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia asociada no encontrada")

    now = utc_now()

    # Verificar si han pasado más de 5 horas desde la salida
    # Asegurar que hora_salida tenga timezone
    hora_salida = salida.hora_salida
    if hora_salida.tzinfo is None:
        hora_salida = hora_salida.replace(tzinfo=now.tzinfo)

    tiempo_transcurrido = now - hora_salida
    limite_5_horas = timedelta(hours=5)

    if tiempo_transcurrido > limite_5_horas:
        # Cerrar automáticamente la salida temporal después de 5 horas
        salida.hora_regreso = hora_salida + limite_5_horas
        salida.estado_salida = EstadoSalida.CERRADA
        salida.minutos_descontados = int(limite_5_horas.total_seconds() / 60) if salida.tipo_salida == TipoSalida.PERMISO_PERSONAL else 0

        # El colaborador queda en estado FUERA
        empleado.estado_actual = EstadoEmpleado.FUERA

        db.add(ObservacionCaseta(
            asistencia_id=asistencia.id,
            tipo_observacion=f"Salida temporal cerrada automáticamente después de 5 horas ({limite_5_horas}). Colaborador marcado como FUERA.",
            fecha_registro=now
        ))

        db.commit()
        db.refresh(salida)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Salida temporal cerrada automáticamente después de 5 horas. Colaborador marcado como FUERA. Debe escanear nuevamente para ingresar.")

    # Obtener horario oficial del empleado
    # Usar la fecha de la asistencia o la fecha actual si fecha_turno es None
    fecha_turno = asistencia.fecha_turno if asistencia.fecha_turno else now.date()
    turno = get_empleado_turno(db, empleado, fecha_turno.weekday())
    hora_salida_oficial = None
    if turno and turno["hora_salida_oficial"]:
        hora_salida_oficial = datetime.combine(
            fecha_turno,
            turno["hora_salida_oficial"],
            )
        # Asegurar que hora_salida_oficial tenga timezone
        if hora_salida_oficial.tzinfo is None:
            hora_salida_oficial = hora_salida_oficial.replace(tzinfo=now.tzinfo)

    # Calcular minutos descontados según tipo de salida
    if salida.tipo_salida == TipoSalida.PERMISO_PERSONAL:
        # Asegurar que salida.hora_salida tenga timezone
        hora_salida_con_tz = salida.hora_salida
        if hora_salida_con_tz.tzinfo is None:
            hora_salida_con_tz = hora_salida_con_tz.replace(tzinfo=now.tzinfo)
        
        # REGLA ANTIFRAUDE: Si el regreso es después de la hora de salida oficial, 
        # cortar el permiso personal exactamente en la hora oficial
        if hora_salida_oficial and now > hora_salida_oficial:
            salida.minutos_descontados = int((hora_salida_oficial - hora_salida_con_tz).total_seconds() / 60)
            salida.hora_regreso = hora_salida_oficial  # Cortar el permiso en la hora oficial
        else:
            salida.minutos_descontados = int((now - hora_salida_con_tz).total_seconds() / 60)
            salida.hora_regreso = now
    else:
        salida.minutos_descontados = 0
        salida.hora_regreso = now

    # Manejar retorno antes o después del fin de turno
    if hora_salida_oficial and now > hora_salida_oficial:
        # Retorno después del fin de turno
        salida.hora_regreso = hora_salida_oficial
        salida.estado_salida = EstadoSalida.CERRADA

        # Crear nueva asistencia como visita
        nueva_visita = RegistroAsistencia(
            empleado_id=empleado.id,
            fecha_turno=now.date(),
            hora_entrada_real=now,
            estado_registro=EstadoRegistro.VISITA_DESCANSO
        )
        db.add(nueva_visita)
        db.flush()
        empleado.estado_actual = EstadoEmpleado.LABORANDO

        # Crear registro en tabla visitas para que aparezca en panel RRHH
        # REGLA ANTIFRAUDE: El tiempo después del regreso es VISITA, no hora extra
        from app.services import crear_visita
        crear_visita(
            db=db,
            empleado_id=empleado.id,
            asistencia_id=nueva_visita.id,
            hora_inicio=now,
            motivo="Visita por reingreso post-turno (regreso después de hora oficial)"
        )

        # Registrar evento de regreso después de fin de turno
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=nueva_visita.id,
            tipo_evento=TipoEvento.REGRESO_SALIDA_TEMPORAL,
            fecha_evento=now,
            observaciones="Regreso después de fin de turno - Clasificado como visita (antifraude)"
        ))

        db.add(ObservacionCaseta(
            asistencia_id=asistencia.id,
            tipo_observacion=f"Retorno después de fin de turno ({hora_salida_oficial.strftime('%H:%M')}). Creada visita nueva.",
            fecha_registro=now
        ))
    else:
        # Retorno antes del fin de turno
        salida.hora_regreso = now
        salida.estado_salida = EstadoSalida.CERRADA
        empleado.estado_actual = EstadoEmpleado.LABORANDO
        
        # Registrar evento de regreso de salida temporal
        db.add(EventoAsistencia(
            empleado_id=empleado.id,
            asistencia_id=asistencia.id,
            tipo_evento=TipoEvento.REGRESO_SALIDA_TEMPORAL,
            fecha_evento=now,
            observaciones="Regreso de salida temporal"
        ))

    db.commit()
    db.refresh(salida)
    return salida


@router.post("/salida-final/{empleado_id}")
def salida_final(empleado_id: int, db: Session = Depends(get_db)):
    from app.services import get_empleado_turno
    from datetime import timedelta

    empleado = db.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")

    now = utc_now()

    # Buscar la asistencia activa del colaborador para el día actual (sin salida registrada)
    asistencia = db.scalar(
        select(RegistroAsistencia)
        .where(RegistroAsistencia.empleado_id == empleado_id)
        .where(RegistroAsistencia.fecha_turno == now.date())
        .where(RegistroAsistencia.hora_salida_real.is_(None))
        .order_by(RegistroAsistencia.hora_entrada_real.desc())
    )

    if not asistencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia del día no encontrada")

    asistencia.hora_salida_real = now
    
    # Asegurar que fecha_turno esté definida
    if not asistencia.fecha_turno:
        asistencia.fecha_turno = now.date()
    
    # Calcular bloques de horas extra si hay turno definido
    turno = get_empleado_turno(db, empleado, asistencia.fecha_turno.weekday())
    
    if turno and turno["hora_entrada_oficial"] and turno["hora_salida_oficial"]:
        from app.services import calcular_y_registrar_bloques_horas_extra
        from datetime import timedelta
        
        hora_entrada_oficial = datetime.combine(asistencia.fecha_turno if asistencia.fecha_turno else now.date(), turno["hora_entrada_oficial"])
        hora_salida_oficial = datetime.combine(asistencia.fecha_turno if asistencia.fecha_turno else now.date(), turno["hora_salida_oficial"])
        
        # Asegurar timezone
        if hora_entrada_oficial.tzinfo is None:
            hora_entrada_oficial = hora_entrada_oficial.replace(tzinfo=now.tzinfo)
        if hora_salida_oficial.tzinfo is None:
            hora_salida_oficial = hora_salida_oficial.replace(tzinfo=now.tzinfo)
        
        # Verificar si la asistencia completa está fuera del horario oficial
        if asistencia.hora_entrada_real and asistencia.hora_salida_real:
            hora_entrada = asistencia.hora_entrada_real
            hora_salida = asistencia.hora_salida_real
            if hora_entrada.tzinfo is None:
                hora_entrada = hora_entrada.replace(tzinfo=now.tzinfo)
            if hora_salida.tzinfo is None:
                hora_salida = hora_salida.replace(tzinfo=now.tzinfo)
            
            # Si toda la asistencia está después del fin del turno o antes del inicio, es una visita
            if hora_entrada >= hora_salida_oficial or hora_salida <= hora_entrada_oficial:
                # Verificar si ya existe una visita para esta asistencia
                visita_existente = db.scalar(
                    select(Visita).where(
                        Visita.empleado_id == empleado_id,
                        Visita.asistencia_id == asistencia.id
                    )
                )
                
                if not visita_existente:
                    from app.services import crear_visita
                    crear_visita(
                        db=db,
                        empleado_id=empleado_id,
                        asistencia_id=asistencia.id,
                        hora_fin=hora_salida,
                        minutos_duracion=int((hora_salida - hora_entrada).total_seconds() / 60),
                        motivo="Visita fuera de horario",
                        hora_inicio=hora_entrada
                    )
                    
                    # Marcar la asistencia como visita
                    asistencia.estado_registro = EstadoRegistro.VISITA_DESCANSO
        
        # Obtener todos los eventos de la asistencia para detectar múltiples bloques
        eventos = db.scalars(
            select(EventoAsistencia).where(
                EventoAsistencia.asistencia_id == asistencia.id
            ).order_by(EventoAsistencia.fecha_evento)
        ).all()
        
        # Agrupar eventos en pares de entrada/salida
        bloques = []
        i = 0
        while i < len(eventos):
            if eventos[i].tipo_evento == TipoEvento.ENTRADA:
                entrada = eventos[i].fecha_evento
                # Buscar la siguiente salida
                j = i + 1
                while j < len(eventos) and eventos[j].tipo_evento != TipoEvento.SALIDA:
                    j += 1
                if j < len(eventos):
                    salida = eventos[j].fecha_evento
                    bloques.append((entrada, salida))
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1
        
        # Para cada bloque, verificar si está fuera de horario y crear visita si es necesario
        for idx, (entrada, salida) in enumerate(bloques):
            entrada_fuera_horario = (
                entrada < hora_entrada_oficial or
                entrada > hora_salida_oficial
            )
            
            salida_fuera_horario = (
                salida < hora_entrada_oficial or
                salida > hora_salida_oficial
            )
            
            if entrada_fuera_horario and salida_fuera_horario:
                # Bloque completamente fuera de horario = Visita
                # Verificar si ya existe una visita para este bloque
                visita_existente = db.scalar(
                    select(Visita).where(
                        Visita.empleado_id == empleado_id,
                        Visita.asistencia_id == asistencia.id,
                        Visita.hora_inicio == entrada
                    )
                )
                
                if not visita_existente:
                    from app.services import crear_visita
                    crear_visita(
                        db=db,
                        empleado_id=empleado_id,
                        asistencia_id=asistencia.id,
                        hora_fin=salida,
                        minutos_duracion=int((salida - entrada).total_seconds() / 60),
                        motivo="Visita fuera de horario",
                        hora_inicio=entrada
                    )
        
        # Calcular bloques de horas extra
        calcular_y_registrar_bloques_horas_extra(db, asistencia, asistencia.hora_entrada_real, now)
    else:
        # Si no hay turno definido, marcar como visita
        visita_pendiente = db.scalar(
            select(Visita).where(
                Visita.empleado_id == empleado_id,
                Visita.estado == EstadoVisita.PENDIENTE,
                Visita.hora_fin.is_(None)
            ).order_by(Visita.fecha_visita.desc())
        )
        
        if visita_pendiente:
            visita_pendiente.hora_fin = now
            visita_pendiente.minutos_duracion = int((now - visita_pendiente.hora_inicio).total_seconds() / 60)
            visita_pendiente.motivo = visita_pendiente.motivo or "Visita sin turno definido"
            db.add(visita_pendiente)
        else:
            from app.services import crear_visita
            crear_visita(
                db=db,
                empleado_id=empleado_id,
                asistencia_id=asistencia.id,
                hora_fin=now,
                minutos_duracion=int((now - asistencia.hora_entrada_real).total_seconds() / 60),
                motivo="Visita sin turno definido"
            )
        
        db.add(ObservacionCaseta(
            asistencia_id=asistencia.id,
            tipo_observacion="Salida sin turno definido. Registrado como visita.",
            fecha_registro=now
        ))
    
    empleado.estado_actual = EstadoEmpleado.FUERA
    # Registrar evento de salida
    db.add(EventoAsistencia(
        empleado_id=empleado_id,
        asistencia_id=asistencia.id,
        tipo_evento=TipoEvento.SALIDA,
        fecha_evento=now,
        observaciones="Salida final"
    ))
    db.commit()
    return {"ok": True}


@router.post("/fila-externos", response_model=FilaExternoOut)
def crear_externo(
    tipo_visitante: str = Form(...),
    nombre_empresa: str = Form(...),
    chofer: str | None = Form(None),
    placa: str | None = Form(None),
    latitud: float | None = Form(None),
    longitud: float | None = Form(None),
    fotos: list[UploadFile] = File(default=[]),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    from app.models import EvidenciaFotografica
    import os
    from pathlib import Path
    
    vigilante_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        decoded = decode_token(token)
        if decoded:
            username = decoded.get("sub")
            vigilante = db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == username))
            if vigilante:
                vigilante_id = vigilante.id
    
    externo = FilaExterno(
        tipo_visitante=tipo_visitante,
        nombre_empresa=nombre_empresa,
        chofer=chofer,
        placa=placa,
        vigilante_id=vigilante_id,
        hora_llegada=utc_now(),
        latitud=latitud,
        longitud=longitud
    )
    db.add(externo)
    db.commit()
    db.refresh(externo)
    
    # Crear directorio para fotos si no existe
    upload_dir = Path("uploads/evidencias")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar fotos si existen
    for foto in fotos:
        # Generar nombre único para el archivo
        timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
        filename = f"externo_{externo.id}_{timestamp}_{foto.filename}"
        file_path = upload_dir / filename
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        
        # Crear registro en base de datos
        evidencia = EvidenciaFotografica(
            referencia_id=externo.id,
            referencia_tipo="fila_externo",
            ruta_archivo=str(file_path),
            fecha_captura=utc_now()
        )
        db.add(evidencia)
    
    db.commit()
    db.refresh(externo)
    return externo


@router.post("/fila-externos/{id}/asignar", response_model=FilaExternoOut)
def asignar_anden(id: int, payload: FilaExternoAsignar, db: Session = Depends(get_db)):
    externo = db.get(FilaExterno, id)
    if not externo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitante no encontrado")
    
    # Validar que el andén no esté ocupado
    anden_ocupado = db.scalar(
        select(FilaExterno).where(
            FilaExterno.anden_asignado == payload.anden_asignado,
            FilaExterno.estado_fila == EstadoFila.ADENTRO_VERDE,
            FilaExterno.id != id
        )
    )
    if anden_ocupado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El andén {payload.anden_asignado} ya está ocupado")
    
    externo.anden_asignado = payload.anden_asignado
    externo.estado_fila = EstadoFila.ADENTRO_VERDE
    # Registrar hora de entrada al almacén si no está registrada
    if not externo.hora_entrada_almacen:
        externo.hora_entrada_almacen = utc_now()
    db.commit()
    db.refresh(externo)
    return externo


@router.get("/fila-externos", response_model=list[FilaExternoOut])
def listar_externos(db: Session = Depends(get_db)):
    return db.scalars(select(FilaExterno).where(FilaExterno.estado_fila != EstadoFila.RETIRADO).order_by(FilaExterno.hora_llegada.desc())).all()


@router.post("/fila-externos/{id}/agregar-evidencias")
def agregar_evidencia_externo(
    id: int,
    fotos: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Agrega evidencias fotográficas a un externo existente"""
    from app.models import EvidenciaFotografica
    from pathlib import Path
    
    externo = db.get(FilaExterno, id)
    if not externo:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    
    # Crear directorio para fotos si no existe
    upload_dir = Path("uploads/evidencias")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar fotos
    for foto in fotos:
        # Generar nombre único para el archivo
        timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
        filename = f"externo_{externo.id}_{timestamp}_{foto.filename}"
        file_path = upload_dir / filename
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        
        # Crear registro en base de datos
        evidencia = EvidenciaFotografica(
            referencia_id=externo.id,
            referencia_tipo="fila_externo",
            ruta_archivo=str(file_path),
            fecha_captura=utc_now()
        )
        db.add(evidencia)
    
    db.commit()
    
    return {
        "message": f"Se agregaron {len(fotos)} evidencia(s) fotográfica(s)",
        "agregados": len(fotos)
    }


@router.get("/fila-externos/{id}/evidencias")
def obtener_evidencias_externo(id: int, db: Session = Depends(get_db)):
    """Obtiene las evidencias fotográficas de un visitante externo"""
    from app.models import EvidenciaFotografica
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    evidencias = db.scalars(
        select(EvidenciaFotografica).where(
            EvidenciaFotografica.referencia_id == id,
            EvidenciaFotografica.referencia_tipo == "fila_externo"
        )
    ).all()
    
    return [
        {
            "id": e.id,
            "ruta_archivo": e.ruta_archivo,
            "fecha_captura": e.fecha_captura.isoformat()
        }
        for e in evidencias
    ]


@router.get("/fila-externos/{id}/evidencias/{evidencia_id}")
def descargar_evidencia(id: int, evidencia_id: int, db: Session = Depends(get_db)):
    """Descarga una evidencia fotográfica específica"""
    from app.models import EvidenciaFotografica
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    evidencia = db.scalar(
        select(EvidenciaFotografica).where(
            EvidenciaFotografica.id == evidencia_id,
            EvidenciaFotografica.referencia_id == id,
            EvidenciaFotografica.referencia_tipo == "fila_externo"
        )
    )
    
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    
    file_path = Path(evidencia.ruta_archivo)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(file_path)


@router.post("/limpiar-evidencias-antiguas")
def limpiar_evidencias_antiguas(db: Session = Depends(get_db)):
    """Elimina evidencias fotográficas con más de 1 mes de antigüedad"""
    from app.models import EvidenciaFotografica
    from datetime import timedelta
    from pathlib import Path
    import os
    
    now = utc_now()
    limite = now - timedelta(days=30)
    
    # Buscar evidencias antiguas
    evidencias_antiguas = db.scalars(
        select(EvidenciaFotografica).where(
            EvidenciaFotografica.fecha_captura < limite
        )
    ).all()
    
    eliminados = 0
    for evidencia in evidencias_antiguas:
        file_path = Path(evidencia.ruta_archivo)
        
        # Eliminar archivo del sistema
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error al eliminar archivo {file_path}: {e}")
        
        # Eliminar registro de base de datos
        db.delete(evidencia)
        eliminados += 1
    
    db.commit()
    
    return {
        "message": f"Se eliminaron {eliminados} evidencias fotográficas antiguas",
        "eliminados": eliminados
    }


@router.put("/fila-externos/{id}/salida", response_model=FilaExternoOut)
def salida_externo(id: int, db: Session = Depends(get_db)):
    externo = db.get(FilaExterno, id)
    if not externo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitante no encontrado")
    externo.estado_fila = EstadoFila.RETIRADO
    externo.hora_salida = utc_now()
    db.commit()
    db.refresh(externo)
    return externo


@router.put("/fila-externos/{id}/entrada-directa", response_model=FilaExternoOut)
def entrada_directa_externo(id: int, db: Session = Depends(get_db)):
    """Entrada directa para proveedores de servicio sin asignación de andén"""
    externo = db.get(FilaExterno, id)
    if not externo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitante no encontrado")
    externo.estado_fila = EstadoFila.ADENTRO_VERDE
    externo.anden_asignado = None  # Sin andén para proveedores
    db.commit()
    db.refresh(externo)
    return externo


@router.get("/eventos/{empleado_id}", response_model=list[EventoAsistenciaOut])
def obtener_eventos_empleado(empleado_id: int, fecha_inicio: str | None = None, fecha_fin: str | None = None, db: Session = Depends(get_db)):
    """Obtiene los eventos de asistencia de un empleado en un rango de fechas"""
    from datetime import date
    
    query = select(EventoAsistencia).where(EventoAsistencia.empleado_id == empleado_id)
    
    if fecha_inicio:
        try:
            fecha_inicio_dt = date.fromisoformat(fecha_inicio)
            query = query.where(EventoAsistencia.fecha_evento >= datetime.combine(fecha_inicio_dt, datetime.min.time()))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de fecha_inicio inválido (debe ser YYYY-MM-DD)")
    
    if fecha_fin:
        try:
            fecha_fin_dt = date.fromisoformat(fecha_fin)
            query = query.where(EventoAsistencia.fecha_evento <= datetime.combine(fecha_fin_dt, datetime.max.time()))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de fecha_fin inválido (debe ser YYYY-MM-DD)")
    
    eventos = db.scalars(query.order_by(EventoAsistencia.fecha_evento.desc())).all()
    return eventos


@router.get("/horas-laboradas/{empleado_id}")
def calcular_horas_por_fecha(empleado_id: int, fecha: str, db: Session = Depends(get_db)):
    """Calcula las horas laboradas de un empleado en una fecha específica basándose en eventos"""
    from datetime import date
    
    try:
        fecha_dt = date.fromisoformat(fecha)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de fecha inválido (debe ser YYYY-MM-DD)")
    
    resultado = calcular_horas_laboradas(db, empleado_id, fecha_dt)
    return resultado


@router.get("/historial")
def historial_accesos(fecha_inicio: str | None = None, fecha_fin: str | None = None, empleado_id: int | None = None, db: Session = Depends(get_db)):
    from datetime import date
    
    query = select(RegistroAsistencia).join(Empleado)
    
    if fecha_inicio:
        try:
            fecha_inicio_dt = date.fromisoformat(fecha_inicio)
            query = query.where(RegistroAsistencia.fecha_turno >= fecha_inicio_dt)
        except ValueError:
            pass
    
    if fecha_fin:
        try:
            fecha_fin_dt = date.fromisoformat(fecha_fin)
            query = query.where(RegistroAsistencia.fecha_turno <= fecha_fin_dt)
        except ValueError:
            pass
    
    if empleado_id:
        query = query.where(RegistroAsistencia.empleado_id == empleado_id)
    
    asistencias = db.scalars(query.order_by(RegistroAsistencia.fecha_turno.desc(), RegistroAsistencia.hora_entrada_real.desc())).all()
    
    return [
        {
            "id": a.id,
            "empleado_id": a.empleado_id,
            "nombre_empleado": a.empleado.nombre_completo,
            "numero_empleado": a.empleado.numero_empleado,
            "puesto": a.empleado.puesto,
            "departamento": a.empleado.departamento.nombre,
            "fecha_turno": a.fecha_turno.isoformat(),
            "hora_entrada_real": a.hora_entrada_real.isoformat() if a.hora_entrada_real else None,
            "hora_salida_real": a.hora_salida_real.isoformat() if a.hora_salida_real else None,
            "estado_registro": a.estado_registro,
            "estado_empleado": a.empleado.estado_actual,
            "minutos_extra_calculados": a.minutos_extra_calculados,
            "validacion_supervisor": a.validacion_supervisor,
            "validacion_rrhh": a.validacion_rrhh,
            "autorizacion_horas_extra_rrhh": a.autorizacion_horas_extra_rrhh
        }
        for a in asistencias
    ]


@router.get("/historial-externos")
def historial_externos(fecha_inicio: str | None = None, fecha_fin: str | None = None, db: Session = Depends(get_db)):
    from datetime import date

    query = select(FilaExterno)

    if fecha_inicio:
        try:
            fecha_inicio_dt = date.fromisoformat(fecha_inicio)
            query = query.where(FilaExterno.hora_llegada >= datetime.combine(fecha_inicio_dt, datetime.min.time(), tzinfo=utc_now().tzinfo))
        except ValueError:
            pass

    if fecha_fin:
        try:
            fecha_fin_dt = date.fromisoformat(fecha_fin)
            query = query.where(FilaExterno.hora_llegada <= datetime.combine(fecha_fin_dt, datetime.max.time(), tzinfo=utc_now().tzinfo))
        except ValueError:
            pass

    externos = db.scalars(query.order_by(FilaExterno.hora_llegada.desc())).all()

    return [
        {
            "id": e.id,
            "tipo_visitante": e.tipo_visitante,
            "nombre_empresa": e.nombre_empresa,
            "chofer": e.chofer,
            "placa": e.placa,
            "estado_fila": e.estado_fila,
            "anden_asignado": e.anden_asignado,
            "hora_llegada": e.hora_llegada.isoformat(),
            "hora_salida": e.hora_salida.isoformat() if e.hora_salida else None
        }
        for e in externos
    ]


@router.post("/procesar-omisiones-salida")
def procesar_omisiones_salida(db: Session = Depends(get_db)):
    """Procesa registros sin salida después de 5 horas del fin de turno oficial"""
    from app.services import get_empleado_turno
    from datetime import timedelta
    now = utc_now()

    # Buscar registros con entrada pero sin salida
    registros_sin_salida = db.scalars(
        select(RegistroAsistencia).where(
            RegistroAsistencia.hora_entrada_real.is_not(None),
            RegistroAsistencia.hora_salida_real.is_(None),
            RegistroAsistencia.omision_salida_detectada == False
        )
    ).all()

    procesados = []
    for registro in registros_sin_salida:
        empleado = db.get(Empleado, registro.empleado_id)
        if not empleado:
            continue

        # Obtener el horario oficial del empleado
        turno = get_empleado_turno(db, empleado, registro.fecha_turno.weekday())
        if not turno or not turno["hora_salida_oficial"]:
            continue

        # Calcular hora oficial de salida
        hora_salida_oficial = datetime.combine(
            registro.fecha_turno,
            turno["hora_salida_oficial"],
            tzinfo=now.tzinfo
        )

        # Verificar si han pasado 5 horas desde el fin de turno
        limite_cierre = hora_salida_oficial + timedelta(hours=5)
        if now >= limite_cierre:
            # Cerrar el registro automáticamente
            registro.hora_salida_real = hora_salida_oficial
            registro.omision_salida_detectada = True
            registro.hora_cierre_automatico = now
            registro.estado_registro = EstadoRegistro.INCIDENCIA
            empleado.estado_actual = EstadoEmpleado.FUERA

            # Agregar observación
            db.add(ObservacionCaseta(
                asistencia_id=registro.id,
                tipo_observacion="Omisión de salida detectada - Cierre automático",
                fecha_registro=now
            ))

            procesados.append({
                "empleado_id": empleado.id,
                "numero_empleado": empleado.numero_empleado,
                "nombre": empleado.nombre_completo,
                "fecha_turno": registro.fecha_turno.isoformat(),
                "hora_salida_oficial": hora_salida_oficial.isoformat(),
                "hora_cierre_automatico": now.isoformat()
            })

    db.commit()
    return {
        "procesados": len(procesados),
        "registros": procesados
    }


@router.post("/procesar-salidas-temporales-expiradas")
def procesar_salidas_temporales_expiradas(db: Session = Depends(get_db)):
    """Cierra automáticamente salidas temporales de permisos después de 5 horas"""
    from datetime import timedelta
    now = utc_now()

    # Buscar salidas temporales abiertas de permisos personales
    salidas_abiertas = db.scalars(
        select(SalidaTemporal).where(
            SalidaTemporal.estado_salida == EstadoSalida.ABIERTA,
            SalidaTemporal.tipo_salida == TipoSalida.PERMISO_PERSONAL
        )
    ).all()

    procesadas = []
    for salida in salidas_abiertas:
        # Verificar si han pasado 5 horas desde la salida
        limite_cierre = salida.hora_salida + timedelta(hours=5)
        if now >= limite_cierre:
            # Cerrar la salida temporal automáticamente
            salida.hora_regreso = salida.hora_salida + timedelta(hours=5)
            salida.minutos_descontados = 300  # 5 horas = 300 minutos
            salida.estado_salida = EstadoSalida.CERRADA

            # Cambiar estado del empleado a FUERA
            empleado = salida.asistencia.empleado
            empleado.estado_actual = EstadoEmpleado.FUERA

            # Agregar observación
            db.add(ObservacionCaseta(
                asistencia_id=salida.asistencia_id,
                tipo_observacion="Salida temporal de permiso expirada (5 horas) - Cierre automático",
                fecha_registro=now
            ))

            procesadas.append({
                "salida_id": salida.id,
                "empleado_id": empleado.id,
                "numero_empleado": empleado.numero_empleado,
                "nombre": empleado.nombre_completo,
                "hora_salida": salida.hora_salida.isoformat(),
                "hora_cierre_automatico": now.isoformat()
            })

    db.commit()
    return {
        "procesadas": len(procesadas),
        "salidas": procesadas
    }


@router.get("/visitas", response_model=list[VisitaOut])
def obtener_visitas(fecha_inicio: str | None = None, fecha_fin: str | None = None, empleado_id: int | None = None, db: Session = Depends(get_db)):
    """Obtiene todas las visitas en un rango de fechas y opcionalmente por empleado"""
    from datetime import date
    
    query = select(Visita)
    
    if fecha_inicio:
        try:
            fecha_inicio_dt = date.fromisoformat(fecha_inicio)
            query = query.where(Visita.fecha_visita >= datetime.combine(fecha_inicio_dt, datetime.min.time()))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de fecha_inicio inválido")
    
    if fecha_fin:
        try:
            fecha_fin_dt = date.fromisoformat(fecha_fin)
            query = query.where(Visita.fecha_visita <= datetime.combine(fecha_fin_dt, datetime.max.time()))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de fecha_fin inválido")
    
    if empleado_id:
        query = query.where(Visita.empleado_id == empleado_id)
    
    # Solo mostrar visitas concluidas (con hora_fin)
    query = query.where(Visita.hora_fin.is_not(None))
    
    visitas = db.scalars(query.order_by(Visita.fecha_visita.desc())).all()
    return visitas


@router.put("/visitas/{visita_id}", response_model=VisitaOut)
def actualizar_visita(visita_id: int, request: VisitaUpdate, db: Session = Depends(get_db)):
    """Actualiza el estado de una visita (solo RRHH)"""
    visita = db.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visita no encontrada")
    
    visita.estado = request.estado
    visita.motivo = request.motivo
    
    if request.estado in [EstadoVisita.PAGADA, EstadoVisita.NO_PAGADA]:
        visita.fecha_autorizacion = utc_now()
    
    db.commit()
    db.refresh(visita)
    return visita


@router.put("/visitas/{visita_id}/duracion", response_model=VisitaOut)
def actualizar_duracion_visita(visita_id: int, minutos: int, db: Session = Depends(get_db)):
    """Actualiza la duración de una visita (solo RRHH)"""
    visita = db.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visita no encontrada")
    
    visita.minutos_duracion = minutos
    db.commit()
    db.refresh(visita)
    return visita
