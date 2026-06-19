from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date
from app.models import RegistroAsistencia, Empleado, EventoAsistencia

engine = create_engine('sqlite:///rrhh_dev.db')
session = Session(engine)

emp = session.scalar(select(Empleado).where(Empleado.numero_empleado == 'EMP001'))
fecha_prueba = date(2026, 6, 18)

eventos = session.scalars(select(EventoAsistencia).where(
    EventoAsistencia.empleado_id == emp.id,
    EventoAsistencia.fecha_evento >= fecha_prueba,
    EventoAsistencia.fecha_evento < fecha_prueba.replace(day=fecha_prueba.day + 1)
)).all()

print(f'Cálculo manual para {emp.nombre_completo} el {fecha_prueba}:')
print(f'Entrada: {eventos[0].fecha_evento}')
print(f'Salida a comida: {eventos[1].fecha_evento}')
print(f'Regreso de comida: {eventos[2].fecha_evento}')
print(f'Salida a permiso: {eventos[3].fecha_evento}')
print(f'Regreso de permiso: {eventos[4].fecha_evento}')
print(f'Salida final: {eventos[5].fecha_evento}')

bloque1 = (eventos[1].fecha_evento - eventos[0].fecha_evento).total_seconds() / 60
bloque2 = (eventos[2].fecha_evento - eventos[1].fecha_evento).total_seconds() / 60
bloque3 = (eventos[3].fecha_evento - eventos[2].fecha_evento).total_seconds() / 60
bloque4 = (eventos[4].fecha_evento - eventos[3].fecha_evento).total_seconds() / 60
bloque5 = (eventos[5].fecha_evento - eventos[4].fecha_evento).total_seconds() / 60

print(f'\nBloques:')
print(f'Bloque 1 (entrada - salida comida): {bloque1:.2f} minutos')
print(f'Bloque 2 (comida): {bloque2:.2f} minutos (NO descuenta)')
print(f'Bloque 3 (regreso comida - salida permiso): {bloque3:.2f} minutos')
print(f'Bloque 4 (permiso): {bloque4:.2f} minutos (descuenta)')
print(f'Bloque 5 (regreso permiso - salida final): {bloque5:.2f} minutos')

total = bloque1 + bloque2 + bloque3 + bloque5
print(f'\nTotal sin descuentos: {total:.2f} minutos')
print(f'Menos permiso: {bloque4:.2f} minutos')
print(f'Resultado: {total - bloque4:.2f} minutos = {(total - bloque4)/60:.2f} horas')
