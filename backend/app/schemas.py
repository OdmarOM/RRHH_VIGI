from datetime import datetime, time, date
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from app.models import EstadoEmpleado, EstadoFila, EstadoRegistro, EstadoSalida, EstadoVisita, RolNombre, TipoAusencia, TipoSalida, TipoEvento, TipoVisitante


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: RolNombre


class LoginRequest(BaseModel):
    username: str
    password: str


class DepartamentoBase(BaseModel):
    nombre: str


class DepartamentoOut(DepartamentoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class EmpleadoCreate(BaseModel):
    numero_empleado: str
    nombre_completo: str
    departamento_id: int
    puesto: str
    activo: bool = True
    fecha_inicio_ciclo: date | None = None


class EmpleadoUpdate(BaseModel):
    nombre_completo: str | None = None
    departamento_id: int | None = None
    puesto: str | None = None
    activo: bool | None = None
    estado_actual: EstadoEmpleado | None = None
    fecha_inicio_ciclo: date | None = None


class EmpleadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    numero_empleado: str
    nombre_completo: str
    departamento_id: int
    puesto: str
    estado_actual: EstadoEmpleado
    activo: bool
    plantilla_turno_id: int | None = None
    fecha_inicio_ciclo: date | None = None


class ImportarEmpleadosResponse(BaseModel):
    exitosos: int
    errores: list[dict]
    total_procesados: int


class PlantillaTurnoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    descripcion: str | None = None
    es_rotativa: bool = False
    ciclo_rotacion_semanas: int = 2
    fecha_inicio_ciclo: date = Field(default_factory=date.today)
    plantilla_semana_par_id: int | None = None
    plantilla_semana_impar_id: int | None = None
    plantilla_semana_3_id: int | None = None


class DetallePlantillaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plantilla_id: int
    dia_semana: int
    hora_entrada_oficial: time | None = None
    hora_salida_oficial: time | None = None
    tolerancia_minutos: int
    es_descanso: bool
    es_por_asistencia: bool

    @field_serializer('hora_entrada_oficial', 'hora_salida_oficial')
    def serialize_time(self, value: time | None):
        return value.strftime("%H:%M") if value else None


class DetallePlantillaCreate(BaseModel):
    dia_semana: int = Field(ge=0, le=6)
    hora_entrada_oficial: time | None = None
    hora_salida_oficial: time | None = None
    tolerancia_minutos: int = 15
    es_descanso: bool = False
    es_por_asistencia: bool = False


class DetallePlantillaUpdate(BaseModel):
    dia_semana: int | None = Field(None, ge=0, le=6)
    hora_entrada_oficial: time | None = None
    hora_salida_oficial: time | None = None
    tolerancia_minutos: int | None = None
    es_descanso: bool | None = None
    es_por_asistencia: bool | None = None


class TurnoCreate(BaseModel):
    empleado_id: int
    dia_semana: int = Field(ge=0, le=6)
    hora_entrada_oficial: time | None = None
    hora_salida_oficial: time | None = None
    tolerancia_minutos: int = 15
    tolerancia_entrada_previa_minutos: int = 15
    tolerancia_salida_posterior_minutos: int = 15
    tolerancia_salida_previa_minutos: int = 5
    es_descanso: bool = False
    es_por_asistencia: bool = False

    @field_validator('hora_entrada_oficial', 'hora_salida_oficial', mode='before')
    @classmethod
    def parse_time(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return time.fromisoformat(v)
        return v


class TurnoDescansoUpdate(BaseModel):
    es_descanso: bool


class TurnoUpdate(BaseModel):
    hora_entrada_oficial: time | None = None
    hora_salida_oficial: time | None = None
    tolerancia_minutos: int | None = None
    tolerancia_entrada_previa_minutos: int | None = None
    tolerancia_salida_posterior_minutos: int | None = None
    tolerancia_salida_previa_minutos: int | None = None
    es_descanso: bool | None = None
    es_por_asistencia: bool | None = None

    @field_validator('hora_entrada_oficial', 'hora_salida_oficial', mode='before')
    @classmethod
    def parse_time(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return time.fromisoformat(v)
        return v


class TurnoOut(TurnoCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

    @field_serializer('hora_entrada_oficial', 'hora_salida_oficial')
    def serialize_time(self, value: time | None):
        return value.strftime("%H:%M") if value else None


class AsistenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empleado_id: int
    fecha_turno: datetime | str
    hora_entrada_real: datetime | None
    hora_salida_real: datetime | None
    estado_registro: EstadoRegistro
    pase_espera_expira: datetime | None
    validacion_supervisor: bool
    validacion_rrhh: bool


class ScanResponse(BaseModel):
    empleado_id: int
    asistencia_id: int
    estado_empleado: EstadoEmpleado
    estado_registro: EstadoRegistro
    mensaje: str
    pase_espera_expira: datetime | None = None


class EntradaRequest(BaseModel):
    empleado_id: int
    observaciones: list[str] = []


class SalidaTemporalCreate(BaseModel):
    empleado_id: int
    tipo_salida: TipoSalida


class RegresoSalidaTemporalRequest(BaseModel):
    empleado_id: int


class SalidaTemporalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asistencia_id: int
    tipo_salida: TipoSalida
    hora_salida: datetime
    hora_regreso: datetime | None
    estado_salida: EstadoSalida


class FilaExternoCreate(BaseModel):
    tipo_visitante: TipoVisitante
    nombre_empresa: str
    chofer: str | None = None
    placa: str | None = None


class FilaExternoAsignar(BaseModel):
    anden_asignado: str


class FilaExternoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo_visitante: str
    nombre_empresa: str
    chofer: str | None
    placa: str | None
    estado_fila: EstadoFila
    anden_asignado: str | None
    hora_llegada: datetime
    hora_entrada_almacen: datetime | None
    hora_salida: datetime | None


class AusenciaCreate(BaseModel):
    empleado_id: int
    tipo_ausencia: TipoAusencia
    fecha_inicio: date
    fecha_fin: date
    pagada: bool = True
    porcentaje_aportacion: int = 100  # Para incapacidades (0-100)
    motivo: str | None = None


class AusenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empleado_id: int
    tipo_ausencia: TipoAusencia
    fecha_inicio: date
    fecha_fin: date
    pagada: bool
    porcentaje_aportacion: int
    motivo: str | None
    aprobado_rrhh: bool
    fecha_registro: datetime


class EventoAsistenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empleado_id: int
    asistencia_id: int | None
    tipo_evento: TipoEvento
    fecha_evento: datetime
    observaciones: str | None
    tipo_salida: str | None


class VisitaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empleado_id: int
    asistencia_id: int
    fecha_visita: datetime
    hora_inicio: datetime | None
    hora_fin: datetime | None
    minutos_duracion: int | None
    estado: EstadoVisita
    autorizado_por: int | None
    fecha_autorizacion: datetime | None
    motivo: str | None


class VisitaUpdate(BaseModel):
    estado: EstadoVisita
    motivo: str | None = None


class CorreccionManualOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empleado_id: int
    fecha: date
    tipo_correccion: str
    minutos_agregados: float
    motivo: str
    autorizado_por: int
    fecha_registro: datetime


class CorreccionManualCreate(BaseModel):
    empleado_id: int
    fecha: date
    tipo_correccion: str
    minutos_agregados: float
    motivo: str
