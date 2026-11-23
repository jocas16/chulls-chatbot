"""Modelos de datos (Pydantic) que definen el contrato de la API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    mensaje: str = Field(min_length=1, max_length=5000, examples=["¿Cuánto cuesta el SOAT para moto?"])
    session_id: str | None = Field(default=None, description="Vacío en el primer mensaje")


class Entidades(BaseModel):
    placa: str | None = None
    telefono: str | None = None
    dni: str | None = None
    placa_invalida: bool = False


class ChatResponse(BaseModel):
    session_id: str
    respuesta: str
    intencion: str
    modo: str = Field(description="deepseek | demo | demo_fallback | regla")
    modelo: str
    requiere_asesor: bool
    fuentes: list[str]
    entidades: Entidades
    solicitud_id: int | None = Field(default=None, description="ID de la derivación registrada")
    turno: int


class Mensaje(BaseModel):
    rol: str
    contenido: str
    intencion: str | None = None
    creado: str
