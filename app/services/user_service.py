from app.extensions import db
from sqlalchemy import select, or_
from werkzeug.security import generate_password_hash

from app.models.user import User
from app.models.role import Role


def create_user( #CREA USUARIOS: USERNN Y PATIENT
    id_role,
    document_type=None,
    document_number=None,
    first_names=None,
    last_names=None,
    email=None,
    phone=None,
    password=None
):
    # Comprobar que el rol exista
    role = db.session.execute(
        select(Role).where(Role.id == id_role)
    ).scalar_one_or_none()
    

    if role is None:
        raise ValueError("Role not found")

    # Usuario no registrado
    if role.name == "usernn":

        user = User(
            id_role=role.id
        )

        db.session.add(user)
        db.session.commit()

        return user

    # Registro de paciente
    if role.name == "patient":

        campos_requeridos = {
            "document_type": document_type,
            "document_number": document_number,
            "first_names": first_names,
            "last_names": last_names,
            "email": email,
            "phone": phone,
            "password": password
        }

        faltantes = [
            campo
            for campo, valor in campos_requeridos.items()
            if not valor
        ]

        if faltantes:
            raise ValueError(
                "Missing required fields: "
                + ", ".join(faltantes)
            )

        # Comprobar datos duplicados
        existing_users = db.session.execute(
            select(User).where(
                or_(
                    User.email == email,
                    User.document_number == document_number,
                    User.phone == phone
                )
            )
        ).scalars().all()

        for user in existing_users:

            if user.email == email:
                raise ValueError("Email already registered")

            if user.document_number == document_number:
                raise ValueError("Document already registered")

            if user.phone == phone:
                raise ValueError("Phone already registered")

        user = User(
            id_role=role.id,
            document_type=document_type,
            document_number=document_number,
            first_names=first_names,
            last_names=last_names,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()
        

        return user

    raise ValueError(
        "This service only creates patients and UserNN"
    )


def get_user_by_id(user_id):

    return db.session.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()




def update_user(
    user_id,
    id_role=None,
    first_names=None,
    last_names=None,
    email=None,
    phone=None,
    document_number=None
):
    user = get_user_by_id(user_id)

    if user is None:
        raise ValueError("User not found")

    if id_role is not None:
        role = db.session.execute(
            select(Role).where(Role.id == id_role)
        ).scalar_one_or_none()

        if role is None:
            raise ValueError("Role not found")

        user.id_role = id_role

    if phone is not None and phone != user.phone:
        existing_phone = db.session.execute(
            select(User).where(User.phone == phone)
        ).scalar_one_or_none()
        if existing_phone:
            raise ValueError("Phone already registered")
        user.phone = phone

    if email is not None and email != user.email:
        existing_email = db.session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        if existing_email:
            raise ValueError("Email already registered")
        user.email = email

    if first_names is not None:
        user.first_names = first_names

    if last_names is not None:
        user.last_names = last_names

    if document_number is not None:
        user.document_number = document_number

    db.session.commit()

    return user


def deactivate_user(user_id):

    user = get_user_by_id(user_id)

    if user is None:
        raise ValueError("User not found")

    user.is_active = False

    db.session.commit()

    return user

def activate_user(user_id):

    user = get_user_by_id(user_id)

    if user is None:
        raise ValueError("User not found")

    user.is_active = True

    db.session.commit()

    return user