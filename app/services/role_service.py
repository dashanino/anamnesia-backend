from app.extensions import db
from sqlalchemy import select
from app.models.role import Role


def get_all_roles():
    return db.session.execute(
        select(Role).where(Role.is_active == True)
    ).scalars().all()


def create_role(name, description=None):
    existing = db.session.execute(
        select(Role).where(Role.name == name)
    ).scalar_one_or_none()

    if existing:
        raise ValueError("Role ya existe")

    role = Role(name=name, description=description)
    db.session.add(role)
    db.session.commit()

    return role