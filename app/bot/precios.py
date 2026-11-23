"""Cotizador: los precios salen SIEMPRE del JSON, nunca del LLM."""
from __future__ import annotations

import json
from functools import lru_cache

from app.bot.textos import normalizar
from app.config import DATA_DIR


@lru_cache
def catalogo() -> dict:
    return json.loads((DATA_DIR / "precios_demo.json").read_text(encoding="utf-8"))


def cotizar(intencion: str, texto: str) -> str:
    """Texto de cotización fija para SOAT o vehicular; vacío para otras intenciones."""
    t, cat = normalizar(texto), catalogo()
    if intencion == "soat":
        auto = cat["soat"]["auto_particular"]["precio_anual_pen"]
        moto = cat["soat"]["moto"]["precio_anual_pen"]
        if "moto" in t:
            return f"SOAT moto: S/ {moto} al año (precio ficticio de demostración)."
        if "auto" in t or "carro" in t:
            return f"SOAT auto particular: S/ {auto} al año (precio ficticio de demostración)."
        return f"SOAT (precios ficticios de demostración): auto particular S/ {auto}/año · moto S/ {moto}/año."
    if intencion == "vehicular":
        filas = [
            f"• {p['nombre']}: desde S/ {p['precio_mensual_desde_pen']}/mes — {p['coberturas']}"
            for p in cat["vehicular"].values()
        ]
        return "Planes vehiculares (precios ficticios):\n" + "\n".join(filas)
    return ""
