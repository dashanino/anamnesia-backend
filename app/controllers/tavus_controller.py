from flask import jsonify
from app.services.tavus_service import TavusService
from app.models.simulacion import Simulacion
from app.extensions import db
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
    def finalizar_conversacion(self, conversation_id):
        try:
            simulacion = Simulacion.query.filter_by(
                conversation_id=conversation_id
            ).first()

            if not simulacion:
                return jsonify({
                    "error": "Simulación no encontrada"
                }), 404

            if simulacion.estado == "finalizada":
                return jsonify({
                    "message": "La simulación ya está finalizada"
                }), 200

            self.service.finalizar_conversacion(conversation_id)

            simulacion.estado = "finalizada"
            db.session.commit()

            return jsonify({
                "message": "Conversación finalizada correctamente",
                "conversation_id": conversation_id,
                "estado": simulacion.estado
            }), 200

        except requests.exceptions.RequestException:
            db.session.rollback()
            return jsonify({
                "error": "No se pudo confirmar el cierre en Tavus"
            }), 502

        except Exception:
            db.session.rollback()
            return jsonify({
                "error": "Error interno al finalizar la conversación"
            }), 500