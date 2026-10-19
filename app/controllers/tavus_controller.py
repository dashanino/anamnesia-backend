from flask import jsonify
from app.services.tavus_service import TavusService
import requests


class TavusController:

    def __init__(self):
        self.service = TavusService()

    def crear_conversacion(self):
        try:
            resultado = self.service.crear_conversacion()

            tavus = resultado["tavus"]

            return jsonify({
                "message": "Conversación creada correctamente",
                "conversation_id": tavus.get("conversation_id"),
                "conversation_url": tavus.get("conversation_url")
            }), 201

        except requests.exceptions.RequestException:
            return jsonify({
                "error": "No se pudo crear la conversación con Tavus"
            }), 502

        except Exception:
            return jsonify({
                "error": "Error interno al crear la conversación"
            }), 500