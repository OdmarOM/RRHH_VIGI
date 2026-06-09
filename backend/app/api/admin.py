from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import require_roles, get_current_user
from app.core.database import get_db
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime
import os
import tempfile
from app.core.time import utc_now
from app.models import Departamento, DetallePlantillaTurno, Empleado, PlantillaTurno, RegistroAsistencia, RegistroAusencia, RolNombre, SalidaTemporal, TurnoHorario, UsuarioSistema, Rol, SupervisorDepartamento
from app.schemas import AusenciaCreate, AusenciaOut, EmpleadoCreate, EmpleadoOut, EmpleadoUpdate, TurnoCreate, TurnoOut, TurnoUpdate


router = APIRouter(prefix="/admin", tags=["admin"])
ADMIN_ACCESS = Depends(require_roles(RolNombre.ADMINISTRADOR, RolNombre.RRHH))


@router.post("/empleados", response_model=EmpleadoOut, dependencies=[ADMIN_ACCESS])
def crear_empleado(payload: EmpleadoCreate, db: Session = Depends(get_db)):
    empleado = Empleado(**payload.model_dump())
    db.add(empleado)
    db.commit()
    db.refresh(empleado)
    return empleado


@router.get("/empleados", response_model=list[EmpleadoOut], dependencies=[ADMIN_ACCESS])
def listar_empleados(db: Session = Depends(get_db)):
    try:
        return db.scalars(select(Empleado).order_by(Empleado.nombre_completo)).all()
    except Exception as e:
        print(f"Error en listar_empleados: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener colaboradores")


@router.get("/empleados/{id}", response_model=EmpleadoOut, dependencies=[ADMIN_ACCESS])
def obtener_empleado(id: int, db: Session = Depends(get_db)):
    empleado = db.get(Empleado, id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    return empleado


@router.put("/empleados/{id}", response_model=EmpleadoOut, dependencies=[ADMIN_ACCESS])
def actualizar_empleado(id: int, payload: EmpleadoUpdate, db: Session = Depends(get_db)):
    empleado = db.get(Empleado, id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(empleado, key, value)
    db.commit()
    db.refresh(empleado)
    return empleado


@router.delete("/empleados/{id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def eliminar_empleado(id: int, db: Session = Depends(get_db)):
    empleado = db.get(Empleado, id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    db.delete(empleado)
    db.commit()
    return {"ok": True}


@router.put("/empleados/{id}/activo", dependencies=[ADMIN_ACCESS])
def activar_desactivar_empleado(id: int, activo: bool, db: Session = Depends(get_db)):
    empleado = db.get(Empleado, id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    empleado.activo = activo
    db.commit()
    db.refresh(empleado)
    return {"ok": True, "activo": empleado.activo}


@router.post("/turnos", response_model=TurnoOut, dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def crear_turno(payload: TurnoCreate, db: Session = Depends(get_db)):
    turno = TurnoHorario(**payload.model_dump())
    db.add(turno)
    db.commit()
    db.refresh(turno)
    return turno


@router.get("/turnos", response_model=list[TurnoOut], dependencies=[ADMIN_ACCESS])
def listar_turnos(db: Session = Depends(get_db)):
    try:
        return db.scalars(select(TurnoHorario).order_by(TurnoHorario.empleado_id, TurnoHorario.dia_semana)).all()
    except Exception as e:
        print(f"Error en listar_turnos: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener turnos")


@router.get("/turnos-raw", dependencies=[ADMIN_ACCESS])
def listar_turnos_raw(db: Session = Depends(get_db)):
    turnos = db.scalars(select(TurnoHorario).order_by(TurnoHorario.empleado_id, TurnoHorario.dia_semana)).all()
    return [
        {
            "id": t.id,
            "empleado_id": t.empleado_id,
            "dia_semana": t.dia_semana,
            "hora_entrada_oficial": str(t.hora_entrada_oficial) if t.hora_entrada_oficial else None,
            "hora_salida_oficial": str(t.hora_salida_oficial) if t.hora_salida_oficial else None,
            "tolerancia_minutos": t.tolerancia_minutos,
            "es_descanso": t.es_descanso
        }
        for t in turnos
    ]


@router.put("/turnos/{id}", response_model=TurnoOut, dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def actualizar_turno(id: int, payload: TurnoUpdate, db: Session = Depends(get_db)):
    turno = db.get(TurnoHorario, id)
    if not turno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(turno, key, value)
    db.commit()
    db.refresh(turno)
    return turno


@router.delete("/turnos/{id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def eliminar_turno(id: int, db: Session = Depends(get_db)):
    turno = db.get(TurnoHorario, id)
    if not turno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
    db.delete(turno)
    db.commit()
    return {"ok": True}


# Plantillas de turnos
@router.post("/plantillas-turnos", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def crear_plantilla(nombre: str, descripcion: str | None = None, db: Session = Depends(get_db)):
    plantilla = PlantillaTurno(nombre=nombre, descripcion=descripcion)
    db.add(plantilla)
    db.commit()
    db.refresh(plantilla)
    return plantilla


@router.get("/plantillas-turnos", dependencies=[ADMIN_ACCESS])
def listar_plantillas(db: Session = Depends(get_db)):
    return db.scalars(select(PlantillaTurno).order_by(PlantillaTurno.nombre)).all()


@router.delete("/plantillas-turnos/{id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def eliminar_plantilla(id: int, db: Session = Depends(get_db)):
    plantilla = db.get(PlantillaTurno, id)
    if not plantilla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla no encontrada")
    # Eliminar detalles primero
    db.scalars(select(DetallePlantillaTurno).where(DetallePlantillaTurno.plantilla_id == id)).all()
    for detalle in db.scalars(select(DetallePlantillaTurno).where(DetallePlantillaTurno.plantilla_id == id)):
        db.delete(detalle)
    db.delete(plantilla)
    db.commit()
    return {"ok": True}


@router.put("/plantillas-turnos/{id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def actualizar_plantilla(id: int, nombre: str, descripcion: str | None = None, db: Session = Depends(get_db)):
    plantilla = db.get(PlantillaTurno, id)
    if not plantilla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla no encontrada")
    plantilla.nombre = nombre
    if descripcion is not None:
        plantilla.descripcion = descripcion
    db.commit()
    db.refresh(plantilla)
    return plantilla


@router.post("/plantillas-turnos/{plantilla_id}/detalles", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def agregar_detalle_plantilla(plantilla_id: int, data: dict, db: Session = Depends(get_db)):
    from datetime import time
    plantilla = db.get(PlantillaTurno, plantilla_id)
    if not plantilla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla no encontrada")

    dia_semana = data.get('dia_semana')
    hora_entrada = data.get('hora_entrada')
    hora_salida = data.get('hora_salida')
    tolerancia = data.get('tolerancia', 15)
    es_descanso = data.get('es_descanso', False)
    es_por_asistencia = data.get('es_por_asistencia', False)

    detalle = DetallePlantillaTurno(
        plantilla_id=plantilla_id,
        dia_semana=dia_semana,
        hora_entrada_oficial=time.fromisoformat(hora_entrada) if hora_entrada and not es_por_asistencia else None,
        hora_salida_oficial=time.fromisoformat(hora_salida) if hora_salida and not es_por_asistencia else None,
        tolerancia_minutos=tolerancia,
        es_descanso=es_descanso,
        es_por_asistencia=es_por_asistencia
    )
    db.add(detalle)
    db.commit()
    db.refresh(detalle)
    return detalle


@router.get("/plantillas-turnos/{plantilla_id}/detalles", dependencies=[ADMIN_ACCESS])
def listar_detalles_plantilla(plantilla_id: int, db: Session = Depends(get_db)):
    detalles = db.scalars(select(DetallePlantillaTurno).where(DetallePlantillaTurno.plantilla_id == plantilla_id).order_by(DetallePlantillaTurno.dia_semana)).all()
    return [
        {
            "id": d.id,
            "plantilla_id": d.plantilla_id,
            "dia_semana": d.dia_semana,
            "hora_entrada_oficial": d.hora_entrada_oficial.isoformat() if d.hora_entrada_oficial else None,
            "hora_salida_oficial": d.hora_salida_oficial.isoformat() if d.hora_salida_oficial else None,
            "tolerancia_minutos": d.tolerancia_minutos,
            "es_descanso": d.es_descanso,
            "es_por_asistencia": d.es_por_asistencia
        }
        for d in detalles
    ]


@router.get("/plantillas-turnos/{plantilla_id}/info", dependencies=[ADMIN_ACCESS])
def info_plantilla(plantilla_id: int, db: Session = Depends(get_db)):
    plantilla = db.get(PlantillaTurno, plantilla_id)
    if not plantilla:
        return {"error": "Plantilla no encontrada"}
    detalles = db.scalars(select(DetallePlantillaTurno).where(DetallePlantillaTurno.plantilla_id == plantilla_id).order_by(DetallePlantillaTurno.dia_semana)).all()
    return {
        "id": plantilla.id,
        "nombre": plantilla.nombre,
        "descripcion": plantilla.descripcion,
        "num_detalles": len(detalles),
        "detalles": [
            {
                "dia_semana": d.dia_semana,
                "hora_entrada": str(d.hora_entrada_oficial) if d.hora_entrada_oficial else None,
                "hora_salida": str(d.hora_salida_oficial) if d.hora_salida_oficial else None,
                "tolerancia": d.tolerancia_minutos,
                "es_descanso": d.es_descanso
            }
            for d in detalles
        ]
    }


@router.delete("/plantillas-turnos/{plantilla_id}/detalles/{detalle_id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def eliminar_detalle_plantilla(plantilla_id: int, detalle_id: int, db: Session = Depends(get_db)):
    detalle = db.get(DetallePlantillaTurno, detalle_id)
    if not detalle or detalle.plantilla_id != plantilla_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle no encontrado")
    db.delete(detalle)
    db.commit()
    return {"ok": True}


@router.get("/usuarios-sistema", dependencies=[ADMIN_ACCESS])
def listar_usuarios_sistema(db: Session = Depends(get_db)):
    usuarios = db.scalars(select(UsuarioSistema).order_by(UsuarioSistema.id)).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "rol": u.rol.nombre,
            "rol_id": u.rol_id,
            "empleado_id": u.empleado_id,
            "empleado_nombre": u.empleado.nombre_completo if u.empleado else None,
            "activo": u.activo
        }
        for u in usuarios
    ]


@router.post("/usuarios-sistema", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR, RolNombre.RRHH))])
def crear_usuario_sistema(username: str, password: str, rol_id: int, empleado_id: int | None = None, db: Session = Depends(get_db), current_user: UsuarioSistema = Depends(get_current_user)):
    from app.core.security import hash_password
    if db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == username)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username ya existe")
    rol = db.get(Rol, rol_id)
    if not rol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")

    # Validar restricciones de jerarquía
    if rol.nombre == RolNombre.SUPERUSUARIO and current_user.rol.nombre != RolNombre.SUPERUSUARIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el superusuario puede crear superusuarios")
    if rol.nombre == RolNombre.ADMINISTRADOR and current_user.rol.nombre != RolNombre.SUPERUSUARIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el superusuario puede crear administradores")
    if rol.nombre == RolNombre.SUPERVISOR and current_user.rol.nombre not in [RolNombre.SUPERUSUARIO, RolNombre.RRHH]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo RRHH o superusuario pueden crear supervisores")

    if empleado_id:
        empleado = db.get(Empleado, empleado_id)
        if not empleado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    usuario = UsuarioSistema(
        username=username,
        password_hash=hash_password(password),
        rol_id=rol_id,
        empleado_id=empleado_id,
        activo=True
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"ok": True, "id": usuario.id}


@router.put("/usuarios-sistema/{usuario_id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR, RolNombre.RRHH))])
def actualizar_usuario_sistema(usuario_id: int, username: str | None = None, rol_id: int | None = None, empleado_id: int | None = None, db: Session = Depends(get_db), current_user: UsuarioSistema = Depends(get_current_user)):
    usuario = db.get(UsuarioSistema, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if username and username != usuario.username:
        if db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == username)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username ya existe")
        usuario.username = username
    if rol_id:
        rol = db.get(Rol, rol_id)
        if not rol:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")

        # Validar restricciones de jerarquía
        if rol.nombre == RolNombre.SUPERUSUARIO and current_user.rol.nombre != RolNombre.SUPERUSUARIO:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el superusuario puede asignar rol de superusuario")
        if rol.nombre == RolNombre.ADMINISTRADOR and current_user.rol.nombre != RolNombre.SUPERUSUARIO:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el superusuario puede asignar rol de administrador")
        if rol.nombre == RolNombre.SUPERVISOR and current_user.rol.nombre not in [RolNombre.SUPERUSUARIO, RolNombre.RRHH]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo RRHH o superusuario pueden asignar rol de supervisor")

        usuario.rol_id = rol_id
    if empleado_id is not None:
        if empleado_id:
            empleado = db.get(Empleado, empleado_id)
            if not empleado:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
        usuario.empleado_id = empleado_id
    db.commit()
    db.refresh(usuario)
    return {"ok": True}


@router.delete("/usuarios-sistema/{usuario_id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR, RolNombre.RRHH))])
def eliminar_usuario_sistema(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.get(UsuarioSistema, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    db.delete(usuario)
    db.commit()
    return {"ok": True}


@router.put("/usuarios-sistema/{usuario_id}/activo", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR, RolNombre.RRHH))])
def activar_desactivar_usuario(usuario_id: int, activo: bool, db: Session = Depends(get_db)):
    usuario = db.get(UsuarioSistema, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    usuario.activo = activo
    db.commit()
    db.refresh(usuario)
    return {"ok": True, "activo": usuario.activo}


@router.get("/supervisores-departamentos", dependencies=[ADMIN_ACCESS])
def listar_supervisores_departamentos(db: Session = Depends(get_db)):
    relaciones = db.scalars(select(SupervisorDepartamento).order_by(SupervisorDepartamento.usuario_id, SupervisorDepartamento.departamento_id)).all()
    return [
        {
            "id": r.id,
            "usuario_id": r.usuario_id,
            "departamento_id": r.departamento_id,
            "usuario_nombre": r.usuario_sistema.username if r.usuario_sistema else None,
            "departamento_nombre": r.departamento.nombre if r.departamento else None
        }
        for r in relaciones
    ]


@router.post("/supervisores-departamentos", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR, RolNombre.RRHH))])
def asignar_supervisor_departamento(usuario_id: int, departamento_id: int, db: Session = Depends(get_db)):
    usuario = db.get(UsuarioSistema, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    departamento = db.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento no encontrado")

    # Verificar si ya existe la relación
    existente = db.scalar(
        select(SupervisorDepartamento).where(
            SupervisorDepartamento.usuario_id == usuario_id,
            SupervisorDepartamento.departamento_id == departamento_id
        )
    )
    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Relación ya existe")

    relacion = SupervisorDepartamento(usuario_id=usuario_id, departamento_id=departamento_id)
    db.add(relacion)
    db.commit()
    db.refresh(relacion)
    return {"ok": True}


@router.delete("/supervisores-departamentos/{relacion_id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR, RolNombre.RRHH))])
def eliminar_supervisor_departamento(relacion_id: int, db: Session = Depends(get_db)):
    relacion = db.get(SupervisorDepartamento, relacion_id)
    if not relacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relación no encontrada")
    db.delete(relacion)
    db.commit()
    return {"ok": True}


@router.put("/plantillas-turnos/{plantilla_id}/detalles/{detalle_id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def actualizar_detalle_plantilla(plantilla_id: int, detalle_id: int, data: dict, db: Session = Depends(get_db)):
    from datetime import time
    detalle = db.get(DetallePlantillaTurno, detalle_id)
    if not detalle or detalle.plantilla_id != plantilla_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle no encontrado")

    es_por_asistencia = data.get('es_por_asistencia', False)
    es_descanso = data.get('es_descanso', False)
    hora_entrada = data.get('hora_entrada')
    hora_salida = data.get('hora_salida')
    tolerancia = data.get('tolerancia', 15)

    if es_por_asistencia:
        detalle.hora_entrada_oficial = None
        detalle.hora_salida_oficial = None
    else:
        if hora_entrada:
            detalle.hora_entrada_oficial = time.fromisoformat(hora_entrada)
        if hora_salida:
            detalle.hora_salida_oficial = time.fromisoformat(hora_salida)

    detalle.tolerancia_minutos = tolerancia
    detalle.es_descanso = es_descanso
    detalle.es_por_asistencia = es_por_asistencia
    db.commit()
    db.refresh(detalle)
    return detalle


@router.put("/empleados/{empleado_id}/plantilla-turno/{plantilla_id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def asignar_plantilla_empleado(empleado_id: int, plantilla_id: int, db: Session = Depends(get_db)):
    empleado = db.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    plantilla = db.get(PlantillaTurno, plantilla_id)
    if not plantilla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla no encontrada")
    
    # Eliminar turnos individuales existentes (ya que usará plantilla)
    for turno in db.scalars(select(TurnoHorario).where(TurnoHorario.empleado_id == empleado_id)):
        db.delete(turno)
    
    # Solo asignar la referencia a la plantilla, no crear turnos individuales
    empleado.plantilla_turno_id = plantilla_id
    db.commit()
    return {"ok": True}


@router.post("/empleados/{empleado_id}/romper-plantilla", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def romper_plantilla_empleado(empleado_id: int, db: Session = Depends(get_db)):
    """Rompe la referencia a la plantilla y crea turnos individuales basados en la plantilla actual."""
    empleado = db.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    
    if not empleado.plantilla_turno_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El empleado no tiene plantilla asignada")
    
    plantilla = db.get(PlantillaTurno, empleado.plantilla_turno_id)
    if not plantilla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla no encontrada")
    
    # Crear turnos individuales basados en la plantilla actual
    detalles = db.scalars(select(DetallePlantillaTurno).where(DetallePlantillaTurno.plantilla_id == plantilla.id)).all()
    for detalle in detalles:
        if not detalle.es_descanso and detalle.hora_entrada_oficial and detalle.hora_salida_oficial:
            nuevo_turno = TurnoHorario(
                empleado_id=empleado_id,
                dia_semana=detalle.dia_semana,
                hora_entrada_oficial=detalle.hora_entrada_oficial,
                hora_salida_oficial=detalle.hora_salida_oficial,
                tolerancia_minutos=detalle.tolerancia_minutos
            )
            db.add(nuevo_turno)
    
    # Romper la referencia a la plantilla
    empleado.plantilla_turno_id = None
    db.commit()
    return {"ok": True}


@router.put("/asistencias/{asistencia_id}/autorizar-horas-extra", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR, RolNombre.RRHH))])
def autorizar_horas_extra(asistencia_id: int, db: Session = Depends(get_db)):
    """Autoriza las horas extra de un registro de asistencia (solo RRHH)"""
    asistencia = db.get(RegistroAsistencia, asistencia_id)
    if not asistencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de asistencia no encontrado")
    
    if asistencia.minutos_extra_calculados == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay horas extra calculadas para autorizar")
    
    asistencia.autorizacion_horas_extra_rrhh = True
    db.commit()
    return {"ok": True, "minutos_extra": asistencia.minutos_extra_calculados}


# CRUD de departamentos
@router.post("/departamentos", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def crear_departamento(nombre: str, db: Session = Depends(get_db)):
    try:
        departamento = Departamento(nombre=nombre)
        db.add(departamento)
        db.commit()
        db.refresh(departamento)
        return departamento
    except Exception as e:
        db.rollback()
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El departamento ya existe")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear departamento")


@router.get("/departamentos", dependencies=[ADMIN_ACCESS])
def listar_departamentos(db: Session = Depends(get_db)):
    return db.scalars(select(Departamento).order_by(Departamento.nombre)).all()


@router.get("/roles", dependencies=[ADMIN_ACCESS])
def listar_roles(db: Session = Depends(get_db)):
    roles = db.scalars(select(Rol).order_by(Rol.id)).all()
    return [
        {
            "id": r.id,
            "nombre": r.nombre
        }
        for r in roles
    ]


@router.put("/departamentos/{id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def actualizar_departamento(id: int, nombre: str, db: Session = Depends(get_db)):
    departamento = db.get(Departamento, id)
    if not departamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento no encontrado")
    departamento.nombre = nombre
    db.commit()
    db.refresh(departamento)
    return departamento


@router.delete("/departamentos/{id}", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR))])
def eliminar_departamento(id: int, db: Session = Depends(get_db)):
    departamento = db.get(Departamento, id)
    if not departamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento no encontrado")
    # Verificar que no tenga empleados activos
    empleados_count = db.scalar(select(Empleado).where(Empleado.departamento_id == id).with_only_columns(Empleado.id).count())
    if empleados_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede eliminar un departamento con empleados activos")
    db.delete(departamento)
    db.commit()
    return {"ok": True}


# Endpoints para gestión de ausencias (vacaciones, incapacidades, permisos)
@router.get("/ausencias", response_model=list[AusenciaOut], dependencies=[ADMIN_ACCESS])
def obtener_ausencias(db: Session = Depends(get_db)):
    return db.scalars(select(RegistroAusencia).order_by(RegistroAusencia.fecha_inicio.desc())).all()


@router.post("/ausencias", response_model=AusenciaOut, dependencies=[ADMIN_ACCESS])
def crear_ausencia(payload: AusenciaCreate, db: Session = Depends(get_db)):
    empleado = db.get(Empleado, payload.empleado_id)
    if not empleado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador no encontrado")
    
    ausencia = RegistroAusencia(
        empleado_id=payload.empleado_id,
        tipo_ausencia=payload.tipo_ausencia,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
        pagada=payload.pagada,
        motivo=payload.motivo,
        fecha_registro=utc_now()
    )
    db.add(ausencia)
    db.commit()
    db.refresh(ausencia)
    return ausencia


@router.put("/ausencias/{ausencia_id}/aprobar", dependencies=[ADMIN_ACCESS])
def aprobar_ausencia(ausencia_id: int, db: Session = Depends(get_db)):
    ausencia = db.get(RegistroAusencia, ausencia_id)
    if not ausencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ausencia no encontrada")
    
    ausencia.aprobado_rrhh = True
    db.commit()
    return {"ok": True}


@router.delete("/ausencias/{ausencia_id}", dependencies=[ADMIN_ACCESS])
def eliminar_ausencia(ausencia_id: int, db: Session = Depends(get_db)):
    ausencia = db.get(RegistroAusencia, ausencia_id)
    if not ausencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ausencia no encontrada")
    db.delete(ausencia)
    db.commit()
    return {"ok": True}


# Endpoints para reportes de RRHH
@router.get("/reportes/horas-laboradas", dependencies=[ADMIN_ACCESS])
def reporte_horas_laboradas(
    fecha_inicio: str,
    fecha_fin: str,
    empleado_id: int | None = None,
    db: Session = Depends(get_db)
):
    from datetime import datetime
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    
    query = select(RegistroAsistencia).where(
        RegistroAsistencia.fecha_turno >= inicio,
        RegistroAsistencia.fecha_turno <= fin,
        RegistroAsistencia.hora_entrada_real.is_not(None),
        RegistroAsistencia.hora_salida_real.is_not(None)
    )
    
    if empleado_id:
        query = query.where(RegistroAsistencia.empleado_id == empleado_id)
    
    registros = db.scalars(query.order_by(RegistroAsistencia.fecha_turno)).all()
    
    reporte = []
    for reg in registros:
        if reg.hora_entrada_real and reg.hora_salida_real:
            horas = (reg.hora_salida_real - reg.hora_entrada_real).total_seconds() / 3600
            reporte.append({
                "empleado_id": reg.empleado_id,
                "fecha": reg.fecha_turno.isoformat(),
                "hora_entrada": reg.hora_entrada_real.isoformat(),
                "hora_salida": reg.hora_salida_real.isoformat(),
                "horas_laboradas": round(horas, 2),
                "estado": reg.estado_registro
            })
    
    return reporte


@router.get("/reportes/horas-extra", dependencies=[ADMIN_ACCESS])
def reporte_horas_extra(
    fecha_inicio: str,
    fecha_fin: str,
    empleado_id: int | None = None,
    db: Session = Depends(get_db)
):
    from datetime import datetime
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    
    query = select(RegistroAsistencia).where(
        RegistroAsistencia.fecha_turno >= inicio,
        RegistroAsistencia.fecha_turno <= fin,
        RegistroAsistencia.minutos_extra_calculados > 0
    )
    
    if empleado_id:
        query = query.where(RegistroAsistencia.empleado_id == empleado_id)
    
    registros = db.scalars(query.order_by(RegistroAsistencia.fecha_turno)).all()
    
    reporte = []
    for reg in registros:
        reporte.append({
            "empleado_id": reg.empleado_id,
            "fecha": reg.fecha_turno.isoformat(),
            "minutos_extra": reg.minutos_extra_calculados,
            "horas_extra": round(reg.minutos_extra_calculados / 60, 2),
            "validado_supervisor": reg.validacion_supervisor,
            "validado_rrhh": reg.validacion_rrhh
        })
    
    return reporte


@router.get("/reportes/asistencias", dependencies=[ADMIN_ACCESS])
def reporte_asistencias(
    fecha_inicio: str,
    fecha_fin: str,
    empleado_id: int | None = None,
    db: Session = Depends(get_db)
):
    from datetime import datetime
    from sqlalchemy import or_
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    
    # Buscar turnos por asistencia
    query_turnos = select(TurnoHorario).where(
        TurnoHorario.es_por_asistencia == True
    )
    
    turnos_por_asistencia = db.scalars(query_turnos).all()
    empleado_ids_por_asistencia = set(t.empleado_id for t in turnos_por_asistencia)
    
    # Filtrar registros de asistencia para estos empleados
    query = select(RegistroAsistencia).where(
        RegistroAsistencia.fecha_turno >= inicio,
        RegistroAsistencia.fecha_turno <= fin,
        RegistroAsistencia.empleado_id.in_(empleado_ids_por_asistencia),
        RegistroAsistencia.hora_entrada_real.is_not(None)
    )
    
    if empleado_id:
        query = query.where(RegistroAsistencia.empleado_id == empleado_id)
    
    registros = db.scalars(query.order_by(RegistroAsistencia.fecha_turno)).all()
    
    reporte = []
    for reg in registros:
        reporte.append({
            "empleado_id": reg.empleado_id,
            "fecha": reg.fecha_turno.isoformat(),
            "hora_entrada": reg.hora_entrada_real.isoformat() if reg.hora_entrada_real else None,
            "hora_salida": reg.hora_salida_real.isoformat() if reg.hora_salida_real else None,
            "estado_registro": reg.estado_registro.value if reg.estado_registro else None
        })

    return reporte


@router.get("/reportes/horas-laboradas/excel", dependencies=[ADMIN_ACCESS])
def exportar_horas_laboradas_excel(
    fecha_inicio: str,
    fecha_fin: str,
    empleado_id: int | None = None,
    db: Session = Depends(get_db)
):
    from datetime import datetime, timedelta
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    query = select(RegistroAsistencia).where(
        RegistroAsistencia.fecha_turno >= inicio,
        RegistroAsistencia.fecha_turno <= fin,
        RegistroAsistencia.hora_entrada_real.is_not(None),
        RegistroAsistencia.hora_salida_real.is_not(None)
    )

    if empleado_id:
        query = query.where(RegistroAsistencia.empleado_id == empleado_id)

    registros = db.scalars(query.order_by(RegistroAsistencia.fecha_turno)).all()

    # Obtener todos los departamentos
    departamentos = db.scalars(select(Departamento)).all()

    # Obtener todos los empleados
    empleados_query = select(Empleado)
    if empleado_id:
        empleados_query = empleados_query.where(Empleado.id == empleado_id)
    empleados = db.scalars(empleados_query).all()

    # Calcular todos los días en el rango
    dias_en_rango = []
    fecha_actual = inicio
    while fecha_actual <= fin:
        dias_en_rango.append(fecha_actual)
        fecha_actual += timedelta(days=1)

    # Nombres de días en español
    dias_semana = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO']

    wb = Workbook()
    wb.remove(wb.active)

    # Crear hoja por departamento
    for dept in departamentos:
        dept_empleados = [e for e in empleados if e.departamento_id == dept.id]
        if not dept_empleados:
            continue

        ws = wb.create_sheet(title=dept.nombre[:31])

        # Header con días
        headers = ['Número', 'Colaborador'] + [f"{d.strftime('%d/%m')} ({dias_semana[d.weekday()]})" for d in dias_en_rango] + ['TOTAL']
        ws.append(headers)

        # Style header
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')

        # Data por empleado
        for emp in dept_empleados:
            fila = [emp.numero_empleado, emp.nombre_completo]
            total_horas = 0

            for fecha in dias_en_rango:
                # Buscar registro de asistencia para este empleado en esta fecha
                reg = next((r for r in registros if r.empleado_id == emp.id and r.fecha_turno == fecha), None)
                if reg and reg.hora_entrada_real and reg.hora_salida_real:
                    horas = (reg.hora_salida_real - reg.hora_entrada_real).total_seconds() / 3600
                    fila.append(round(horas, 2))
                    total_horas += horas
                else:
                    fila.append(0)

            fila.append(round(total_horas, 2))
            ws.append(fila)

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    # Si no hay datos, crear hoja vacía
    if len(wb.sheetnames) == 0:
        ws = wb.create_sheet(title="Sin Datos")
        ws.append(['No hay registros para el período seleccionado'])

    filename = f"horas_laboradas_{fecha_inicio}_{fecha_fin}.xlsx"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    wb.save(filepath)

    return FileResponse(filepath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/reportes/horas-extra/excel", dependencies=[ADMIN_ACCESS])
def exportar_horas_extra_excel(
    fecha_inicio: str,
    fecha_fin: str,
    empleado_id: int | None = None,
    db: Session = Depends(get_db)
):
    from datetime import datetime, timedelta
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    query = select(RegistroAsistencia).where(
        RegistroAsistencia.fecha_turno >= inicio,
        RegistroAsistencia.fecha_turno <= fin,
        RegistroAsistencia.minutos_extra_calculados > 0
    )

    if empleado_id:
        query = query.where(RegistroAsistencia.empleado_id == empleado_id)

    registros = db.scalars(query.order_by(RegistroAsistencia.fecha_turno)).all()

    departamentos = db.scalars(select(Departamento)).all()

    empleados_query = select(Empleado)
    if empleado_id:
        empleados_query = empleados_query.where(Empleado.id == empleado_id)
    empleados = db.scalars(empleados_query).all()

    dias_en_rango = []
    fecha_actual = inicio
    while fecha_actual <= fin:
        dias_en_rango.append(fecha_actual)
        fecha_actual += timedelta(days=1)

    dias_semana = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO']

    wb = Workbook()
    wb.remove(wb.active)

    for dept in departamentos:
        dept_empleados = [e for e in empleados if e.departamento_id == dept.id]
        if not dept_empleados:
            continue

        ws = wb.create_sheet(title=dept.nombre[:31])

        headers = ['Número', 'Colaborador'] + [f"{d.strftime('%d/%m')} ({dias_semana[d.weekday()]})" for d in dias_en_rango] + ['TOTAL']
        ws.append(headers)

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')

        for emp in dept_empleados:
            fila = [emp.numero_empleado, emp.nombre_completo]
            total_horas = 0

            for fecha in dias_en_rango:
                reg = next((r for r in registros if r.empleado_id == emp.id and r.fecha_turno == fecha), None)
                if reg and reg.minutos_extra_calculados > 0:
                    horas = reg.minutos_extra_calculados / 60
                    fila.append(round(horas, 2))
                    total_horas += horas
                else:
                    fila.append(0)

            fila.append(round(total_horas, 2))
            ws.append(fila)

        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    if len(wb.sheetnames) == 0:
        ws = wb.create_sheet(title="Sin Datos")
        ws.append(['No hay registros de horas extra para el período seleccionado'])

    filename = f"horas_extra_{fecha_inicio}_{fecha_fin}.xlsx"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    wb.save(filepath)

    return FileResponse(filepath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/reportes/asistencias/excel", dependencies=[ADMIN_ACCESS])
def exportar_asistencias_excel(
    fecha_inicio: str,
    fecha_fin: str,
    empleado_id: int | None = None,
    db: Session = Depends(get_db)
):
    from datetime import datetime, timedelta
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    query_turnos = select(TurnoHorario).where(TurnoHorario.es_por_asistencia == True)
    turnos_por_asistencia = db.scalars(query_turnos).all()
    empleado_ids_por_asistencia = set(t.empleado_id for t in turnos_por_asistencia)

    query = select(RegistroAsistencia).where(
        RegistroAsistencia.fecha_turno >= inicio,
        RegistroAsistencia.fecha_turno <= fin,
        RegistroAsistencia.empleado_id.in_(empleado_ids_por_asistencia),
        RegistroAsistencia.hora_entrada_real.is_not(None)
    )

    if empleado_id:
        query = query.where(RegistroAsistencia.empleado_id == empleado_id)

    registros = db.scalars(query.order_by(RegistroAsistencia.fecha_turno)).all()

    departamentos = db.scalars(select(Departamento)).all()

    empleados_query = select(Empleado).where(Empleado.id.in_(empleado_ids_por_asistencia))
    if empleado_id:
        empleados_query = empleados_query.where(Empleado.id == empleado_id)
    empleados = db.scalars(empleados_query).all()

    dias_en_rango = []
    fecha_actual = inicio
    while fecha_actual <= fin:
        dias_en_rango.append(fecha_actual)
        fecha_actual += timedelta(days=1)

    dias_semana = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO']

    wb = Workbook()
    wb.remove(wb.active)

    for dept in departamentos:
        dept_empleados = [e for e in empleados if e.departamento_id == dept.id]
        if not dept_empleados:
            continue

        ws = wb.create_sheet(title=dept.nombre[:31])

        headers = ['Número', 'Colaborador'] + [f"{d.strftime('%d/%m')} ({dias_semana[d.weekday()]})" for d in dias_en_rango] + ['TOTAL']
        ws.append(headers)

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')

        for emp in dept_empleados:
            fila = [emp.numero_empleado, emp.nombre_completo]
            total_asistencias = 0

            for fecha in dias_en_rango:
                reg = next((r for r in registros if r.empleado_id == emp.id and r.fecha_turno == fecha), None)
                if reg and reg.hora_entrada_real:
                    fila.append('✅')
                    total_asistencias += 1
                else:
                    fila.append('❌')

            fila.append(total_asistencias)
            ws.append(fila)

        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    if len(wb.sheetnames) == 0:
        ws = wb.create_sheet(title="Sin Datos")
        ws.append(['No hay registros de asistencias para el período seleccionado'])

    filename = f"asistencias_{fecha_inicio}_{fecha_fin}.xlsx"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    wb.save(filepath)

    return FileResponse(filepath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.put("/incidencias/horas-extra/{asistencia_id}/aprobar-rrhh", dependencies=[Depends(require_roles(RolNombre.ADMINISTRADOR, RolNombre.RRHH))])
def aprobar_horas_extra_rrhh(asistencia_id: int, db: Session = Depends(get_db)):
    """Aprueba horas extra y bloquea el registro para evitar modificaciones"""
    from app.core.time import utc_now
    asistencia = db.get(RegistroAsistencia, asistencia_id)
    if not asistencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia no encontrada")
    if not asistencia.validacion_supervisor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El registro debe ser validado por supervisor primero")
    asistencia.validacion_rrhh = True
    db.commit()
    db.refresh(asistencia)
    return asistencia


@router.get("/reportes/salidas-temporales", dependencies=[ADMIN_ACCESS])
def reporte_salidas_temporales(
    fecha_inicio: str,
    fecha_fin: str,
    empleado_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Reporte detallado de salidas temporales (comer, mandado, permisos)"""
    from datetime import datetime, timedelta
    from app.core.time import utc_now

    fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    query = (
        select(SalidaTemporal, RegistroAsistencia, Empleado)
        .join(RegistroAsistencia, SalidaTemporal.asistencia_id == RegistroAsistencia.id)
        .join(Empleado, RegistroAsistencia.empleado_id == Empleado.id)
        .where(RegistroAsistencia.fecha_turno >= fecha_inicio_dt)
        .where(RegistroAsistencia.fecha_turno <= fecha_fin_dt)
    )

    if empleado_id:
        query = query.where(RegistroAsistencia.empleado_id == empleado_id)

    resultados = db.execute(query.order_by(SalidaTemporal.hora_salida.desc())).all()

    reporte = []
    for salida, asistencia, empleado in resultados:
        duracion_minutos = None
        if salida.hora_regreso:
            duracion_minutos = int((salida.hora_regreso - salida.hora_salida).total_seconds() / 60)

        reporte.append({
            "id": salida.id,
            "empleado_id": empleado.id,
            "nombre_empleado": empleado.nombre_completo,
            "numero_empleado": empleado.numero_empleado,
            "puesto": empleado.puesto,
            "tipo_salida": salida.tipo_salida.value,
            "hora_salida": salida.hora_salida,
            "hora_regreso": salida.hora_regreso,
            "estado_salida": salida.estado_salida.value,
            "duracion_minutos": duracion_minutos,
            "minutos_descontados": salida.minutos_descontados,
            "descuenta_tiempo": salida.descuenta_tiempo,
            "fecha_turno": asistencia.fecha_turno
        })

    return reporte
