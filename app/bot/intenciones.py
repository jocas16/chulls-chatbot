"""Clasificador de intenciones por reglas (determinista, rápido y explicable).

El orden importa: la primera regla que coincide gana. Por eso 'emergencia'
va primero: un mensaje con heridos nunca debe tratarse como una cotización.

Es tolerante a errores de tipeo: 'quiero sefuro vehicualr' se corrige a
'quiero seguro vehicular' antes de clasificar.
"""
from __future__ import annotations

import re
from difflib import get_close_matches

from app.bot.textos import normalizar

# (intención, prefijos de palabra). Se compara contra el texto sin tildes.
REGLAS: list[tuple[str, tuple[str, ...]]] = [
    ("emergencia", ("herido", "lesionad", "sangr", "inconscient", "ambulancia", "atropell", "emergencia medica")),
    # Preguntas informativas ("¿qué es el SOAT?") se responden con la base de conocimiento
    ("consulta", ("que es", "que cubre", "que significa", "como funciona", "para que sirve", "explicame")),
    ("asesor", ("asesor", "humano", "persona real", "hablar con alguien", "operador", "agente")),
    ("grua", ("grua", "remolq")),
    ("accidente", ("choque", "choc", "accident", "colision")),
    ("siniestro", ("siniestro", "expediente", "reclamo")),
    ("renovacion", ("renov", "vence", "vencimiento", "caduca")),
    ("certificado", ("certificado", "vigencia", "vigente", "poliza")),
    ("vehicular", ("espejo", "robo", "robaron", "plan", "planes", "vehicular", "vehiculo",
                   "todo riesgo", "cobertura", "deducible", "cubre")),
    ("soat", ("soat", "moto", "motos", "cotiz", "precio", "costo", "cuesta", "comprar", "pagar",
              "auto", "autos", "carro")),
    # "quiero un seguro" sin especificar cuál -> mostrar opciones
    ("menu", ("seguro", "asegur", "informacion", "ayuda", "opciones", "que ofrecen", "que venden")),
    ("despedida", ("gracias", "chau", "adios", "hasta luego", "eso es todo",
                   "thanks", "thank you", "bye")),
    ("saludo", ("hola", "ola", "buenas", "buen dia", "buenos dias", "que tal",
                "hello", "hi", "hey", "good morning", "good afternoon")),
]

# Intenciones que el bot resuelve sin LLM (respuestas fijas y seguras).
DETERMINISTAS = {"emergencia", "fuera_de_alcance", "despedida", "saludo", "asesor", "menu"}
# Intenciones donde se ofrece derivar a una persona.
DERIVABLES = {"soat", "vehicular", "grua", "accidente", "siniestro", "certificado", "renovacion", "asesor"}
REQUIEREN_ASESOR = {"emergencia", "asesor", "grua", "siniestro", "accidente"}

# Palabras cortas que deben coincidir completas ('robo' no es 'robot', 'moto' no es 'motor').
EXACTAS = {"robo", "auto", "moto", "ola", "plan", "hi", "hey"}

# Vocabulario del negocio para corregir errores de tipeo ("sefuro" -> "seguro").
# Solo palabras de 5+ letras: las muy cortas generan falsos positivos.
VOCABULARIO = [
    "seguro", "seguros", "asegurar", "vehicular", "vehiculo", "accidente", "choque", "chocaron",
    "siniestro", "certificado", "vigencia", "vigente", "poliza", "renovar", "renovacion",
    "vencimiento", "espejo", "espejos", "cobertura", "deducible", "cotizar", "cotizacion",
    "precio", "comprar", "carro", "asesor", "humano", "emergencia", "herido", "heridos",
    "ambulancia", "remolque", "planes", "gracias", "buenas", "reclamo", "atropello",
]


def corregir(texto: str) -> str:
    """Normaliza (minúsculas, sin tildes) y corrige palabras mal escritas que se
    parezcan en un 80 % o más a una del vocabulario.

    Ej.: 'Quiero sefuro vehicualr' -> 'quiero seguro vehicular'
    """
    def arreglar(m: re.Match) -> str:
        palabra = m.group(0)
        if len(palabra) < 5 or palabra in VOCABULARIO:
            return palabra
        parecida = get_close_matches(palabra, VOCABULARIO, n=1, cutoff=0.8)
        return parecida[0] if parecida else palabra

    return re.sub(r"[a-z]+", arreglar, normalizar(texto))


def _patron(clave: str) -> str:
    """Una palabra se compara como prefijo ('accident' -> accidente).
    Una frase o palabra corta debe aparecer completa
    ('que es' no coincide con 'que espejos'; 'robo' no coincide con 'robot')."""
    completa = " " in clave or clave in EXACTAS
    return r"\b" + re.escape(clave) + (r"\b" if completa else "")


def detectar_intencion(texto: str) -> str:
    t = corregir(texto)
    for intencion, claves in REGLAS:
        if any(re.search(_patron(k), t) for k in claves):
            return intencion
    return "general"