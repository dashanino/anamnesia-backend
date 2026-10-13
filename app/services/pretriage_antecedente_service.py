from sqlalchemy import select

from app.extensions import db
from app.models.pretriage import Pretriage
from app.models.antecedente import Antecedente
from app.models.pretriage_antecedente import PretriageAntecedente
from app.models.user import User
from app.models.role import Role

ANTECEDENTES_NN = {
    "Anticoagulantes",
    "Inmunocomprometido",
    "Autoinmune",
    "Hemodiálisis",
    "Cáncer activo"
}


def guardar_antecedentes_nn(id_pretriage, ids_antecedentes):

    # 1. Buscar el pretriage existente
    pretriage = db.session.get(Pretriage, id_pretriage)

    if pretriage is None:
        raise ValueError("El pretriage no existe")

    # 2. Buscar el usuario asociado
    usuario = db.session.get(User, pretriage.id_user)

    if usuario is None:
        raise ValueError("El usuario del pretriage no existe")

    # 3. Comprobar que tenga el rol usernn
    rol = db.session.get(Role, usuario.id_role)

    if rol is None or rol.name != "usernn":
        raise ValueError("El pretriage no pertenece a un usuario NN")
    

    if pretriage.estado != "iniciado":
        raise ValueError("El pretriage no está en estado iniciado")

    # 2. Validar la lista recibida
    if not isinstance(ids_antecedentes, list):
        raise ValueError("Los antecedentes deben enviarse en una lista")

    if any(
        type(id_antecedente) is not int
        for id_antecedente in ids_antecedentes
    ):
        raise ValueError("Los identificadores deben ser números enteros")

    if len(ids_antecedentes) != len(set(ids_antecedentes)):
        raise ValueError("No se permiten antecedentes repetidos")

    try:
        # 3. Consultar los antecedentes seleccionados
        antecedentes = db.session.execute(
            select(Antecedente).where(
                Antecedente.id.in_(ids_antecedentes)
            )
        ).scalars().all()

        if len(antecedentes) != len(ids_antecedentes):
            raise ValueError("Uno o más antecedentes no existen")

        # 4. Validar que sean los cinco permitidos
        for antecedente in antecedentes:
            if (
                antecedente.name not in ANTECEDENTES_NN
                or not antecedente.is_active
            ):
                raise ValueError(
                    "Se seleccionó un antecedente no permitido"
                )

        # 5. Consultar las selecciones anteriores
        anteriores = db.session.execute(
            select(PretriageAntecedente).where(
                PretriageAntecedente.id_pretriage == id_pretriage
            )
        ).scalars().all()

        # 6. Reemplazar las selecciones anteriores
        for registro in anteriores:
            db.session.delete(registro)

        db.session.flush()

        # 7. Guardar las nuevas selecciones
        for id_antecedente in ids_antecedentes:
            registro = PretriageAntecedente(
                id_pretriage=id_pretriage,
                id_antecedente=id_antecedente
            )

            db.session.add(registro)

        db.session.commit()

        return {
            "id_pretriage": id_pretriage,
            "id_antecedentes": ids_antecedentes
        }

    except Exception:
        db.session.rollback()
        raise