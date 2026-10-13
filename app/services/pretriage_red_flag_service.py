from app.extensions import db
from app.models.pretriage import Pretriage
from app.models.red_flag import RedFlag
from app.models.poblacion_red_flag import PoblacionRedFlag
from app.models.pretriage_red_flag import PretriageRedFlag


def guardar_banderas_rojas_nn(
    id_pretriage,
    id_user,
    ids_banderas
):
    # 1. Buscar el pretriage
    pretriage = db.session.get(Pretriage, id_pretriage)

    if pretriage is None:
        raise ValueError("El pretriage no existe")

    # 2. Verificar que pertenezca al usuario
    if pretriage.id_user != id_user:
        raise PermissionError(
            "No tienes permiso para modificar este pretriage"
        )

    # 3. Verificar que el pretriage siga activo
    if pretriage.estado != "iniciado":
        raise ValueError(
            "El pretriage ya no se encuentra iniciado"
        )

    # 4. Verificar que tenga población
    if pretriage.id_poblacion is None:
        raise ValueError(
            "Primero debes seleccionar una población"
        )

    # 5. Validar que se reciba una lista
    if not isinstance(ids_banderas, list):
        raise ValueError(
            "id_banderas debe ser una lista"
        )

    # Evitar IDs repetidos
    ids_banderas = list(set(ids_banderas))

    # Validar que todos sean enteros
    if any(type(id_bandera) is not int for id_bandera in ids_banderas):
        raise ValueError(
            "Todos los IDs de las banderas deben ser números enteros"
        )

    # 6. Buscar las banderas permitidas para esa población
    asociaciones = (
        db.session.query(PoblacionRedFlag)
        .join(
            RedFlag,
            RedFlag.id == PoblacionRedFlag.id_bandera
        )
        .filter(
            PoblacionRedFlag.id_poblacion == pretriage.id_poblacion,
            RedFlag.is_active.is_(True)
        )
        .all()
    )

    ids_permitidos = {
        asociacion.id_bandera
        for asociacion in asociaciones
    }

    # 7. Verificar que todas las seleccionadas
    # pertenezcan a esa población
    ids_invalidos = [
        id_bandera
        for id_bandera in ids_banderas
        if id_bandera not in ids_permitidos
    ]

    if ids_invalidos:
        raise ValueError(
            f"Las banderas {ids_invalidos} no pertenecen "
            "a la población seleccionada"
        )

    try:
        # 8. Eliminar selecciones anteriores
        db.session.query(PretriageRedFlag).filter(
            PretriageRedFlag.id_pretriage == id_pretriage
        ).delete()

        # 9. Guardar las nuevas selecciones
        for id_bandera in ids_banderas:
            seleccion = PretriageRedFlag(
                id_pretriage=id_pretriage,
                id_bandera=id_bandera
            )

            db.session.add(seleccion)

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    # 10. Consultar los nombres para devolverlos
    banderas = (
        db.session.query(RedFlag)
        .filter(RedFlag.id.in_(ids_banderas))
        .all()
        if ids_banderas
        else []
    )

    return {
        "id_pretriage": id_pretriage,
        "id_poblacion": pretriage.id_poblacion,
        "banderas_seleccionadas": [
            {
                "id_bandera": bandera.id,
                "name": bandera.name
            }
            for bandera in banderas
        ]
    }