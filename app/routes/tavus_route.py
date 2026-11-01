from flask import Blueprint
from app.controllers.tavus_controller import TavusController

tavus_bp = Blueprint("tavus", __name__)

controller = TavusController()


@tavus_bp.route("/tavus/conversation", methods=["POST"])
def crear_conversacion():
    return controller.crear_conversacion()

@tavus_bp.route(
    "/tavus/conversation/<string:conversation_id>/finalizar",
    methods=["POST"]
)
def finalizar_conversacion(conversation_id):
    return controller.finalizar_conversacion(conversation_id)


@tavus_bp.route(
    "/tavus/conversation/<string:conversation_id>/diagnostico",
    methods=["GET"]
)
def diagnosticar_conversacion(conversation_id):
    return controller.diagnosticar_conversacion(conversation_id)


@tavus_bp.route(
    "/tavus/conversation/<string:conversation_id>/transcripcion",
    methods=["GET"]
)
def obtener_transcripcion(conversation_id):
    return controller.obtener_transcripcion(conversation_id)

@tavus_bp.route(
    "/tavus/conversation/<string:conversation_id>/evaluar",
    methods=["POST"]
)
def evaluar_conversacion(conversation_id):
    return controller.evaluar_conversacion(conversation_id)

@tavus_bp.route(
    "/tavus/conversation/<string:conversation_id>/evaluacion",
    methods=["GET"]
)
def obtener_evaluacion(conversation_id):
    return controller.obtener_evaluacion(conversation_id)

