from flask import jsonify
from app.services.tavus_service import TavusService
import requests

class TavusController:
    def __init__(self):
        self.service = TavusService()

    def crear_conversacion(self):
        try:
            resultado = self.service.crear_conversacion()

            return jsonify({
                "conversation_id": resultado.get("conversation_id"),
                "conversation_url": resultado.get("conversation_url")
            }), 201

        except requests.exceptions.RequestException as error:
            return jsonify({
                "error": "No se pudo crear la conversación con Tavus"
            }), 502