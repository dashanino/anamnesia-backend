import base64
import os

from openai import OpenAI


class TTSService:
    """Genera una retroalimentación breve en audio para el cierre."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        self.voice = os.getenv("OPENAI_TTS_VOICE", "coral")

        if not api_key:
            raise ValueError("Falta configurar OPENAI_API_KEY")

        self.client = OpenAI(api_key=api_key)

    @staticmethod
    def construir_feedback(evaluacion):
        porcentaje = float(evaluacion.get("porcentaje", 0))
        fortalezas = evaluacion.get("fortalezas") or []
        mejoras = evaluacion.get("aspectos_por_mejorar") or []

        if porcentaje >= 90:
            inicio = "¡Excelente!"
        elif porcentaje >= 80:
            inicio = "¡Muy bien!"
        elif porcentaje >= 70:
            inicio = "Buen trabajo."
        elif porcentaje >= 60:
            inicio = "Bien, aunque hay algunos aspectos por mejorar."
        else:
            inicio = "Tienes varios aspectos importantes por reforzar."

        partes = [
            f"{inicio} Obtuviste un {porcentaje:.0f} por ciento."
        ]

        if fortalezas:
            partes.append(
                f"Lo hiciste bien en {str(fortalezas[0]).rstrip('.')} ."
            )

        if mejoras:
            partes.append(
                f"Para mejorar, {str(mejoras[0]).rstrip('.').lower()}."
            )

        if porcentaje >= 90:
            cierre = "En general, tu desempeño fue excelente."
        elif porcentaje >= 80:
            cierre = "En general, tu desempeño fue muy bueno."
        elif porcentaje >= 70:
            cierre = "Sigue practicando para ganar mayor profundidad y organización."
        else:
            cierre = "Te recomiendo practicar una estructura más sistemática para la anamnesis."

        partes.append(cierre)
        return " ".join(partes)

    def generar_audio_feedback(self, evaluacion):
        texto = self.construir_feedback(evaluacion)

        respuesta = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=texto,
            response_format="mp3",
        )

        audio_bytes = respuesta.read()

        return {
            "texto": texto,
            "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
            "mime_type": "audio/mpeg",
        }
