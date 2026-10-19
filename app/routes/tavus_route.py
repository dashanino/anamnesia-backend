from flask import Blueprint
from app.controllers.tavus_controller import TavusController

tavus_bp = Blueprint("tavus", __name__)

controller = TavusController()


@tavus_bp.route("/tavus/conversation", methods=["POST"])
def crear_conversacion():
    return controller.crear_conversacion()