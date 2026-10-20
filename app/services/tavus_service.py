import os
import json
import requests
from dotenv import load_dotenv
from app.extensions import db
from app.models.simulacion import Simulacion

from app.services.caso_clinico_service import CasoClinicoService

load_dotenv()


class TavusService:

    def __init__(self):
        self.api_key = os.getenv("TAVUS_API_KEY")
        self.pal_id = os.getenv("TAVUS_PAL_ID")

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
            "test_mode": True
        }

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
            estado="creada"
        )

        # Guardar en PostgreSQL
        try:
            db.session.add(simulacion)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # Devolver el resultado al controlador
        return {
            "tavus": resultado,
            "caso": caso
        }

    
    def finalizar_conversacion(self, conversation_id):
        if not conversation_id:
            raise ValueError("El conversation_id es obligatorio")

        url = f"https://tavusapi.com/v2/conversations/{conversation_id}"

        headers = {
            "x-api-key": self.api_key
        }

        response = requests.delete(
            url,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        return {
            "conversation_id": conversation_id,
            "finalizada": True
        }
   
                