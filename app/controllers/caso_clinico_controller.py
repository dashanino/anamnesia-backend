from flask import jsonify
from app.services.caso_clinico_service import CasoClinicoService


class CasoClinicoController:

    def __init__(self):
        self.service = CasoClinicoService()

    def generar_caso(self):
        try:
            caso = self.service.generar_caso()

            return jsonify({
                "message": "Caso clínico generado correctamente",
                "caso": caso
            }), 201

        except Exception:
            return jsonify({
                "error": "No se pudo generar el caso clínico"
            }), 500