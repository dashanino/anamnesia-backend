from app.extensions import db
from sqlalchemy import select, delete
from app.models.patient_antecedente import PatientAntecedente
from app.models.patient import Patient
from app.models.antecedente import Antecedente


def get_antecedentes_by_patient(patient_id):
    return db.session.execute(
        select(PatientAntecedente).where(
            PatientAntecedente.id_paciente == patient_id
        )
    ).scalars().all()


def set_antecedentes_for_patient(patient_id, antecedente_ids: list[int]):
    # Validar que el paciente exista
    patient = db.session.execute(
        select(Patient).where(Patient.id == patient_id)
    ).scalar_one_or_none()

    if patient is None:
        raise ValueError("Patient not found")

    # Validar que todos los antecedente_ids enviados existan realmente
    if antecedente_ids:
        found = db.session.execute(
            select(Antecedente.id).where(Antecedente.id.in_(antecedente_ids))
        ).scalars().all()

        invalid_ids = set(antecedente_ids) - set(found)
        if invalid_ids:
            raise ValueError(f"Invalid antecedente_ids: {sorted(invalid_ids)}")

    # Borra todo lo que este paciente tenía marcado
    db.session.execute(
        delete(PatientAntecedente).where(
            PatientAntecedente.id_paciente == patient_id
        )
    )

    # Reinserta solo los que llegaron marcados
    # (si la lista viene vacía, no inserta nada -> "ninguno" marcado)
    for antecedente_id in antecedente_ids:
        db.session.add(
            PatientAntecedente(
                id_paciente=patient_id,
                id_antecedente=antecedente_id
            )
        )

    db.session.commit()

    return get_antecedentes_by_patient(patient_id)