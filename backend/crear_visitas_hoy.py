from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Visita, RegistroAsistencia, EventoAsistencia, TipoEvento, Empleado, TurnoHorario
from datetime import datetime, time

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

print("=" * 80)
print("CREANDO VISITAS PARA BLOQUES FUERA DE HORARIO DE HOY")
print("=" * 80)

hoy = datetime(2026, 7, 1).date()
asistencias_hoy = session.scalars(
    select(RegistroAsistencia).where(RegistroAsistencia.fecha_turno == hoy)
).all()

for asistencia in asistencias_hoy:
    emp = session.get(Empleado, asistencia.empleado_id)
    print(f"\nAsistencia ID: {asistencia.id} - {emp.nombre_completo}")
    
    # Obtener turno del empleado
    turno = session.scalar(
        select(TurnoHorario).where(
            TurnoHorario.empleado_id == emp.id,
            TurnoHorario.dia_semana == hoy.weekday()
        )
    )
    
    if not turno:
        # Intentar buscar cualquier turno del empleado
        turnos = session.scalars(
            select(TurnoHorario).where(TurnoHorario.empleado_id == emp.id)
        ).all()
        print(f"  Turnos encontrados: {len(turnos)}")
        if turnos:
            # Usar el primer turno encontrado
            turno = turnos[0]
            print(f"  Usando turno del día {turno.dia_semana}")
        else:
            print("  Sin turno definido")
            continue
    
    hora_entrada_oficial = datetime.combine(hoy, turno.hora_entrada_oficial)
    hora_salida_oficial = datetime.combine(hoy, turno.hora_salida_oficial)
    print(f"  Horario oficial: {hora_entrada_oficial.strftime('%H:%M')} - {hora_salida_oficial.strftime('%H:%M')}")
    
    # Obtener eventos
    eventos = session.scalars(
        select(EventoAsistencia).where(
            EventoAsistencia.asistencia_id == asistencia.id
        ).order_by(EventoAsistencia.fecha_evento)
    ).all()
    
    # Agrupar en bloques
    bloques = []
    i = 0
    while i < len(eventos):
        if eventos[i].tipo_evento == TipoEvento.ENTRADA:
            entrada = eventos[i].fecha_evento
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
    
    print(f"  Bloques detectados: {len(bloques)}")
    
    for idx, (entrada, salida) in enumerate(bloques):
        entrada_fuera = entrada < hora_entrada_oficial or entrada > hora_salida_oficial
        salida_fuera = salida < hora_entrada_oficial or salida > hora_salida_oficial
        
        print(f"    Bloque {idx + 1}: {entrada.strftime('%H:%M')} - {salida.strftime('%H:%M')}")
        print(f"      Entrada fuera: {entrada_fuera}, Salida fuera: {salida_fuera}")
        
        if entrada_fuera and salida_fuera:
            # Verificar si ya existe visita
            visita_existente = session.scalar(
                select(Visita).where(
                    Visita.empleado_id == emp.id,
                    Visita.asistencia_id == asistencia.id,
                    Visita.hora_inicio == entrada
                )
            )
            
            if not visita_existente:
                from app.services import crear_visita
                visita = crear_visita(
                    db=session,
                    empleado_id=emp.id,
                    asistencia_id=asistencia.id,
                    hora_fin=salida,
                    minutos_duracion=int((salida - entrada).total_seconds() / 60),
                    motivo="Visita fuera de horario",
                    hora_inicio=entrada
                )
                print(f"      -> Creada visita ID {visita.id}")
            else:
                print(f"      -> Ya existe visita ID {visita_existente.id}")

session.commit()

print("\n" + "=" * 80)
print("VISITAS CREADAS HOY")
print("=" * 80)
visitas_hoy = session.scalars(
    select(Visita).where(Visita.fecha_visita >= datetime.combine(hoy, datetime.min.time()))
).all()

print(f"Total visitas de hoy: {len(visitas_hoy)}")
for v in visitas_hoy:
    emp = session.get(Empleado, v.empleado_id)
    print(f"ID: {v.id}, Empleado: {emp.nombre_completo}, Hora inicio: {v.hora_inicio.strftime('%H:%M')}, Hora fin: {v.hora_fin.strftime('%H:%M')}, Minutos: {v.minutos_duracion}, Estado: {v.estado.value}")
