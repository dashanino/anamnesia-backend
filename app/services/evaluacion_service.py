import os
import json
import logging

from openai import OpenAI


logger = logging.getLogger(__name__)


CRITERIOS = [
    {
        "id": "motivo_consulta",
        "nombre": "Motivo de consulta",
        "descripcion": (
            "Explora el motivo principal por el que la paciente "
            "consulta y permite identificar su preocupación principal."
        )
    },
    {
        "id": "caracterizacion_sintoma",
        "nombre": "Caracterización del síntoma principal",
        "descripcion": (
            "Pregunta por inicio, evolución, duración cuando corresponda, "
            "intensidad y descripción del síntoma principal."
        )
    },
    {
        "id": "sintomas_asociados",
        "nombre": "Síntomas asociados",
        "descripcion": (
            "Investiga los síntomas acompañantes pertinentes al escenario "
            "clínico y presentes en la ficha."
        )
    },
    {
        "id": "antecedentes_personales",
        "nombre": "Antecedentes personales",
        "descripcion": (
            "Pregunta por antecedentes personales relevantes que aparecen "
            "en la ficha clínica."
        )
    },
    {
        "id": "antecedentes_familiares",
        "nombre": "Antecedentes familiares",
        "descripcion": (
            "Explora antecedentes familiares relevantes incluidos "
            "en la ficha clínica."
        )
    },
    {
        "id": "medicamentos_alergias",
        "nombre": "Medicamentos y alergias",
        "descripcion": (
            "Pregunta por los medicamentos que utiliza la paciente "
            "y por sus alergias."
        )
    },
    {
        "id": "factores_riesgo",
        "nombre": "Factores de riesgo cardiovascular",
        "descripcion": (
            "Explora los factores de riesgo que puedan identificarse "
            "en los antecedentes personales y familiares de esta ficha. "
            "No inventes factores que no estén registrados."
        )
    },
    {
        "id": "sintomas_negativos",
        "nombre": "Síntomas negativos relevantes",
        "descripcion": (
            "Investiga síntomas ausentes que sean pertinentes para "
            "el escenario y estén registrados en la ficha."
        )
    },
    {
        "id": "comunicacion",
        "nombre": "Comunicación durante la entrevista",
        "descripcion": (
            "Evalúa claridad, respeto, preguntas comprensibles, escucha "
            "y organización de las preguntas del estudiante."
        )
    }
]


class EvaluacionService:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_TEXT_MODEL")

        if not api_key:
            raise ValueError("Falta configurar OPENAI_API_KEY")

        if not self.model:
            raise ValueError("Falta configurar OPENAI_TEXT_MODEL")

        self.client = OpenAI(api_key=api_key)

    def evaluar_anamnesis(self, caso, dialogo):

        if not isinstance(caso, dict):
            raise ValueError("El caso clínico no tiene un formato válido")

        if not isinstance(dialogo, list) or not dialogo:
            raise ValueError("La transcripción no contiene intervenciones válidas")

        # La conversación completa sirve como contexto,
        # pero solo se califican las preguntas del estudiante.
        intervenciones_estudiante = [
            item for item in dialogo
            if isinstance(item, dict)
            and item.get("role") == "user"
            and isinstance(item.get("content"), str)
            and item["content"].strip()
        ]

        if not intervenciones_estudiante:
            raise ValueError(
                "No se encontraron intervenciones del estudiante"
            )

        sistema = """
Eres un evaluador académico especializado en anamnesis cardiovascular.

Tu tarea es evaluar EXCLUSIVAMENTE la entrevista realizada por el estudiante.

REGLAS OBLIGATORIAS:

1. Evalúa únicamente las intervenciones con role="user".
2. Las intervenciones con role="assistant" pertenecen a Lucy.
   Sus respuestas sirven como contexto, pero nunca se califican como
   preguntas realizadas por el estudiante.
3. Compara la entrevista con la ficha clínica proporcionada.
4. No inventes preguntas, respuestas, síntomas ni antecedentes.
5. No penalices al estudiante por no preguntar información que no
   corresponde al escenario o que no está disponible en la ficha.
6. Considera la pertinencia clínica según el escenario.
7. No evalúes diagnóstico, tratamiento ni decisiones terapéuticas.
8. No afirmes que el estudiante exploró un dato si no existe una
   pregunta explícita o suficientemente clara en sus intervenciones.
9. Una pregunta puede explorar más de un dato si su contenido lo permite.
10. Evalúa la comunicación a partir de las intervenciones del estudiante,
    no de las respuestas de Lucy.

ESCALA PARA CADA CRITERIO:
- 0: No explorado o exploración inadecuada.
- 1: Exploración parcial o poco precisa.
- 2: Exploración adecuada y suficientemente clara.

Debes devolver los nueve criterios solicitados, sin agregar ni eliminar
criterios.

En "fortalezas" incluye aspectos positivos observables.
En "aspectos_por_mejorar" incluye recomendaciones concretas.
En "preguntas_omitidas" incluye únicamente preguntas pertinentes que
habrían permitido completar información de la ficha y que el estudiante
no realizó.

No calcules el puntaje total ni el porcentaje. El backend lo calculará.

Devuelve exclusivamente un objeto JSON válido con esta estructura:

{
  "criterios": [
    {
      "id": "identificador_del_criterio",
      "puntaje": 0,
      "justificacion": "Explicación breve basada en la entrevista"
    }
  ],
  "fortalezas": ["fortaleza"],
  "aspectos_por_mejorar": ["recomendación"],
  "preguntas_omitidas": ["pregunta que habría sido pertinente"],
  "retroalimentacion_general": "Comentario académico breve"
}
"""

        datos = {
            "ficha_clinica": caso,
            "escenario": caso.get("escenario"),
            "criterios_a_evaluar": CRITERIOS,
            "conversacion": dialogo,
            "intervenciones_del_estudiante": intervenciones_estudiante
        }

        try:
            respuesta = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": sistema
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            datos,
                            ensure_ascii=False
                        )
                    }
                ],
                response_format={"type": "json_object"}
            )

            contenido = respuesta.choices[0].message.content

            if not contenido:
                raise ValueError("OpenAI devolvió una respuesta vacía")

            evaluacion = json.loads(contenido)

            return self._validar_y_calcular(evaluacion)

        except Exception:
            logger.exception("Error al evaluar la anamnesis con OpenAI")
            raise

    @staticmethod
    def _validar_y_calcular(evaluacion):

        if not isinstance(evaluacion, dict):
            raise ValueError("La evaluación recibida no es válida")

        criterios_recibidos = evaluacion.get("criterios")

        if not isinstance(criterios_recibidos, list):
            raise ValueError("La evaluación no contiene criterios válidos")

        esperados = {criterio["id"]: criterio for criterio in CRITERIOS}
        recibidos = {}

        for criterio in criterios_recibidos:
            if not isinstance(criterio, dict):
                continue

            criterio_id = criterio.get("id")

            if criterio_id not in esperados:
                continue

            if criterio_id in recibidos:
                raise ValueError("OpenAI devolvió criterios duplicados")

            puntaje = criterio.get("puntaje")

            if isinstance(puntaje, bool) or puntaje not in (0, 1, 2):
                raise ValueError(
                    f"Puntaje inválido para el criterio {criterio_id}"
                )

            recibidos[criterio_id] = {
                "id": criterio_id,
                "nombre": esperados[criterio_id]["nombre"],
                "puntaje": puntaje,
                "puntaje_maximo": 2,
                "justificacion": str(
                    criterio.get("justificacion", "")
                )
            }

        if set(recibidos) != set(esperados):
            raise ValueError(
                "OpenAI no devolvió exactamente los nueve criterios"
            )

        criterios = [
            recibidos[criterio["id"]]
            for criterio in CRITERIOS
        ]

        puntaje_total = sum(
            criterio["puntaje"] for criterio in criterios
        )

        puntaje_maximo = len(CRITERIOS) * 2
        porcentaje = round(
            (puntaje_total / puntaje_maximo) * 100,
            2
        )

        return {
            "criterios": criterios,
            "puntaje_total": puntaje_total,
            "puntaje_maximo": puntaje_maximo,
            "porcentaje": porcentaje,
            "fortalezas": evaluacion.get("fortalezas", []),
            "aspectos_por_mejorar": evaluacion.get(
                "aspectos_por_mejorar", []
            ),
            "preguntas_omitidas": evaluacion.get(
                "preguntas_omitidas", []
            ),
            "retroalimentacion_general": evaluacion.get(
                "retroalimentacion_general", ""
            )
        }