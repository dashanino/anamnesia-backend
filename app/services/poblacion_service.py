from app.extensions import db
from sqlalchemy import select
from app.models.poblacion import Poblacion


def get_all_poblaciones():
    return db.session.execute(
        select(Poblacion).where(Poblacion.is_active == True)
    ).scalars().all()


def create_poblacion(name, description=None):
    existing = db.session.execute(
        select(Poblacion).where(Poblacion.name == name)
    ).scalar_one_or_none()

    if existing:
        raise ValueError("Población ya existe")

    poblacion = Poblacion(name=name, description=description)
    db.session.add(poblacion)
    db.session.commit()

    return poblacion