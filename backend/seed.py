from datetime import datetime, time, date, timedelta
from sqlalchemy import select
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Departamento, DetallePlantillaTurno, Empleado, EstadoEmpleado, EstadoFila, EstadoRegistro, EstadoVisita, EventoAsistencia, FilaExterno, PlantillaTurno, RegistroAsistencia, RegistroAusencia, Rol, RolNombre, SupervisorDepartamento, TipoAusencia, TipoEvento, TipoVisitante, TurnoHorario, UsuarioSistema, Visita


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    for nombre in RolNombre:
        if not db.scalar(select(Rol).where(Rol.nombre == nombre)):
            db.add(Rol(nombre=nombre))
    db.flush()

    if not db.scalar(select(Departamento).where(Departamento.nombre == "Producción")):
        db.add(Departamento(nombre="Producción"))
    if not db.scalar(select(Departamento).where(Departamento.nombre == "Almacén")):
        db.add(Departamento(nombre="Almacén"))
    if not db.scalar(select(Departamento).where(Departamento.nombre == "Mantenimiento")):
        db.add(Departamento(nombre="Mantenimiento"))
    db.flush()

    super_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.SUPERUSUARIO))
    vigilante_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.VIGILANTE))
    supervisor_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.SUPERVISOR))
    rrhh_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.RRHH))
    admin_rol = db.scalar(select(Rol).where(Rol.nombre == RolNombre.ADMINISTRADOR))
    
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "super")):
        db.add(UsuarioSistema(username="super", password_hash=hash_password("super123"), rol_id=super_rol.id, activo=True))
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "vigilante")):
        db.add(UsuarioSistema(username="vigilante", password_hash=hash_password("vigilante123"), rol_id=vigilante_rol.id, activo=True))
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "supervisor")):
        db.add(UsuarioSistema(username="supervisor", password_hash=hash_password("supervisor123"), rol_id=supervisor_rol.id, activo=True))
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "rrhh")):
        db.add(UsuarioSistema(username="rrhh", password_hash=hash_password("rrhh123"), rol_id=rrhh_rol.id, activo=True))
    if not db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "admin")):
        db.add(UsuarioSistema(username="admin", password_hash=hash_password("admin123"), rol_id=admin_rol.id, activo=True))
    db.flush()

    # Crear plantillas de turnos de ejemplo
    if not db.scalar(select(PlantillaTurno).where(PlantillaTurno.nombre == "Matutino")):
        plantilla_matutino = PlantillaTurno(nombre="Matutino", descripcion="Turno de 8:00 AM a 4:00 PM")
        db.add(plantilla_matutino)
        db.flush()

        # Lunes a viernes (0 = lunes, 4 = viernes)
        for dia in range(0, 5):
            db.add(DetallePlantillaTurno(
                plantilla_id=plantilla_matutino.id,
                dia_semana=dia,
                hora_entrada_oficial=time(8, 0),
                hora_salida_oficial=time(16, 0),
                tolerancia_minutos=15
            ))

    if not db.scalar(select(PlantillaTurno).where(PlantillaTurno.nombre == "Vespertino")):
        plantilla_vespertino = PlantillaTurno(nombre="Vespertino", descripcion="Turno de 2:00 PM a 10:00 PM")
        db.add(plantilla_vespertino)
        db.flush()

        # Lunes a viernes (0 = lunes, 4 = viernes)
        for dia in range(0, 5):
            db.add(DetallePlantillaTurno(
                plantilla_id=plantilla_vespertino.id,
                dia_semana=dia,
                hora_entrada_oficial=time(14, 0),
                hora_salida_oficial=time(22, 0),
                tolerancia_minutos=15
            ))

    if not db.scalar(select(PlantillaTurno).where(PlantillaTurno.nombre == "Mixto con descanso")):
        plantilla_mixto = PlantillaTurno(nombre="Mixto con descanso", descripcion="Turno mixto con día de descanso")
        db.add(plantilla_mixto)
        db.flush()

        # Lunes a sábado (0 = lunes, 5 = sábado), domingo (6) es descanso
        for dia in range(0, 6):
            db.add(DetallePlantillaTurno(
                plantilla_id=plantilla_mixto.id,
                dia_semana=dia,
                hora_entrada_oficial=time(8, 0) if dia != 5 else None,
                hora_salida_oficial=time(16, 0) if dia != 5 else None,
                tolerancia_minutos=15,
                es_descanso=(dia == 5)  # Sábado es descanso
            ))
    db.flush()

    # Crear empleados
    prod_dept = db.scalar(select(Departamento).where(Departamento.nombre == "Producción"))
    almacen_dept = db.scalar(select(Departamento).where(Departamento.nombre == "Almacén"))
    mant_dept = db.scalar(select(Departamento).where(Departamento.nombre == "Mantenimiento"))
    
    empleados_data = [
        ("EMP001", "Juan Pérez", prod_dept.id, "Operador"),
        ("EMP002", "María García", prod_dept.id, "Operador"),
        ("EMP003", "Carlos López", almacen_dept.id, "Almacenero"),
        ("EMP004", "Ana Martínez", almacen_dept.id, "Almacenero"),
        ("EMP005", "Pedro Sánchez", mant_dept.id, "Técnico"),
    ]
    
    empleados = []
    for num, nombre, dept_id, puesto in empleados_data:
        if not db.scalar(select(Empleado).where(Empleado.numero_empleado == num)):
            emp = Empleado(numero_empleado=num, nombre_completo=nombre, departamento_id=dept_id, puesto=puesto)
            db.add(emp)
            db.flush()
            empleados.append(emp)
    
    # Asignar supervisor a departamentos
    supervisor_user = db.scalar(select(UsuarioSistema).where(UsuarioSistema.username == "supervisor"))
    if supervisor_user:
        if not db.scalar(select(SupervisorDepartamento).where(
            SupervisorDepartamento.usuario_id == supervisor_user.id, 
            SupervisorDepartamento.departamento_id == prod_dept.id
        )):
            db.add(SupervisorDepartamento(usuario_id=supervisor_user.id, departamento_id=prod_dept.id))
        if not db.scalar(select(SupervisorDepartamento).where(
            SupervisorDepartamento.usuario_id == supervisor_user.id, 
            SupervisorDepartamento.departamento_id == almacen_dept.id
        )):
            db.add(SupervisorDepartamento(usuario_id=supervisor_user.id, departamento_id=almacen_dept.id))
    db.flush()

    # Asignar plantillas a algunos empleados
    if len(empleados) >= 2:
        empleados[0].plantilla_turno_id = plantilla_matutino.id
        empleados[1].plantilla_turno_id = plantilla_vespertino.id
        empleados[2].plantilla_turno_id = plantilla_mixto.id
    db.flush()

    # Crear turnos individuales para un empleado sin plantilla
    if len(empleados) >= 4:
        for dia in range(0, 5):
            db.add(TurnoHorario(
                empleado_id=empleados[3].id,
                dia_semana=dia,
                hora_entrada_oficial=time(9, 0),
                hora_salida_oficial=time(17, 0),
                tolerancia_minutos=15,
                es_descanso=False
            ))
    
    # Crear turnos por asistencia para un empleado
    if len(empleados) >= 5:
        for dia in range(0, 5):
            db.add(TurnoHorario(
                empleado_id=empleados[4].id,
                dia_semana=dia,
                hora_entrada_oficial=None,
                hora_salida_oficial=None,
                tolerancia_minutos=0,
                es_descanso=False,
                es_por_asistencia=True
            ))
    db.flush()

    # Crear registros de asistencia con pases de retardo y horas extra
    # Fecha actual: 3/06/2026
    hoy = date(2026, 6, 3)
    ayer = hoy - timedelta(days=1)
    anteayer = hoy - timedelta(days=2)
    hace_3_dias = hoy - timedelta(days=3)
    hace_4_dias = hoy - timedelta(days=4)
    hace_5_dias = hoy - timedelta(days=5)
    
    if len(empleados) >= 3:
        # 1. Registro con pase de retardo (expira en 15 minutos) - Proceso de retardos
        pase_expira = datetime(2026, 6, 3, 17, 15, tzinfo=None)
        reg1 = RegistroAsistencia(
            empleado_id=empleados[0].id,
            fecha_turno=hoy,
            hora_entrada_real=datetime(2026, 6, 3, 8, 20, tzinfo=None),  # 20 minutos tarde
            estado_registro=EstadoRegistro.INCIDENCIA,
            pase_espera_expira=pase_expira,
            minutos_extra_calculados=0,
            validacion_supervisor=False,
            validacion_rrhh=False
        )
        db.add(reg1)
        
        # 2. Registro con horas extra pendientes de validación - Horas extra
        reg2 = RegistroAsistencia(
            empleado_id=empleados[1].id,
            fecha_turno=ayer,
            hora_entrada_real=datetime(2026, 6, 2, 14, 0, tzinfo=None),
            hora_salida_real=datetime(2026, 6, 2, 23, 30, tzinfo=None),  # 1.5 horas extra
            estado_registro=EstadoRegistro.NORMAL,
            minutos_extra_calculados=90,
            validacion_supervisor=False,
            validacion_rrhh=False
        )
        db.add(reg2)
        
        # 3. Registro normal validado - Entradas/salidas normales
        reg3 = RegistroAsistencia(
            empleado_id=empleados[0].id,
            fecha_turno=anteayer,
            hora_entrada_real=datetime(2026, 6, 1, 8, 0, tzinfo=None),
            hora_salida_real=datetime(2026, 6, 1, 16, 0, tzinfo=None),
            estado_registro=EstadoRegistro.NORMAL,
            minutos_extra_calculados=0,
            validacion_supervisor=True,
            validacion_rrhh=True
        )
        db.add(reg3)
        
        # 4. Registro con incidencia pendiente de validación - Validación de incidencias
        reg4 = RegistroAsistencia(
            empleado_id=empleados[2].id,
            fecha_turno=hace_3_dias,
            hora_entrada_real=datetime(2026, 5, 31, 9, 30, tzinfo=None),  # 1.5 horas tarde
            hora_salida_real=datetime(2026, 5, 31, 16, 0, tzinfo=None),
            estado_registro=EstadoRegistro.INCIDENCIA,
            minutos_extra_calculados=0,
            validacion_supervisor=False,
            validacion_rrhh=False
        )
        db.add(reg4)
        
        # 5. Registro con horas extra validadas por supervisor pero pendiente RRHH
        reg5 = RegistroAsistencia(
            empleado_id=empleados[1].id,
            fecha_turno=hace_4_dias,
            hora_entrada_real=datetime(2026, 5, 30, 14, 0, tzinfo=None),
            hora_salida_real=datetime(2026, 5, 30, 22, 30, tzinfo=None),  # 30 minutos extra
            estado_registro=EstadoRegistro.NORMAL,
            minutos_extra_calculados=30,
            validacion_supervisor=True,
            validacion_rrhh=False
        )
        db.add(reg5)
        
        # 6. Registro normal sin validación pendiente
        reg6 = RegistroAsistencia(
            empleado_id=empleados[0].id,
            fecha_turno=hace_5_dias,
            hora_entrada_real=datetime(2026, 5, 29, 8, 5, tzinfo=None),
            hora_salida_real=datetime(2026, 5, 29, 16, 0, tzinfo=None),
            estado_registro=EstadoRegistro.NORMAL,
            minutos_extra_calculados=0,
            validacion_supervisor=True,
            validacion_rrhh=True
        )
        db.add(reg6)
        
        # 7. Registros de asistencia para empleado por asistencia
        if len(empleados) >= 5:
            # Registro del día actual
            reg7 = RegistroAsistencia(
                empleado_id=empleados[4].id,
                fecha_turno=hoy,
                hora_entrada_real=datetime(2026, 6, 3, 8, 30, tzinfo=None),
                hora_salida_real=datetime(2026, 6, 3, 17, 0, tzinfo=None),
                estado_registro=EstadoRegistro.NORMAL,
                minutos_extra_calculados=0,
                validacion_supervisor=True,
                validacion_rrhh=True
            )
            db.add(reg7)
            
            # Registro de ayer
            reg8 = RegistroAsistencia(
                empleado_id=empleados[4].id,
                fecha_turno=ayer,
                hora_entrada_real=datetime(2026, 6, 2, 9, 0, tzinfo=None),
                hora_salida_real=datetime(2026, 6, 2, 17, 30, tzinfo=None),
                estado_registro=EstadoRegistro.NORMAL,
                minutos_extra_calculados=0,
                validacion_supervisor=True,
                validacion_rrhh=True
            )
            db.add(reg8)
            
            # Registro de anteayer
            reg9 = RegistroAsistencia(
                empleado_id=empleados[4].id,
                fecha_turno=anteayer,
                hora_entrada_real=datetime(2026, 6, 1, 8, 0, tzinfo=None),
                hora_salida_real=datetime(2026, 6, 1, 16, 30, tzinfo=None),
                estado_registro=EstadoRegistro.NORMAL,
                minutos_extra_calculados=0,
                validacion_supervisor=True,
                validacion_rrhh=True
            )
            db.add(reg9)
            
            # Registro de hace 3 días
            reg10 = RegistroAsistencia(
                empleado_id=empleados[4].id,
                fecha_turno=hace_3_dias,
                hora_entrada_real=datetime(2026, 5, 31, 8, 15, tzinfo=None),
                hora_salida_real=datetime(2026, 5, 31, 17, 0, tzinfo=None),
                estado_registro=EstadoRegistro.NORMAL,
                minutos_extra_calculados=0,
                validacion_supervisor=True,
                validacion_rrhh=True
            )
            db.add(reg10)
            
            # Registro de hace 4 días
            reg11 = RegistroAsistencia(
                empleado_id=empleados[4].id,
                fecha_turno=hace_4_dias,
                hora_entrada_real=datetime(2026, 5, 30, 8, 0, tzinfo=None),
                hora_salida_real=datetime(2026, 5, 30, 16, 45, tzinfo=None),
                estado_registro=EstadoRegistro.NORMAL,
                minutos_extra_calculados=0,
                validacion_supervisor=True,
                validacion_rrhh=True
            )
            db.add(reg11)
    
    # Crear registros de ausencias de prueba
    if len(empleados) >= 3:
        # Vacaciones aprobadas
        aus1 = RegistroAusencia(
            empleado_id=empleados[0].id,
            tipo_ausencia=TipoAusencia.VACACIONES,
            fecha_inicio=date(2026, 6, 10),
            fecha_fin=date(2026, 6, 15),
            pagada=True,
            motivo="Vacaciones familiares",
            aprobado_rrhh=True,
            fecha_registro=datetime(2026, 5, 20, 10, 0, tzinfo=None)
        )
        db.add(aus1)
        
        # Incapacidad pendiente de aprobación
        aus2 = RegistroAusencia(
            empleado_id=empleados[1].id,
            tipo_ausencia=TipoAusencia.INCAPACIDAD,
            fecha_inicio=date(2026, 6, 5),
            fecha_fin=date(2026, 6, 7),
            pagada=True,
            motivo="Incapacidad médica",
            aprobado_rrhh=False,
            fecha_registro=datetime(2026, 6, 2, 9, 0, tzinfo=None)
        )
        db.add(aus2)
        
        # Permiso no pagado pendiente
        aus3 = RegistroAusencia(
            empleado_id=empleados[2].id,
            tipo_ausencia=TipoAusencia.PERMISO,
            fecha_inicio=date(2026, 6, 8),
            fecha_fin=date(2026, 6, 8),
            pagada=False,
            motivo="Trámite personal",
            aprobado_rrhh=False,
            fecha_registro=datetime(2026, 6, 2, 11, 0, tzinfo=None)
        )
        db.add(aus3)
    
    # Crear registros de fila virtual (visitantes externos)
    # Externo esperando andén
    externo1 = FilaExterno(
        tipo_visitante=TipoVisitante.EXTERNO,
        nombre_empresa="Transportes Express",
        chofer="Juan Pérez",
        placa="ABC-123",
        estado_fila=EstadoFila.ESPERA_AMARILLO,
        anden_asignado=None,
        hora_llegada=datetime(2026, 6, 5, 8, 30, tzinfo=None),
        hora_salida=None
    )
    db.add(externo1)
    
    # Proveedor de servicio adentro (sin andén)
    externo2 = FilaExterno(
        tipo_visitante=TipoVisitante.PROVEEDOR_SERVICIO,
        nombre_empresa="Servicios de Limpieza SA",
        chofer="María García",
        placa="XYZ-789",
        estado_fila=EstadoFila.ADENTRO_VERDE,
        anden_asignado=None,
        hora_llegada=datetime(2026, 6, 5, 9, 0, tzinfo=None),
        hora_salida=None
    )
    db.add(externo2)
    
    # Cliente esperando andén
    externo3 = FilaExterno(
        tipo_visitante=TipoVisitante.CLIENTE,
        nombre_empresa="Distribuidora Central",
        chofer="Pedro Sánchez",
        placa="DEF-456",
        estado_fila=EstadoFila.ESPERA_AMARILLO,
        anden_asignado=None,
        hora_llegada=datetime(2026, 6, 5, 10, 15, tzinfo=None),
        hora_salida=None
    )
    db.add(externo3)
    
    # Externo con andén asignado y adentro
    externo4 = FilaExterno(
        tipo_visitante=TipoVisitante.EXTERNO,
        nombre_empresa="Logística Norte",
        chofer="Ana Martínez",
        placa="GHI-012",
        estado_fila=EstadoFila.ADENTRO_VERDE,
        anden_asignado="Andén 3",
        hora_llegada=datetime(2026, 6, 5, 7, 45, tzinfo=None),
        hora_salida=None
    )
    db.add(externo4)
    
    # Externo retirado (histórico)
    externo5 = FilaExterno(
        tipo_visitante=TipoVisitante.EXTERNO,
        nombre_empresa="Cargas Rápidas",
        chofer="Carlos López",
        placa="JKL-345",
        estado_fila=EstadoFila.RETIRADO,
        anden_asignado="Andén 1",
        hora_llegada=datetime(2026, 6, 4, 14, 0, tzinfo=None),
        hora_salida=datetime(2026, 6, 4, 16, 30, tzinfo=None)
    )
    db.add(externo5)
    
    db.commit()

print("Seed completado")
