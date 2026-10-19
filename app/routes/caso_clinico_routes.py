from flask import Blueprint
from app.controllers.caso_clinico_controller import CasoClinicoController


caso_clinico_bp = Blueprint(
    "caso_clinico",
    __name__
)

caso_clinico_controller = CasoClinicoController()


@caso_clinico_bp.route("/generar", methods=["POST"])
def generar_caso():
    return caso_clinico_controller.generar_caso()