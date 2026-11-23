"""Integración LangChain + DeepSeek (API compatible con OpenAI).

LangChain se importa de forma diferida para que el bot funcione en modo demo
y los tests corran aunque no haya red ni clave.
"""
from __future__ import annotations

from app.config import Settings

SYSTEM = """Eres CHULLS Bot, asistente DEMOSTRATIVO de CHULLS Seguros (Perú).
Responde en español, claro, cálido y BREVE (máximo 120 palabras).
Alcance: venta de SOAT, seguro vehicular y postventa (certificado/vigencia,
accidente, grúa, seguimiento de siniestro, renovación).

REGLAS:
- Usa SOLO el CONTEXTO y los PRECIOS. Si algo no está, dilo y ofrece un asesor.
- Los precios son FICTICIOS. No inventes costos, coberturas, teléfonos ni plazos.
- No afirmes haber emitido pólizas, cobrado, enviado grúas ni aprobado siniestros.
- No pidas datos bancarios ni contraseñas. No des asesoría médica ni legal.
- Si falta la placa o el teléfono para derivar, pídelos.
- Para consultar vigencia, certificado o renovación pide la placa o el DNI.
- Termina con una pregunta útil.

INTENCIÓN DETECTADA: {intencion}
DATOS YA CAPTURADOS: {entidades}
CONTEXTO RECUPERADO:
{contexto}

PRECIOS DEMO:
{precios}

HISTORIAL RECIENTE:
{historial}
"""


class GeneradorLLM:
    def __init__(self, settings: Settings):
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("human", "{pregunta}")])
        modelo = ChatOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            temperature=0.2,
            timeout=30,
            max_retries=1,
        )
        # Cadena LCEL: prompt -> modelo -> texto
        self.cadena = prompt | modelo | StrOutputParser()

    def generar(self, **variables: str) -> str:
        return self.cadena.invoke(variables).strip()
