import os
import logging
import json
import requests
from dotenv import load_dotenv
from app.extensions import db
from app.models.simulacion import Simulacion

from app.services.caso_clinico_service import CasoClinicoService

load_dotenv()

logger = logging.getLogger(__name__)


class TavusService:

    def __init__(self):
        self.api_key = os.getenv("TAVUS_API_KEY")
        self.pal_id = os.getenv("TAVUS_PAL_ID")
        self.face_id = os.getenv("TAVUS_FACE_ID", "").strip()

        # Conserva el modo de prueba hasta activarlo explícitamente en .env.
        test_mode = os.getenv("TAVUS_TEST_MODE", "true").strip().lower()
        if test_mode not in {"true", "false"}:
            raise ValueError("TAVUS_TEST_MODE debe ser true o false")
        self.test_mode = test_mode == "true"

        if not self.api_key or not self.pal_id:
            raise ValueError("Falta TAVUS_API_KEY o TAVUS_PAL_ID")

        self.url = "https://tavusapi.com/v2/conversations"
        self.caso_service = CasoClinicoService()

    def crear_conversacion(self):

        # 1. Generar un caso aleatorio
        caso = self.caso_service.generar_caso()

        # 2. Preparar instrucciones para Lucy
        instrucciones = """
        Eres Lucy, una paciente ficticia de sexo femenino.

        Estás participando en una simulación académica
        de anamnesis cardiovascular.

        REGLAS:
        - Habla exclusivamente en español cotidiano.
        - Actúa como paciente, nunca como médica.
        - Usa la edad y ocupación indicadas en la ficha.
        - No reveles el diagnóstico ni el escenario.
        - No menciones el nombre técnico de tu enfermedad.
        - Responde según los datos de la ficha clínica.
        - No inventes síntomas, antecedentes o medicamentos.
        - Si desconoces un dato, dilo naturalmente.
        - No reveles toda la historia espontáneamente.
        - Deja que el estudiante dirija la entrevista.
        - Varía tu manera de saludar y expresarte.
        - Mantén los datos consistentes durante la sesión.
        - No evalúes ni califiques al estudiante.
        - No ofrezcas retroalimentación académica.

        Cuando el estudiante diga "hemos terminado",
        responde: "Muchas gracias, doctor".
        La aplicación se encargará de cerrar la sesión.

        FICHA CLÍNICA CONFIDENCIAL:
        """

        contexto = (
            instrucciones
            + "\n"
            + json.dumps(
                caso,
                ensure_ascii=False,
                indent=2
            )
        )

        # 3. Crear conversación con Tavus
        payload = {
            "pal_id": self.pal_id,
            "conversation_name": (
                f"Anamnesis cardiovascular - {caso['caso_id']}"
            ),
            "conversational_context": contexto,
            "dynamic_greeting": True,
            "test_mode": self.test_mode
        }

        # Omite este campo si el PAL ya tiene un default_face_id válido.
        if self.face_id:
            payload["face_id"] = self.face_id

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(
            self.url,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        resultado = response.json()
        # Obtener el identificador de la conversación
        conversation_id = resultado.get("conversation_id")

        if not conversation_id:
            raise ValueError(
                "Tavus no devolvió un conversation_id"
            )

        # Crear el registro de la simulación
        simulacion = Simulacion(
            caso_id=caso["caso_id"],
            conversation_id=conversation_id,
            escenario=caso["escenario"],
            caso_clinico=caso,
            estado=(
                "finalizada" if resultado.get("status") == "ended"
                else "creada"
            )
        )

        # Guardar en PostgreSQL
        try:
            db.session.add(simulacion)
            db.session.commit()
        except Exception:
            db.session.rollback()
            # Si falló PostgreSQL tras crear la sala, intenta cerrarla.
            # El error de persistencia original sigue siendo el principal.
            if resultado.get("status") != "ended":
                try:
                    self.finalizar_conversacion(conversation_id)
                except Exception:
                    logger.exception(
                        "No se pudo cerrar en Tavus la conversación %s "
                        "tras un fallo de persistencia; requiere revisión",
                        conversation_id
                    )
            raise

        # Devolver el resultado al controlador
        return {
            "tavus": resultado,
            "caso": caso
        }

    
    def finalizar_conversacion(self, conversation_id):
        if not conversation_id:
            raise ValueError("El conversation_id es obligatorio")

        url = f"{self.url}/{conversation_id}/end"

        headers = {
            "x-api-key": self.api_key
        }

        response = requests.post(
            url,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        return {
            "conversation_id": conversation_id,
            "finalizada": True
        }

    def diagnosticar_conversacion(self, conversation_id):
        """Consulta Tavus sin crear ni finalizar conversaciones."""
        response = requests.get(
            f"{self.url}/{conversation_id}",
            params={"verbose": "true"},
            headers={"x-api-key": self.api_key},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Respuesta de diagnóstico Tavus no válida")

        # Lista permitida: no expone transcripciones, percepción ni tokens.
        campos = (
            "conversation_id", "status", "pal_id", "face_id",
            "created_at", "updated_at", "shutdown_reason"
        )
        diagnostico = {
            campo: data.get(campo)
            if isinstance(data.get(campo), str) else None
            for campo in campos
        }
        eventos = data.get("events") or []
        if not isinstance(eventos, list):
            eventos = []
        diagnostico["eventos_sistema"] = []
        for evento in eventos:
            if not isinstance(evento, dict):
                continue
            tipo = evento.get("event_type")
            if tipo not in {
                "system.pal_joined", "system.replica_joined", "system.shutdown"
            }:
                continue
            properties = evento.get("properties")
            if not isinstance(properties, dict):
                properties = {}
            motivo = properties.get("shutdown_reason")
            motivo = motivo if isinstance(motivo, str) else None
            timestamp = evento.get("timestamp")
            diagnostico["eventos_sistema"].append({
                "event_type": tipo,
                "timestamp": timestamp
                if isinstance(timestamp, (str, int, float)) else None,
                "shutdown_reason": motivo
            })
            if tipo == "system.shutdown" and motivo:
                diagnostico["shutdown_reason"] = motivo
        return diagnostico
