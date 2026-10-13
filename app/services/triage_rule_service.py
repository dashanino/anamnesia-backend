from app.extensions import db

from app.models.pretriage import Pretriage
from app.models.pretriage_antecedente import PretriageAntecedente
from app.models.pretriage_red_flag import PretriageRedFlag

from app.models.triage_rule import TriageRule
from app.models.triage_rule_antecedente import TriageRuleAntecedente

from app.models.red_flag import RedFlag


def evaluar_reglas_triage(id_pretriage, id_user):

    # 1. Buscar el pretriage
    pretriage = db.session.get(Pretriage, id_pretriage)

    if pretriage is None:
        raise ValueError("El pretriage no existe")

    if pretriage.id_user != id_user:
        raise PermissionError(
            "No tienes permiso para consultar este pretriage"
        )

    if pretriage.estado != "iniciado":
        raise ValueError(
            "El pretriage ya no se encuentra iniciado"
        )

    if pretriage.id_poblacion is None:
        raise ValueError(
            "Primero debes seleccionar una población"
        )

    # 2. Obtener antecedentes seleccionados
    antecedentes_pretriage = (
        db.session.query(PretriageAntecedente.id_antecedente)
        .filter(
            PretriageAntecedente.id_pretriage == id_pretriage
        )
        .all()
    )

    ids_antecedentes = {
        fila.id_antecedente
        for fila in antecedentes_pretriage
    }

    # 3. Obtener banderas seleccionadas
    banderas_pretriage = (
        db.session.query(PretriageRedFlag.id_bandera)
        .filter(
            PretriageRedFlag.id_pretriage == id_pretriage
        )
        .all()
    )

    ids_banderas = {
        fila.id_bandera
        for fila in banderas_pretriage
    }

    if not ids_banderas:
        raise ValueError(
            "Debes seleccionar al menos una bandera roja"
        )

        # 4. Evaluar cada bandera roja seleccionada
    for id_bandera in ids_banderas:

        # Buscar las reglas que correspondan a:
        # población del usuario + bandera actual
        reglas = (
            db.session.query(TriageRule)
            .filter(
                TriageRule.id_poblacion == pretriage.id_poblacion,
                TriageRule.id_bandera == id_bandera
            )
            .all()
        )

        # 5. Buscar cuál regla tiene exactamente
        # los mismos antecedentes del usuario
        for regla in reglas:

            antecedentes_regla = (
                db.session.query(
                    TriageRuleAntecedente.id_antecedente
                )
                .filter(
                    TriageRuleAntecedente.id_regla == regla.id
                )
                .all()
            )

            ids_antecedentes_regla = {
                fila.id_antecedente
                for fila in antecedentes_regla
            }

            # Los antecedentes deben coincidir exactamente
            if ids_antecedentes_regla != ids_antecedentes:
                continue

            # Encontramos la regla exacta
            bandera = db.session.get(
                RedFlag,
                regla.id_bandera
            )

            # Si es alta prioridad, detener inmediatamente
            if regla.alta_prioridad:

                return {
                    "id_pretriage": id_pretriage,
                    "alta_prioridad": True,
                    "accion": "alerta",
                    "regla_activadora": regla.id,
                    "bandera_activadora": {
                        "id_bandera": bandera.id,
                        "name": bandera.name
                    }
                }

            # Si es False, esta bandera no activa
            # alta prioridad y continúa con la siguiente.
            break

    # 6. Ninguna de las banderas dio alta prioridad
    return {
        "id_pretriage": id_pretriage,
        "alta_prioridad": False,
        "accion": "continuar_ia"
    }