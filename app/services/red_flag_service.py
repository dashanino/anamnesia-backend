from app.extensions import db
from app.models.pretriage import Pretriage
from app.models.red_flag import RedFlag
from app.models.poblacion_red_flag import PoblacionRedFlag


def obtener_banderas_rojas(id_pretriage, id_user):

    # 1. Buscar el pretriage
    pretriage = db.session.get(Pretriage, id_pretriage)

    if pretriage is None:
        raise ValueError("El pretriage no existe")

    # 2. Verificar que pertenece al usuario
    if pretriage.id_user != id_user:
        raise PermissionError(
            "No tienes permiso para consultar este pretriage"
        )

    # 3. Verificar que ya seleccionó una población
    if pretriage.id_poblacion is None:
        raise ValueError(
            "Primero debes seleccionar una población"
        )

    # 4. Consultar las banderas asociadas a la población
    banderas = (
        db.session.query(RedFlag)
        .join(
            PoblacionRedFlag,
            PoblacionRedFlag.id_bandera == RedFlag.id
        )
        .filter(
            PoblacionRedFlag.id_poblacion == pretriage.id_poblacion,
            RedFlag.is_active.is_(True)
        )
        .order_by(PoblacionRedFlag.id)
        .all()
    )

    # 5. Preparar la respuesta
    return {
        "id_pretriage": pretriage.id,
        "id_poblacion": pretriage.id_poblacion,
        "banderas_rojas": [
            {
                "id_bandera": bandera.id,
                "name": bandera.name,
                "description": bandera.description
            }
            for bandera in banderas
        ]
    }