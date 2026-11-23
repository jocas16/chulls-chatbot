"""Base de conocimiento y recuperación (RAG ligero por coincidencia léxica).

Se divide base_conocimiento.md por secciones '## ' y se puntúa cada sección
según las palabras de la pregunta. Sin embeddings: suficiente para ~10
secciones y 100 % explicable en la demo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.bot.textos import normalizar
from app.config import DATA_DIR

STOPWORDS = {
    "para", "como", "tengo", "quiero", "puedo", "puede", "pueden", "esta", "este", "esto", "estan",
    "sobre", "cual", "cuales", "cuanto", "donde", "cuando", "porque", "tiene", "tienen", "hacer",
    "necesito", "dime", "favor", "hola", "gracias", "todo", "todos", "mucho", "algo", "desde",
    "hasta", "entre", "pero", "tambien", "solo", "seguro", "seguros", "quien", "ustedes", "usted",
    "chulls", "bueno", "buena", "buenas", "debo", "sera", "seria", "hace", "cosa", "saber",
}

# Palabra clave extra que se suma según la intención detectada.
ALIAS = {
    "emergencia": "accidente", "accidente": "accidente", "grua": "grua", "soat": "soat",
    "vehicular": "vehicular", "siniestro": "siniestro", "certificado": "certificado",
    "renovacion": "renovacion", "asesor": "asesor",
}


@dataclass(frozen=True)
class Fragmento:
    seccion: str
    contenido: str


@lru_cache
def cargar_fragmentos(ruta: Path = DATA_DIR / "base_conocimiento.md") -> tuple[Fragmento, ...]:
    texto = ruta.read_text(encoding="utf-8")
    bloques = re.split(r"(?=^## )", texto, flags=re.M)
    return tuple(
        Fragmento(seccion=b.splitlines()[0].lstrip("# ").strip(), contenido=b.strip())
        for b in bloques
        if b.startswith("## ")
    )


def _terminos(pregunta: str) -> set[str]:
    palabras = re.findall(r"\w+", normalizar(pregunta))
    return {p for p in palabras if len(p) > 3 and p not in STOPWORDS}


def puntuar(fragmento: Fragmento, terminos: set[str]) -> int:
    """+3 si el término aparece en el título de la sección, +1 si está en el cuerpo."""
    titulo, cuerpo = normalizar(fragmento.seccion), normalizar(fragmento.contenido)
    return sum(3 if t in titulo else 1 for t in terminos if t in cuerpo)


def recuperar(pregunta: str, intencion: str = "general", k: int = 3) -> list[tuple[Fragmento, int]]:
    """Devuelve hasta k secciones relevantes con su puntaje (lista vacía si nada coincide)."""
    terminos = _terminos(pregunta)
    if intencion in ALIAS:
        terminos.add(ALIAS[intencion])
    puntuados = [(f, puntuar(f, terminos)) for f in cargar_fragmentos()]
    puntuados = [x for x in puntuados if x[1] > 0]
    puntuados.sort(key=lambda x: x[1], reverse=True)
    return puntuados[:k]
