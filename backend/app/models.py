from datetime import date, datetime, time
from enum import StrEnum
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class RolNombre(StrEnum):
    VIGILANTE = "Vigilante"
    SUPERVISOR = "Supervisor"
    RRHH = "RRHH"
    ADMINISTRADOR = "Administrador"
    SUPERUSUARIO = "Superusuario"


class EstadoEmpleado(StrEnum):
    FUERA = "Fuera"
    LABORANDO = "Laborando"
    SALIDA_TEMPORAL = "Salida_Temporal"
    EN_ESPERA_PASE = "En_Espera_Pase"


class EstadoRegistro(StrEnum):
    NORMAL = "Normal"
    RETARDO_APROBADO = "Retardo_Aprobado"
    INCIDENCIA = "Incidencia"
    VISITA_DESCANSO = "Visita_Descanso"
    FALTA = "Falta"


class TipoSalida(StrEnum):
    MANDADO_TRABAJO = "Mandado_Trabajo"
    PERMISO_PERSONAL = "Permiso_Personal"
    COMER = "Comer"


class EstadoFila(StrEnum):
    ESPERA_AMARILLO = "Espera_Amarillo"
    ADENTRO_VERDE = "Adentro_Verde"
    RETIRADO = "Retirado"


class TipoVisitante(StrEnum):
    EXTERNO = "Externo"
    PROVEEDOR_SERVICIO = "Proveedor_Servicio"
    CLIENTE = "Cliente"


class EstadoSalida(StrEnum):
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class Departamento(Base):
    __tablename__ = "departamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[RolNombre] = mapped_column(Enum(RolNombre), unique=True, nullable=False)


class Empleado(Base):
    __tablename__ = "empleados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    numero_empleado: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(180), nullable=False)
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamentos.id"), nullable=False)
    puesto: Mapped[str] = mapped_column(String(120), nullable=False)
    plantilla_turno_id: Mapped[int | None] = mapped_column(ForeignKey("plantillas_turnos.id"), nullable=True)
    estado_actual: Mapped[EstadoEmpleado] = mapped_column(Enum(EstadoEmpleado), default=EstadoEmpleado.FUERA, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    departamento: Mapped[Departamento] = relationship()


class UsuarioSistema(Base):
    __tablename__ = "usuarios_sistema"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empleado_id: Mapped[int | None] = mapped_column(ForeignKey("empleados.id"), nullable=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    empleado: Mapped[Empleado | None] = relationship()
    rol: Mapped[Rol] = relationship()


class SupervisorDepartamento(Base):
    __tablename__ = "supervisores_departamentos"
    __table_args__ = (UniqueConstraint("usuario_id", "departamento_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios_sistema.id"), nullable=False)
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamentos.id"), nullable=False)

    usuario_sistema: Mapped[UsuarioSistema] = relationship()
    departamento: Mapped[Departamento] = relationship()


class TurnoHorario(Base):
    __tablename__ = "turnos_horarios"
    __table_args__ = (UniqueConstraint("empleado_id", "dia_semana"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleados.id"), nullable=False)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_entrada_oficial: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_salida_oficial: Mapped[time | None] = mapped_column(Time, nullable=True)
    tolerancia_minutos: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    tolerancia_entrada_previa_minutos: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    tolerancia_salida_posterior_minutos: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    tolerancia_salida_previa_minutos: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    es_descanso: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    es_por_asistencia: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PlantillaTurno(Base):
    __tablename__ = "plantillas_turnos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)


class DetallePlantillaTurno(Base):
    __tablename__ = "detalles_plantilla_turno"
    __table_args__ = (UniqueConstraint("plantilla_id", "dia_semana"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plantilla_id: Mapped[int] = mapped_column(ForeignKey("plantillas_turnos.id"), nullable=False)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_entrada_oficial: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_salida_oficial: Mapped[time | None] = mapped_column(Time, nullable=True)
    tolerancia_minutos: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    tolerancia_entrada_previa_minutos: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    tolerancia_salida_posterior_minutos: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    tolerancia_salida_previa_minutos: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    es_descanso: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    es_por_asistencia: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RegistroAsistencia(Base):
    __tablename__ = "registro_asistencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleados.id"), nullable=False, index=True)
    vigilante_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios_sistema.id"), nullable=True)
    fecha_turno: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fecha_entrada_turno: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)  # Para turnos nocturnos que cruzan medianoche
    hora_entrada_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hora_salida_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado_registro: Mapped[EstadoRegistro] = mapped_column(Enum(EstadoRegistro), default=EstadoRegistro.NORMAL, nullable=False)
    pase_espera_expira: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    minutos_extra_calculados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    validacion_supervisor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validacion_rrhh: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    autorizacion_horas_extra_rrhh: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    omision_salida_detectada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hora_cierre_automatico: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    empleado: Mapped[Empleado] = relationship()


class BloqueHorasExtra(Base):
    __tablename__ = "bloques_horas_extra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asistencia_id: Mapped[int] = mapped_column(ForeignKey("registro_asistencias.id"), nullable=False)
    tipo_bloque: Mapped[str] = mapped_column(String(20), nullable=False)  # "ANTES_INICIO" o "DESPUES_FIN"
    hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hora_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    minutos_extra: Mapped[int] = mapped_column(Integer, nullable=False)
    validacion_supervisor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validacion_rrhh: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    asistencia: Mapped[RegistroAsistencia] = relationship()


class ObservacionCaseta(Base):
    __tablename__ = "observaciones_caseta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asistencia_id: Mapped[int] = mapped_column(ForeignKey("registro_asistencias.id"), nullable=False)
    tipo_observacion: Mapped[str] = mapped_column(String(120), nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TipoEvento(StrEnum):
    ENTRADA = "Entrada"
    SALIDA = "Salida"
    SALIDA_TEMPORAL = "Salida_Temporal"
    REGRESO_SALIDA_TEMPORAL = "Regreso_Salida_Temporal"


class EventoAsistencia(Base):
    __tablename__ = "eventos_asistencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleados.id"), nullable=False, index=True)
    asistencia_id: Mapped[int | None] = mapped_column(ForeignKey("registro_asistencias.id"), nullable=True)
    tipo_evento: Mapped[TipoEvento] = mapped_column(Enum(TipoEvento), nullable=False)
    fecha_evento: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observaciones: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tipo_salida: Mapped[str | None] = mapped_column(String(80), nullable=True)  # Para salidas temporales

    empleado: Mapped[Empleado] = relationship()
    asistencia: Mapped["RegistroAsistencia"] = relationship()


class EstadoVisita(StrEnum):
    PENDIENTE = "Pendiente"
    PAGADA = "Pagada"
    NO_PAGADA = "No_Pagada"


class Visita(Base):
    __tablename__ = "visitas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleados.id"), nullable=False, index=True)
    asistencia_id: Mapped[int] = mapped_column(ForeignKey("registro_asistencias.id"), nullable=False)
    fecha_visita: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hora_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hora_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    minutos_duracion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[EstadoVisita] = mapped_column(Enum(EstadoVisita), nullable=False, default=EstadoVisita.PENDIENTE)
    autorizado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios_sistema.id"), nullable=True)
    fecha_autorizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)

    empleado: Mapped[Empleado] = relationship()
    asistencia: Mapped["RegistroAsistencia"] = relationship()
    autorizado_por_usuario: Mapped["UsuarioSistema"] = relationship(foreign_keys=[autorizado_por])


class TipoAusencia(StrEnum):
    VACACIONES = "Vacaciones"
    INCAPACIDAD = "Incapacidad"
    PERMISO = "Permiso"


class RegistroAusencia(Base):
    __tablename__ = "registro_ausencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleados.id"), nullable=False, index=True)
    tipo_ausencia: Mapped[TipoAusencia] = mapped_column(Enum(TipoAusencia), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    pagada: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    porcentaje_aportacion: Mapped[int] = mapped_column(Integer, default=100, nullable=False)  # Para incapacidades (0-100)
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    aprobado_rrhh: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    empleado: Mapped[Empleado] = relationship()


class SalidaTemporal(Base):
    __tablename__ = "salidas_temporales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asistencia_id: Mapped[int] = mapped_column(ForeignKey("registro_asistencias.id"), nullable=False)
    tipo_salida: Mapped[TipoSalida] = mapped_column(Enum(TipoSalida), nullable=False)
    hora_salida: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hora_regreso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado_salida: Mapped[EstadoSalida] = mapped_column(Enum(EstadoSalida), default=EstadoSalida.ABIERTA, nullable=False)
    minutos_descontados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    descuenta_tiempo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class FilaExterno(Base):
    __tablename__ = "fila_externos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_visitante: Mapped[TipoVisitante] = mapped_column(Enum(TipoVisitante), nullable=False)
    nombre_empresa: Mapped[str] = mapped_column(String(160), nullable=False)
    chofer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    placa: Mapped[str | None] = mapped_column(String(40), nullable=True)
    vigilante_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios_sistema.id"), nullable=True)
    estado_fila: Mapped[EstadoFila] = mapped_column(Enum(EstadoFila), default=EstadoFila.ESPERA_AMARILLO, nullable=False)
    anden_asignado: Mapped[str | None] = mapped_column(String(40), nullable=True)
    hora_llegada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hora_entrada_almacen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hora_salida: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latitud: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitud: Mapped[float | None] = mapped_column(Float, nullable=True)


class EvidenciaFotografica(Base):
    __tablename__ = "evidencias_fotograficas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referencia_id: Mapped[int] = mapped_column(Integer, nullable=False)
    referencia_tipo: Mapped[str] = mapped_column(String(50), nullable=False)  # 'fila_externo' u otros
    ruta_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_captura: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TipoCorreccion(StrEnum):
    HORAS_LABORADAS = "Horas_Laboradas"
    HORAS_EXTRA = "Horas_Extra"
    INCIDENCIA = "Incidencia"
    PERMISO = "Permiso"


class CorreccionManual(Base):
    __tablename__ = "correcciones_manuales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleados.id"), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tipo_correccion: Mapped[TipoCorreccion] = mapped_column(Enum(TipoCorreccion), nullable=False)
    minutos_agregados: Mapped[float] = mapped_column(Float, nullable=False)  # Minutos a agregar (positivo) o restar (negativo), puede ser decimal
    motivo: Mapped[str] = mapped_column(String(200), nullable=False)
    autorizado_por: Mapped[int] = mapped_column(ForeignKey("usuarios_sistema.id"), nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    empleado: Mapped[Empleado] = relationship()
    autorizador: Mapped[UsuarioSistema] = relationship(foreign_keys=[autorizado_por])
