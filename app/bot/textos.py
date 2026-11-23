"""Utilidades de texto: normalización y extracción de datos (placa, teléfono, DNI)."""
from __future__ import annotations

import re
import unicodedata

from app.models import Entidades

# Placa de auto: ABC-123 / A1B-234 (al menos una letra en el primer bloque).
_PLACA_AUTO = re.compile(r"\b(?=[A-Z0-9]{0,2}[A-Z])[A-Z0-9]{3}-?\d{3}\b")
# Placa de moto: 1234-AB
_PLACA_MOTO = re.compile(r"\b\d{4}-?[A-Z]{2}\b")
# Celular peruano: 9 dígitos empezando en 9
_TELEFONO = re.compile(r"(?<!\d)9\d{8}(?!\d)")
# DNI peruano: 8 dígitos exactos
_DNI = re.compile(r"(?<!\d)\d{8}(?!\d)")
_TRAS_PALABRA_PLACA = re.compile(r"placa\s*(?:es|:|numero|nro\.?|n°)?\s*([a-z0-9-]+)")


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes: 'Grúa' -> 'grua'."""
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")


def _formatear_placa(valor: str) -> str:
    """Estandariza con guion: ABC123 -> ABC-123, 1234AB -> 1234-AB."""
    limpio = valor.replace("-", "")
    corte = 4 if limpio[:4].isdigit() else 3
    return f"{limpio[:corte]}-{limpio[corte:]}"


def extraer_entidades(texto: str) -> Entidades:
    mayus = texto.upper()
    placa = _PLACA_AUTO.search(mayus) or _PLACA_MOTO.search(mayus)
    # Unir dígitos separados por espacios o guiones: "987 654 321" -> "987654321"
    compacto = re.sub(r"(?<=\d)[\s-](?=\d)", "", texto)
    telefono = _TELEFONO.search(compacto)
    dni = _DNI.search(texto)

    placa_invalida = False
    if not placa:
        m = _TRAS_PALABRA_PLACA.search(normalizar(texto))
        # Escribió algo con números después de "placa" pero no tiene formato válido
        placa_invalida = bool(m and any(c.isdigit() for c in m.group(1)))

    return Entidades(
        placa=_formatear_placa(placa.group(0)) if placa else None,
        telefono=telefono.group(0) if telefono else None,
        dni=dni.group(0) if dni else None,
        placa_invalida=placa_invalida,
    )
