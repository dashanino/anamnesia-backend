from sqlalchemy import select
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.models.pretriage import Pretriage
from app.models.poblacion import Poblacion



def iniciar_pretriage_nn():

    try:
        # 1. Buscar el rol usernn
        rol_usernn = db.session.execute(
            select(Role).where(Role.name == "usernn")
        ).scalar_one_or_none()

        if rol_usernn is None:
            raise ValueError("El rol usernn no existe")

        # 2. Crear el usuario NN
        user_nn = User(
            id_role=rol_usernn.id
        )

        db.session.add(user_nn)
        db.session.flush()

        # 3. Crear el pretriage asociado
        pretriage = Pretriage(
            id_user=user_nn.id,
            estado="iniciado"
        )

        db.session.add(pretriage)
        db.session.flush()

        # 4. Obtener los identificadores
        id_user = user_nn.id
        id_pretriage = pretriage.id

        # 5. Confirmar los registros
        db.session.commit()

        # 6. Generar el token JWT
        access_token = create_access_token(
            identity=str(id_user),
            additional_claims={
                "id_pretriage": id_pretriage,
                "tipo_acceso": "emergencia"
            }
        )

        return {
            "id_user": id_user,
            "id_pretriage": id_pretriage,
            "access_token": access_token
        }

    except Exception:
        db.session.rollback()
        raise
def guardar_poblacion_nn(id_pretriage, id_user, id_poblacion):

    # 1. Buscar el pretriage existente
    pretriage = db.session.get(Pretriage, id_pretriage)

    if pretriage is None:
        raise ValueError("El pretriage no existe")

    # 2. Comprobar que pertenece al usuario del token
    if pretriage.id_user != id_user:
        raise PermissionError(
            "No tienes permiso para modificar este pretriage"
        )

    # 3. Comprobar que sigue en curso
    if pretriage.estado != "iniciado":
        raise ValueError(
            "El pretriage no está en estado iniciado"
        )

    # 4. Buscar la población seleccionada
    poblacion = db.session.get(Poblacion, id_poblacion)

    if poblacion is None:
        raise ValueError("La población no existe")

    if not poblacion.is_active:
        raise ValueError("La población no está activa")

    try:
        # 5. Actualizar el pretriage existente
        pretriage.id_poblacion = poblacion.id

        db.session.commit()

        return {
            "id_pretriage": pretriage.id,
            "id_poblacion": poblacion.id,
            "poblacion": poblacion.name
        }

    except Exception:
        db.session.rollback()
        raise