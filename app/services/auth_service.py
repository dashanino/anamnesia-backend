from sqlalchemy import select
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
    
)

from app.extensions import db
from app.models.user import User
from app.services.user_service import create_user
from app.models.role import Role


def register_service(document_type, document_number, first_names, last_names, email, phone, password): 
    #CREA SIEMPRE PACIENTES!
    # Busca el rol "patient" — nunca permite que el registro público elija el rol
    patient_role = db.session.execute(
        select(Role).where(Role.name == "patient")
    ).scalar_one_or_none()

    if patient_role is None:
        raise ValueError("Patient role not configured")

    # Reutiliza create_user, pero FORZANDO el rol, sin dejar que el cliente lo elija
    return create_user(
        id_role=patient_role.id,
        document_type=document_type,
        document_number=document_number,
        first_names=first_names,
        last_names=last_names,
        email=email,
        phone=phone,
        password=password,
    )


def login_service(document_number,password):
    user = (
        user.query.filter_by(
            document_number=document_number
        ).first()
    )
    if not user:
        return {"message": "documento inválido"}

    if not user.check_password(password):
        return {"message": "Contraseña inválida"}

    return {'message': 'login exitoso',
            'user': {
                'id':user.id,
                'document_number': user.document_number
            }}
            
