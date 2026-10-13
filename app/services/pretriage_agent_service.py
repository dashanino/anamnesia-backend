import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from app.extensions import db
from app.models.pretriage import Pretriage


load_dotenv()


class PretriageAgentService:

    def __init__(self):

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY no está configurada"
            )

        self.client = OpenAI(api_key=api_key)

    def evaluate(self, id_pretriage):

        # =========================================================
        # 1. BUSCAR EL PRETRIAGE EN LA BASE DE DATOS
        # =========================================================

        pretriage = db.session.get(
            Pretriage,
            id_pretriage
        )

        if pretriage is None:
            raise ValueError(
                "El pretriage no existe"
            )

        # =========================================================
        # 2. OBTENER LA POBLACIÓN
        # =========================================================

        if pretriage.poblacion is None:
            raise ValueError(
                "El pretriage no tiene una población seleccionada"
            )

        poblacion = pretriage.poblacion.name

        # =========================================================
        # 3. OBTENER LOS ANTECEDENTES
        # =========================================================

        antecedentes = [
            asociacion.antecedente.name
            for asociacion in pretriage.antecedentes_asociados
            if asociacion.antecedente is not None
        ]

        if not antecedentes:
            antecedentes_texto = "No se registraron antecedentes"
        else:
            antecedentes_texto = ", ".join(antecedentes)

        # =========================================================
        # 4. OBTENER LAS BANDERAS ROJAS
        # =========================================================

        banderas = [
            asociacion.red_flag.name
            for asociacion in pretriage.banderas_seleccionadas
            if asociacion.red_flag is not None
        ]

        if not banderas:
            raise ValueError(
                "El pretriage no tiene banderas rojas seleccionadas"
            )

        banderas_texto = ", ".join(banderas)

        # =========================================================
        # 5. INSTRUCCIONES DEL AGENTE
        # =========================================================

        instructions = """
        Eres un asistente de apoyo al pretriage basado en criterios de
        Medicina de Urgencias y Emergencias.

        RESPONDE SIEMPRE EN ESPAÑOL.

        Tu función es analizar exclusivamente la información proporcionada
        del paciente y sugerir una prioridad de atención.

        Las prioridades permitidas de Urgentia son únicamente:

        - alta
        - media_alta
        - media_baja
        - baja

        El sistema utiliza el Emergency Severity Index (ESI)
        únicamente como referencia clínica.

        Estas cuatro categorías son propias de Urgentia y no deben
        presentarse como niveles oficiales del ESI.

        REGLAS:

        - Utiliza únicamente la información proporcionada.

        - No inventes síntomas, antecedentes, signos vitales,
          resultados de exámenes ni información que no haya sido
          proporcionada.

        - No establezcas diagnósticos definitivos.

        - No asumas que la ausencia de un dato significa que el paciente
          no presenta dicho signo o síntoma.

        - Si la información disponible no es suficiente para determinar
          una prioridad con confianza, indícalo explícitamente.

        - Da mayor importancia a las condiciones potencialmente graves
          y a las banderas rojas.

        - Esta evaluación funciona únicamente como apoyo al pretriage
          y no reemplaza la valoración realizada por personal de salud.

        FUENTES DE REFERENCIA:

        Cuando sea necesario fundamentar una decisión clínica, prioriza
        criterios provenientes de fuentes médicas de alta calidad como:

        - Emergency Severity Index (ESI).
        - American College of Emergency Physicians (ACEP).
        - American Heart Association (AHA).
        - European Resuscitation Council (ERC).
        - Sociedad Española de Medicina de Urgencias y Emergencias (SEMES).
        - UpToDate.
        - DynaMed.
        - Tintinalli's Emergency Medicine.
        - Rosen's Emergency Medicine.
        - Reglas de predicción clínica validadas cuando sean aplicables.

        No utilices blogs, foros, contenido de opinión ni sitios
        comerciales dirigidos al público general como fundamento clínico.

        Si existe incertidumbre o evidencia insuficiente, declara la
        limitación en lugar de inventar una conclusión.

        FORMATO DE RESPUESTA:

        Devuelve ÚNICAMENTE un objeto JSON válido.

        No utilices Markdown.
        No utilices bloques de código.
        No agregues texto antes ni después del JSON.

        Debes utilizar exactamente esta estructura:

        {
            "prioridad": "alta | media_alta | media_baja | baja",
            "justificacion": "Explicación breve de la prioridad sugerida",
            "incertidumbre": true,
            "detalle_incertidumbre": "Explicación breve de la incertidumbre"
        }

        El campo "prioridad" solamente puede contener uno de estos
        cuatro valores:

        alta
        media_alta
        media_baja
        baja

        El campo "incertidumbre" debe ser un booleano verdadero o falso.

        Si no existe incertidumbre relevante, utiliza:

        "incertidumbre": false

        y:

        "detalle_incertidumbre": null
        """

        # =========================================================
        # 6. CONSTRUIR EL PROMPT
        # =========================================================

        prompt = f"""
        DATOS DEL PRETRIAGE

        ID del pretriage:
        {id_pretriage}

        Tipo de población:
        {poblacion}

        Antecedentes seleccionados:
        {antecedentes_texto}

        Banderas rojas seleccionadas:
        {banderas_texto}

        Analiza exclusivamente la información anterior y sugiere
        la prioridad correspondiente.

        Devuelve únicamente el objeto JSON solicitado.
        """

        # =========================================================
        # 7. ENVIAR LOS DATOS A LA IA
        # =========================================================

        response = self.client.responses.create(
            model="gpt-5.6-luna",
            instructions=instructions,
            input=prompt
        )

        # =========================================================
        # 8. OBTENER RESPUESTA DE LA IA
        # =========================================================

        response_text = response.output_text.strip()

        # =========================================================
        # 9. CONVERTIR LA RESPUESTA A JSON
        # =========================================================

        try:
            result = json.loads(response_text)

        except json.JSONDecodeError:
            raise ValueError(
                "La IA devolvió una respuesta con formato JSON inválido"
            )

        # =========================================================
        # 10. VALIDAR LA PRIORIDAD
        # =========================================================

        prioridades_validas = {
            "alta",
            "media_alta",
            "media_baja",
            "baja"
        }

        prioridad = result.get("prioridad")

        if prioridad not in prioridades_validas:
            raise ValueError(
                "La IA devolvió una prioridad no válida"
            )

        # =========================================================
        # 11. VALIDAR CAMPOS OBLIGATORIOS
        # =========================================================

        if "justificacion" not in result:
            raise ValueError(
                "La IA no devolvió una justificación"
            )

        if "incertidumbre" not in result:
            raise ValueError(
                "La IA no indicó si existe incertidumbre"
            )

        if not isinstance(result["incertidumbre"], bool):
            raise ValueError(
                "El campo incertidumbre debe ser verdadero o falso"
            )

        if "detalle_incertidumbre" not in result:
            result["detalle_incertidumbre"] = None

        # =========================================================
        # 12. DEVOLVER RESULTADO ESTRUCTURADO
        # =========================================================

        return result
    def generate_additional_questions(self, id_pretriage):
        return id_pretriage
