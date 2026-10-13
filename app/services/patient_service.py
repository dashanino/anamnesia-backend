from app.extensions import db
from sqlalchemy import select
from app.models.patient import Patient
from app.models.user import User
from app.models.eps import EPS


def create_patient(user_id, id_eps=None, birth_date=None, sex=None):
    # Validar que el usuario exista
    user = db.session.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if user is None:
        raise ValueError("User not found")

    # Validar que ese usuario no tenga ya un paciente asociado (relación 1:1)
    existing_patient = db.session.execute(
        select(Patient).where(Patient.user_id == user_id)
    ).scalar_one_or_none()

    if existing_patient:
        raise ValueError("User already has a patient profile")

    # Validar que la EPS exista, si se envió
    if id_eps is not None:
        eps = db.session.execute(
            select(EPS).where(EPS.id == id_eps)
        ).scalar_one_or_none()

        if eps is None:
            raise ValueError("EPS not found")

    patient = Patient(
        user_id=user_id,
        id_eps=id_eps,
        birth_date=birth_date,
        sex=sex
    )

    db.session.add(patient)
    db.session.commit()

    return patient


def get_patient_by_id(patient_id):
    return db.session.execute(
        select(Patient).where(Patient.id == patient_id)
    ).scalar_one_or_none()


def get_patient_by_user_id(user_id):
    return db.session.execute(
        select(Patient).where(Patient.user_id == user_id)
    ).scalar_one_or_none()


def update_patient(patient_id, id_eps=None, birth_date=None, sex=None):
    patient = get_patient_by_id(patient_id)

    if patient is None:
        raise ValueError("Patient not found")

    if id_eps is not None:
        eps = db.session.execute(
            select(EPS).where(EPS.id == id_eps)
        ).scalar_one_or_none()

        if eps is None:
            raise ValueError("EPS not found")

        patient.id_eps = id_eps

    if birth_date is not None:
        patient.birth_date = birth_date

    if sex is not None:
        patient.sex = sex

    db.session.commit()

    return patient