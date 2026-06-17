from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.core.database import get_db
from app.models import BloqueHorasExtra, DetallePlantillaTurno, Empleado, EstadoEmpleado, PlantillaTurno, RegistroAsistencia, RolNombre, SupervisorDepartamento, TurnoHorario, UsuarioSistema
from app.schemas import AsistenciaOut, DetallePlantillaOut, EmpleadoOut, PlantillaTurnoOut, TurnoOut, TurnoCreate, TurnoDescansoUpdate
from app.services import approve_late_pass


router = APIRouter(tags=["supervisor"])


@router.get("/incidencias", response_model=list[dict])
def incidencias(
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR, RolNombre.RRHH, RolNombre.ADMINISTRADOR, RolNombre.SUPERUSUARIO)),
):
    from app.core.time import utc_now
    from datetime import timedelta

    # Si es supervisor, filtrar por sus departamentos asignados
    # Si es RRHH/Admin/Superusuario, ver todos los empleados
    if user.rol == RolNombre.SUPERVISOR:
        departamentos = select(SupervisorDepartamento.departamento_id).where(SupervisorDepartamento.usuario_id == user.id)
        empleados_ids = db.scalars(select(Empleado.id).where(Empleado.departamento_id.in_(departamentos))).all()
    else:
        # RRHH, Admin, Superusuario ven todos los empleados
        empleados_ids = db.scalars(select(Empleado.id).where(Empleado.activo == True)).all()

    now = utc_now()

    # Filtrar pases que no han expirado (pase_espera_expira > now)
    # Hacer join con Empleado para obtener el nombre
    resultados = db.execute(
        select(RegistroAsistencia, Empleado)
        .join(Empleado, RegistroAsistencia.empleado_id == Empleado.id)
        .where(
            RegistroAsistencia.empleado_id.in_(empleados_ids),
            RegistroAsistencia.pase_espera_expira.is_not(None),
            RegistroAsistencia.pase_espera_expira > now
        )
        .order_by(RegistroAsistencia.pase_espera_expira.asc())
    ).all()

    # Formatear respuesta con nombre del colaborador
    return [
        {
            "id": asistencia.id,
            "empleado_id": asistencia.empleado_id,
            "nombre_empleado": empleado.nombre_completo,
            "numero_empleado": empleado.numero_empleado,
            "fecha_turno": asistencia.fecha_turno,
            "hora_entrada_real": asistencia.hora_entrada_real,
            "hora_salida_real": asistencia.hora_salida_real,
            "estado_registro": asistencia.estado_registro,
            "pase_espera_expira": asistencia.pase_espera_expira,
            "validacion_supervisor": asistencia.validacion_supervisor,
            "validacion_rrhh": asistencia.validacion_rrhh
        }
        for asistencia, empleado in resultados
    ]


@router.get("/incidencias/horas-extra", response_model=list[dict])
def incidencias_horas_extra(
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR)),
):
    """Lista los bloques de horas extra pendientes de validación por el supervisor
    para los colaboradores de sus departamentos."""
    departamentos = select(SupervisorDepartamento.departamento_id).where(SupervisorDepartamento.usuario_id == user.id)
    empleados_ids = db.scalars(select(Empleado.id).where(Empleado.departamento_id.in_(departamentos))).all()

    # Obtener bloques pendientes de validación de supervisor unidos con asistencia y empleado
    resultados = db.execute(
        select(BloqueHorasExtra, RegistroAsistencia, Empleado)
        .join(RegistroAsistencia, BloqueHorasExtra.asistencia_id == RegistroAsistencia.id)
        .join(Empleado, RegistroAsistencia.empleado_id == Empleado.id)
        .where(
            RegistroAsistencia.empleado_id.in_(empleados_ids),
            BloqueHorasExtra.validacion_supervisor.is_(False)
        )
        .order_by(RegistroAsistencia.fecha_turno.desc(), BloqueHorasExtra.hora_inicio.asc())
    ).all()

    return [
        {
            "bloque_id": bloque.id,
            "asistencia_id": asistencia.id,
            "empleado_id": asistencia.empleado_id,
            "nombre_empleado": empleado.nombre_completo,
            "numero_empleado": empleado.numero_empleado,
            "fecha_turno": asistencia.fecha_turno,
            "tipo_bloque": bloque.tipo_bloque,
            "hora_inicio": bloque.hora_inicio,
            "hora_fin": bloque.hora_fin,
            "minutos_extra": bloque.minutos_extra,
            "validacion_supervisor": bloque.validacion_supervisor,
            "validacion_rrhh": bloque.validacion_rrhh
        }
        for bloque, asistencia, empleado in resultados
    ]


@router.put("/incidencias/horas-extra/bloque/{bloque_id}/validar")
def validar_bloque_horas_extra(
    bloque_id: int,
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR)),
):
    """El supervisor valida un bloque individual de horas extra de un colaborador
    de su departamento. RRHH terminará de validar desde el panel de administración."""
    departamentos = select(SupervisorDepartamento.departamento_id).where(SupervisorDepartamento.usuario_id == user.id)
    empleados_ids = db.scalars(select(Empleado.id).where(Empleado.departamento_id.in_(departamentos))).all()

    bloque = db.get(BloqueHorasExtra, bloque_id)
    if not bloque:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bloque de horas extra no encontrado")

    asistencia = db.get(RegistroAsistencia, bloque.asistencia_id)
    if not asistencia or asistencia.empleado_id not in empleados_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para validar este bloque")

    bloque.validacion_supervisor = True
    db.commit()
    return {"ok": True}


@router.post("/aprobar-pase/{asistencia_id}", response_model=AsistenciaOut)
def aprobar_pase(
    asistencia_id: int,
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR)),
):
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"DEBUG - Endpoint aprobar_pase llamado con asistencia_id: {asistencia_id}")

    try:
        asistencia = approve_late_pass(db, user, asistencia_id)
        db.commit()
        db.refresh(asistencia)
        return asistencia
    except HTTPException as e:
        db.rollback()
        logger.info(f"DEBUG - HTTPException: {e.status_code} - {e.detail}")
        raise e
    except Exception as e:
        db.rollback()
        import logging
        logging.error(f"Error al aprobar pase: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al aprobar pase: {str(e)}")


@router.get("/empleados", response_model=list[EmpleadoOut])
def obtener_empleados_subordinados(
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR)),
):
    departamentos = select(SupervisorDepartamento.departamento_id).where(SupervisorDepartamento.usuario_id == user.id)
    return db.scalars(
        select(Empleado)
        .where(Empleado.departamento_id.in_(departamentos), Empleado.activo.is_(True))
        .order_by(Empleado.nombre_completo)
    ).all()


@router.get("/plantillas-turnos", response_model=list[PlantillaTurnoOut])
def obtener_plantillas_turnos(
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR, RolNombre.RRHH, RolNombre.ADMINISTRADOR, RolNombre.SUPERUSUARIO)),
):
    return db.scalars(select(PlantillaTurno).order_by(PlantillaTurno.nombre)).all()


@router.get("/plantillas-turnos/{plantilla_id}/detalles", response_model=list[DetallePlantillaOut])
def obtener_detalles_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR, RolNombre.RRHH, RolNombre.ADMINISTRADOR, RolNombre.SUPERUSUARIO)),
):
    plantilla = db.get(PlantillaTurno, plantilla_id)
    if not plantilla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla no encontrada")
    return db.scalars(
        select(DetallePlantillaTurno)
        .where(DetallePlantillaTurno.plantilla_id == plantilla_id)
        .order_by(DetallePlantillaTurno.dia_semana)
    ).all()


@router.put("/empleados/{empleado_id}/romper-plantilla")
def romper_plantilla_empleado(
    empleado_id: int,
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR)),
):
    departamentos = select(SupervisorDepartamento.departamento_id).where(SupervisorDepartamento.usuario_id == user.id)
    empleados_ids = db.scalars(select(Empleado.id).where(Empleado.departamento_id.in_(departamentos))).all()
    
    if empleado_id not in empleados_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para modificar este colaborador")
    
    empleado = db.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    
    # Si tiene plantilla asignada, crear turnos individuales basados en ella
    if empleado.plantilla_turno_id:
        plantilla = db.get(PlantillaTurno, empleado.plantilla_turno_id)
        if plantilla:
            detalles = db.scalars(
                select(DetallePlantillaTurno)
                .where(DetallePlantillaTurno.plantilla_id == plantilla.id)
                .order_by(DetallePlantillaTurno.dia_semana)
            ).all()
            
            # Crear turnos individuales basados en la plantilla
            for detalle in detalles:
                turno = TurnoHorario(
                    empleado_id=empleado_id,
                    dia_semana=detalle.dia_semana,
                    hora_entrada_oficial=detalle.hora_entrada_oficial,
                    hora_salida_oficial=detalle.hora_salida_oficial,
                    tolerancia_minutos=detalle.tolerancia_minutos,
                    es_descanso=detalle.es_descanso
                )
                db.add(turno)
    
    # Romper la referencia a la plantilla
    empleado.plantilla_turno_id = None
    db.commit()
    return {"ok": True}


@router.get("/turnos", response_model=list[TurnoOut])
def obtener_turnos_subordinados(
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR)),
):
    departamentos = select(SupervisorDepartamento.departamento_id).where(SupervisorDepartamento.usuario_id == user.id)
    empleados = select(Empleado.id).where(Empleado.departamento_id.in_(departamentos))
    return db.scalars(
        select(TurnoHorario)
        .where(TurnoHorario.empleado_id.in_(empleados))
        .order_by(TurnoHorario.empleado_id, TurnoHorario.dia_semana)
    ).all()


@router.post("/turnos", response_model=TurnoOut)
def crear_turno_subordinado(
    payload: TurnoCreate,
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR)),
):
    departamentos = select(SupervisorDepartamento.departamento_id).where(SupervisorDepartamento.usuario_id == user.id)
    empleados_ids = db.scalars(select(Empleado.id).where(Empleado.departamento_id.in_(departamentos))).all()

    if payload.empleado_id not in empleados_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes crear turnos para colaboradores que no son tus subordinados")

    turno = TurnoHorario(**payload.model_dump())
    db.add(turno)
    db.commit()
    db.refresh(turno)
    return turno


@router.put("/turnos/{turno_id}", response_model=TurnoOut)
def actualizar_turno_subordinado(
    turno_id: int,
    payload: TurnoDescansoUpdate,
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR)),
):
    turno = db.get(TurnoHorario, turno_id)
    if not turno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")

    departamentos = select(SupervisorDepartamento.departamento_id).where(SupervisorDepartamento.usuario_id == user.id)
    empleados_ids = db.scalars(select(Empleado.id).where(Empleado.departamento_id.in_(departamentos))).all()

    if turno.empleado_id not in empleados_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes modificar turnos de colaboradores que no son tus subordinados")

    turno.es_descanso = payload.es_descanso
    db.commit()
    db.refresh(turno)
    return turno


@router.delete("/turnos/{turno_id}")
def eliminar_turno_subordinado(
    turno_id: int,
    db: Session = Depends(get_db),
    user: UsuarioSistema = Depends(require_roles(RolNombre.SUPERVISOR)),
):
    turno = db.get(TurnoHorario, turno_id)
    if not turno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")

    departamentos = select(SupervisorDepartamento.departamento_id).where(SupervisorDepartamento.usuario_id == user.id)
    empleados_ids = db.scalars(select(Empleado.id).where(Empleado.departamento_id.in_(departamentos))).all()

    if turno.empleado_id not in empleados_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes eliminar turnos de colaboradores que no son tus subordinados")

    db.delete(turno)
    db.commit()
    return {"ok": True}
