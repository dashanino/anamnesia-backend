from flask import current_app, jsonify
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
                "message": (
                    "Prueba creada correctamente; el avatar no ingresará"
                    if self.service.test_mode
                    else "Conversación creada correctamente"
                ),
                "conversation_id": tavus.get("conversation_id"),
                "conversation_url": tavus.get("conversation_url"),
                "status": tavus.get("status"),
                "test_mode": self.service.test_mode
            }), 201

        except requests.exceptions.HTTPError as error:
            return self._error_http_tavus(
                error, "Tavus rechazó la creación de la conversación"
            )

        except requests.exceptions.RequestException:
            return jsonify({
                "error": "No se pudo crear la conversación con Tavus"
            }), 502

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Error interno al crear la conversación")

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

        except requests.exceptions.HTTPError as error:
            db.session.rollback()
            return self._error_http_tavus(
                error, "Tavus rechazó el cierre de la conversación"
            )

        except requests.exceptions.RequestException:
            db.session.rollback()
            return jsonify({
                "error": "No se pudo confirmar el cierre en Tavus"
            }), 502

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Error interno al finalizar la conversación")
            return jsonify({
                "error": "Error interno al finalizar la conversación"
            }), 500
    @staticmethod
    def _error_http_tavus(error, message):
        # No devuelve cabeceras, claves, contexto clínico ni el cuerpo completo.
        response = error.response
        status = response.status_code if response is not None else None
        current_app.logger.warning("%s (HTTP %s)", message, status)
        return jsonify({
            "error": message,
            "tavus_status": status
        }), 502

    def diagnosticar_conversacion(self, conversation_id):
        try:
            simulacion = Simulacion.query.filter_by(
                conversation_id=conversation_id
            ).first()
            if simulacion is None:
                return jsonify({"error": "Simulación no encontrada"}), 404

            resultado = self.service.diagnosticar_conversacion(conversation_id)
            return jsonify(resultado), 200
        except requests.exceptions.HTTPError as error:
            return self._error_http_tavus(
                error, "Tavus rechazó la consulta de la conversación"
            )
        except requests.exceptions.RequestException:
            return jsonify({"error": "No se pudo consultar Tavus"}), 502
        except Exception:
            current_app.logger.exception("Error al consultar la conversación")
            return jsonify({"error": "Error interno al consultar la conversación"}), 500
