import copy
import random
from uuid import uuid4


# ==================================================
# CASOS CLÍNICOS BASE
# ==================================================
# Son ejemplos ficticios para desarrollo.
# Deben ser revisados y validados por docentes
# antes de utilizarse en evaluaciones académicas.

CASOS_BASE = {
    "dolor_toracico_isquemico": [
        {
            "motivo_consulta": "Dolor en el pecho",
            "inicio": "Hace 30 minutos",
            "evolucion": "El dolor continúa",
            "intensidad": "8/10",
            "descripcion": (
                "Siento una presión muy fuerte en "
                "el centro del pecho"
            ),
            "sintomas_presentes": [
                "Dolor opresivo en el pecho",
                "Dolor hacia el brazo izquierdo",
                "Sudoración fría",
                "Náuseas",
                "Dificultad para respirar"
            ],
            "sintomas_ausentes": [
                "Fiebre",
                "Tos",
                "Hinchazón de piernas"
            ],
            "factores_agravantes": [
                "Esfuerzo físico"
            ],
            "factores_alivio": [
                "No mejora con el reposo"
            ],
            "signos_alarma": [
                "Dolor torácico persistente",
                "Sudoración fría",
                "Dificultad respiratoria"
            ],
            "antecedentes_personales": [
                "Hipertensión arterial",
                "Diabetes mellitus tipo 2"
            ],
            "antecedentes_familiares": [
                "Padre con antecedente de infarto"
            ],
            "medicamentos": [
                "Losartán",
                "Metformina"
            ],
            "alergias": [
                "Ninguna conocida"
            ]
        },
        {
            "motivo_consulta": "Molestia en el pecho",
            "inicio": "Hace 45 minutos",
            "evolucion": "La molestia no desaparece",
            "intensidad": "7/10",
            "descripcion": (
                "Siento como si tuviera algo "
                "muy pesado encima del pecho"
            ),
            "sintomas_presentes": [
                "Presión en el pecho",
                "Molestia hacia la mandíbula",
                "Náuseas",
                "Cansancio repentino"
            ],
            "sintomas_ausentes": [
                "Fiebre",
                "Tos",
                "Hinchazón de piernas"
            ],
            "factores_agravantes": [
                "Actividad física"
            ],
            "factores_alivio": [
                "No mejora completamente al descansar"
            ],
            "signos_alarma": [
                "Molestia torácica persistente",
                "Náuseas asociadas"
            ],
            "antecedentes_personales": [
                "Hipertensión arterial"
            ],
            "antecedentes_familiares": [
                "Madre con enfermedad coronaria"
            ],
            "medicamentos": [
                "Amlodipino"
            ],
            "alergias": [
                "Ninguna conocida"
            ]
        }
    ],

    "falla_cardiaca": [
        {
            "motivo_consulta": "Dificultad para respirar",
            "inicio": "Hace dos semanas",
            "evolucion": (
                "La dificultad para respirar "
                "ha empeorado progresivamente"
            ),
            "intensidad": "Moderada a intensa",
            "descripcion": (
                "Me canso mucho al caminar "
                "y me cuesta respirar acostada"
            ),
            "sintomas_presentes": [
                "Dificultad respiratoria al caminar",
                "Dificultad para respirar acostada",
                "Necesidad de dormir con tres almohadas",
                "Hinchazón de ambas piernas",
                "Cansancio progresivo"
            ],
            "sintomas_ausentes": [
                "Fiebre",
                "Dolor torácico opresivo",
                "Sudoración fría"
            ],
            "factores_agravantes": [
                "Caminar",
                "Acostarse completamente"
            ],
            "factores_alivio": [
                "Sentarse",
                "Descansar"
            ],
            "signos_alarma": [
                "Dificultad respiratoria progresiva",
                "Dificultad respiratoria al acostarse"
            ],
            "antecedentes_personales": [
                "Hipertensión arterial",
                "Insuficiencia cardíaca conocida"
            ],
            "antecedentes_familiares": [
                "Madre con hipertensión arterial"
            ],
            "medicamentos": [
                "Losartán",
                "Furosemida"
            ],
            "alergias": [
                "Ninguna conocida"
            ]
        },
        {
            "motivo_consulta": "Hinchazón y cansancio",
            "inicio": "Hace diez días",
            "evolucion": (
                "La hinchazón y el cansancio "
                "han aumentado"
            ),
            "intensidad": "Moderada",
            "descripcion": (
                "Tengo los pies muy hinchados "
                "y me agito al subir escaleras"
            ),
            "sintomas_presentes": [
                "Hinchazón de ambos tobillos",
                "Cansancio al caminar",
                "Dificultad para subir escaleras",
                "Despertares nocturnos por falta de aire"
            ],
            "sintomas_ausentes": [
                "Fiebre",
                "Dolor torácico opresivo",
                "Náuseas"
            ],
            "factores_agravantes": [
                "Esfuerzo físico",
                "Permanecer mucho tiempo de pie"
            ],
            "factores_alivio": [
                "Descansar",
                "Elevar las piernas"
            ],
            "signos_alarma": [
                "Despertares nocturnos por falta de aire",
                "Empeoramiento progresivo de síntomas"
            ],
            "antecedentes_personales": [
                "Hipertensión arterial",
                "Insuficiencia cardíaca conocida"
            ],
            "antecedentes_familiares": [
                "Padre con hipertensión arterial"
            ],
            "medicamentos": [
                "Enalapril",
                "Furosemida"
            ],
            "alergias": [
                "Ninguna conocida"
            ]
        }
    ]
}


# ==================================================
# SERVICIO GENERADOR DE CASOS
# ==================================================

class CasoClinicoService:

    def __init__(self):
        self.escenarios = list(CASOS_BASE.keys())

        self.ocupaciones = [
            "Comerciante",
            "Docente",
            "Ama de casa",
            "Contadora",
            "Costurera",
            "Vendedora",
            "Pensionada"
        ]

        self.edades = {
            "dolor_toracico_isquemico": (40, 80),
            "falla_cardiaca": (45, 85)
        }

        self.emociones = [
            "Preocupada",
            "Nerviosa",
            "Cansada",
            "Asustada"
        ]

    def generar_caso(self):
        """
        Genera una ficha clínica nueva.
        Selecciona aleatoriamente uno de los dos
        escenarios y una variante clínica.
        """

        escenario = random.choice(self.escenarios)

        variante = copy.deepcopy(
            random.choice(CASOS_BASE[escenario])
        )

        edad_min, edad_max = self.edades[escenario]

        paciente = {
            "nombre": "Lucy",
            "sexo": "femenino",
            "edad": random.randint(
                edad_min,
                edad_max
            ),
            "ocupacion": random.choice(
                self.ocupaciones
            )
        }

        caso = {
            "caso_id": str(uuid4()),
            "escenario": escenario,
            "paciente": paciente,
            "motivo_consulta": variante[
                "motivo_consulta"
            ],
            "sintomas": {
                "inicio": variante["inicio"],
                "evolucion": variante["evolucion"],
                "intensidad": variante["intensidad"],
                "descripcion": variante["descripcion"],
                "presentes": variante[
                    "sintomas_presentes"
                ],
                "ausentes": variante[
                    "sintomas_ausentes"
                ],
                "factores_agravantes": variante[
                    "factores_agravantes"
                ],
                "factores_alivio": variante[
                    "factores_alivio"
                ]
            },
            "antecedentes": {
                "personales": variante[
                    "antecedentes_personales"
                ],
                "familiares": variante[
                    "antecedentes_familiares"
                ],
                "medicamentos": variante[
                    "medicamentos"
                ],
                "alergias": variante[
                    "alergias"
                ]
            },
            "signos_alarma": variante[
                "signos_alarma"
            ],
            "comportamiento": {
                "emocion": random.choice(
                    self.emociones
                ),
                "lenguaje": "Cotidiano",
                "revelar_diagnostico": False,
                "evaluar_estudiante": False
            }
        }

        return caso


# ==================================================
# PRUEBA LOCAL
# ==================================================

if __name__ == "__main__":
    import json

    servicio = CasoClinicoService()

    caso = servicio.generar_caso()

    print(
        json.dumps(
            caso,
            indent=4,
            ensure_ascii=False
        )
    )