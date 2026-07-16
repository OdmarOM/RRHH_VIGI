from app.core.database import SessionLocal
from app.models import Empleado
from app.services import get_empleado_turno
from datetime import date, timedelta


def test():
    db = SessionLocal()
    emp = db.query(Empleado).filter(Empleado.numero_empleado == 'EMP471').first()
    if not emp:
        print('EMP471 no encontrado')
        return
    print(f'Empleado {emp.numero_empleado}, plantilla_turno_id={emp.plantilla_turno_id}')
    for i in range(10):
        d = date(2026, 7, 13) + timedelta(weeks=i)
        turno = get_empleado_turno(db, emp, d.weekday(), d)
        print(d, d.strftime('%A'), turno)


if __name__ == "__main__":
    test()
