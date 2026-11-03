from flask import current_app, jsonify
from app.services.tavus_service import TavusService
from app.models.simulacion import Simulacion
from app.extensions import db
import requests
from openai import OpenAIError
from app.services.evaluacion_service import EvaluacionService
from app.services.tts_service import TTSService


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

    def obtener_transcripcion(self, conversation_id):
        try:
            simulacion = Simulacion.query.filter_by(
                conversation_id=conversation_id
            ).first()

            if simulacion is None:
                return jsonify({
                    "error": "Simulación no encontrada"
                }), 404

            resultado = self.service.obtener_transcripcion(
                conversation_id
            )

            if not resultado["disponible"]:
                return jsonify({
                    "message": "La transcripción todavía no está disponible",
                    "conversation_id": conversation_id,
                    "disponible": False
                }), 202

            return jsonify(resultado), 200

        except requests.exceptions.HTTPError as error:
            return self._error_http_tavus(
                error,
                "Tavus rechazó la consulta de la transcripción"
            )

        except requests.exceptions.RequestException:
            return jsonify({
                "error": "No se pudo consultar la transcripción en Tavus"
            }), 502

        except Exception:
            current_app.logger.exception(
                "Error al obtener la transcripción"
            )

            return jsonify({
                "error": "Error interno al obtener la transcripción"
            }), 500

    def evaluar_conversacion(self, conversation_id):
        try:
            simulacion = Simulacion.query.filter_by(
                conversation_id=conversation_id
            ).first()

            if simulacion is None:
                return jsonify({
                    "error": "Simulación no encontrada"
                }), 404

            if simulacion.estado != "finalizada":
                return jsonify({
                    "error": "Debes finalizar la simulación antes de evaluarla",
                    "estado": simulacion.estado
                }), 409

            if simulacion.evaluacion is not None:
                return jsonify({
                    "message": "Evaluación recuperada correctamente",
                    "conversation_id": conversation_id,
                    "caso_id": simulacion.caso_id,
                    "escenario": simulacion.escenario,
                    "evaluacion": simulacion.evaluacion
                }), 200

            resultado = self.service.obtener_transcripcion(
                conversation_id
            )

            if not resultado["disponible"]:
                return jsonify({
                    "message": "La transcripción todavía no está disponible",
                    "conversation_id": conversation_id,
                    "disponible": False
                }), 202

            dialogo = self.service.limpiar_transcripcion(
                resultado["transcript"]
            )

            if not dialogo:
                return jsonify({
                    "error": "La transcripción no contiene intervenciones válidas"
                }), 422

            evaluacion_service = EvaluacionService()

            evaluacion = evaluacion_service.evaluar_anamnesis(
                caso=simulacion.caso_clinico,
                dialogo=dialogo
            )

            simulacion.evaluacion = evaluacion
            db.session.commit()

            # Generar el feedback hablado únicamente al completar una evaluación nueva.
            # No se ejecuta al recuperar una evaluación ya guardada.
            try:
                tts_service = TTSService()
                feedback_audio = tts_service.generar_audio_feedback(evaluacion)
            except Exception:
                current_app.logger.exception(
                    "La evaluación fue exitosa, pero no se pudo generar el TTS"
                )
                feedback_audio = None

            response = {
                "message": "Evaluación realizada correctamente",
                "conversation_id": conversation_id,
                "caso_id": simulacion.caso_id,
                "escenario": simulacion.escenario,
                "evaluacion": evaluacion
            }

            if feedback_audio:
                response["feedback_tts"] = feedback_audio

            return jsonify(response), 200

        except requests.exceptions.HTTPError as error:
            db.session.rollback()
            return self._error_http_tavus(
                error,
                "Tavus rechazó la consulta de la transcripción"
            )

        except requests.exceptions.RequestException:
            db.session.rollback()
            return jsonify({
                "error": "No se pudo consultar la transcripción en Tavus"
            }), 502

        except OpenAIError:
            db.session.rollback()
            current_app.logger.exception(
                "Error de comunicación con OpenAI durante la evaluación"
            )

            return jsonify({
                "error": "No se pudo realizar la evaluación con OpenAI"
            }), 502

        except ValueError as error:
            db.session.rollback()
            current_app.logger.warning(
                "No se pudo evaluar la conversación: %s",
                str(error)
            )

            return jsonify({
                "error": str(error)
            }), 422

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Error interno al evaluar la conversación"
            )

            return jsonify({
                "error": "Error interno al realizar la evaluación"
            }), 500

    def obtener_evaluacion(self, conversation_id):
        try:
            simulacion = Simulacion.query.filter_by(
                conversation_id=conversation_id
            ).first()

            if simulacion is None:
                return jsonify({
                    "error": "Simulación no encontrada"
                }), 404

            if simulacion.evaluacion is None:
                return jsonify({
                    "message": "Esta simulación todavía no tiene una evaluación"
                }), 404

            return jsonify({
                "message": "Evaluación recuperada correctamente",
                "conversation_id": conversation_id,
                "caso_id": simulacion.caso_id,
                "escenario": simulacion.escenario,
                "evaluacion": simulacion.evaluacion
            }), 200

        except Exception:
            current_app.logger.exception(
                "Error al recuperar la evaluación"
            )

            return jsonify({
                "error": "Error interno al recuperar la evaluación"
            }), 500
