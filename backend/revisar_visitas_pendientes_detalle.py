from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, Empleado, RegistroAsistencia, EventoAsistencia, TipoEvento
from datetime import datetime

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("=" * 80)
print("VISITAS PENDIENTES (sin hora_fin)")
print("=" * 80)
visitas_pendientes = session.scalars(
    select(Visita).where(Visita.hora_fin.is_(None))
).all()

for v in visitas_pendientes:
    emp = session.get(Empleado, v.empleado_id)
    asistencia = session.get(RegistroAsistencia, v.asistencia_id)
    print(f"Visita ID: {v.id}")
    print(f"  Empleado: {emp.nombre_completo if emp else 'N/A'} (ID: {v.empleado_id})")
    print(f"  Asistencia ID: {v.asistencia_id}")
    print(f"  Fecha visita: {v.fecha_visita}")
    print(f"  Hora inicio: {v.hora_inicio}")
    print(f"  Hora fin: {v.hora_fin}")
    print(f"  Minutos duración: {v.minutos_duracion}")
    print(f"  Estado: {v.estado.value}")
    print(f"  Motivo: {v.motivo}")
    
    if asistencia:
        print(f"  Asistencia:")
        print(f"    Fecha turno: {asistencia.fecha_turno}")
        print(f"    Hora entrada: {asistencia.hora_entrada_real}")
        print(f"    Hora salida: {asistencia.hora_salida_real}")
        print(f"    Estado registro: {asistencia.estado_registro}")
        
        # Mostrar eventos de esta asistencia
        eventos = session.scalars(
            select(EventoAsistencia).where(EventoAsistencia.asistencia_id == asistencia.id)
            .order_by(EventoAsistencia.fecha_evento)
        ).all()
        print(f"  Eventos ({len(eventos)}):")
        for e in eventos:
            print(f"    {e.tipo_evento.value}: {e.fecha_evento} - {e.observaciones}")
    
    print("-" * 80)
