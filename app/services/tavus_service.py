import os
import requests
from dotenv import load_dotenv

load_dotenv()

class TavusService:
    def __init__(self):
        self.api_key = os.getenv("TAVUS_API_KEY")
        self.replica_id = os.getenv("TAVUS_REPLICA_ID")
        self.persona_id = os.getenv("TAVUS_PERSONA_ID")

        if not self.api_key:
            raise ValueError("Falta TAVUS_API_KEY")

        self.url = "https://tavusapi.com/v2/conversations"

    def crear_conversacion(self):
        caso_clinico = """
        Eres Carlos, un paciente ficticio de 58 años.

        MOTIVO DE CONSULTA:
        Dolor opresivo en el pecho desde hace 30 minutos.

        ANTECEDENTES:
        Hipertensión arterial y tabaquismo.

        SÍNTOMAS:
        - Dolor torácico de intensidad 8/10.
        - Dolor irradiado al brazo izquierdo.
        - Sudoración fría.
        - Náuseas.

        INSTRUCCIONES:
        - Actúa como paciente, no como médico.
        - Responde en español.
        - No reveles el diagnóstico.
        - Responde únicamente según el caso clínico.
        - Si preguntan por datos no definidos, indica
          que no los recuerdas o no los sabes.
        - No inventes antecedentes médicos.
        - Guarda una evaluación del estudiante para dar una retroalimentación al final
        """

        payload = {
            "replica_id": self.replica_id,
            "persona_id": self.persona_id,
            "conversation_name": "Simulación cardíaca",
            "conversational_context": caso_clinico
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
        return response.json()