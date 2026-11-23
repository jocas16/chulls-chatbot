"""Orquestador del chatbot: une intención, recuperación, LLM y almacenamiento.

Flujo de un mensaje:
  1. Validar entrada
  2. Detectar intención (reglas) + extraer placa/teléfono
  3. Usar memoria: si el mensaje es una continuación, heredar la intención previa
  4. Recuperar contexto de la base de conocimiento (RAG)
  5. Guardrails: emergencias / fuera de alcance / datos inválidos -> respuesta fija
  6. Postventa: si hay placa/DNI, consultar pólizas reales (data/polizas.csv)
  7. Generar respuesta con DeepSeek (o respuesta fija en modo demo / si falla)
  8. Registrar derivación (si hay datos) y guardar todo en SQLite
"""
from __future__ import annotations

import json
import logging
import uuid

from app.bot import intenciones as it
from app.bot.conocimiento import recuperar
from app.bot.polizas import buscar, respuesta_consulta, resumen_cobertura
from app.bot.precios import catalogo
from app.bot.respuestas import RESPUESTAS, confirmacion_solicitud, respuesta_fija
from app.bot.textos import extraer_entidades
from app.config import Settings, get_settings
from app.models import ChatResponse
from app.storage import Repositorio

log = logging.getLogger("chulls")

# Intenciones que se resuelven consultando las pólizas del cliente
POSTVENTA_CONSULTA = {"certificado", "renovacion"}


class Asistente:
    def __init__(self, settings: Settings | None = None, repo: Repositorio | None = None):
        self.settings = settings or get_settings()
        self.repo = repo or Repositorio(self.settings.db_path)
        self.llm = None
        if self.settings.usa_llm:
            from app.bot.llm import GeneradorLLM

            self.llm = GeneradorLLM(self.settings)

    @property
    def modo(self) -> str:
        return "deepseek" if self.llm else "demo"

    # ------------------------------------------------------------------
    def _resolver_intencion(self, mensaje: str, session_id: str, tiene_datos: bool) -> tuple[str, list, bool]:
        intencion, heredada = it.detectar_intencion(mensaje), False
        if intencion == "general":
            previa = self.repo.ultima_intencion(session_id)
            # "mi placa es ABC-123" continúa la conversación anterior (memoria)
            if previa and tiene_datos:
                intencion, heredada = previa, True
            elif tiene_datos:  # deja sus datos sin contexto previo -> derivar a asesor
                intencion, heredada = "asesor", True
        docs = recuperar(it.corregir(mensaje), intencion)
        if intencion in ("general", "consulta") and not docs:
            intencion = "fuera_de_alcance"
        return intencion, docs, heredada

    def responder(self, mensaje: str, session_id: str | None = None) -> ChatResponse:
        mensaje = (mensaje or "").strip()
        if not mensaje:
            raise ValueError("Escribe un mensaje.")
        if len(mensaje) > self.settings.max_caracteres:
            raise ValueError(f"Mensaje demasiado largo (máximo {self.settings.max_caracteres} caracteres).")

        sid = session_id or uuid.uuid4().hex
        historial = self.repo.historial(sid, self.settings.turnos_historial * 2)
        entidades = extraer_entidades(mensaje)
        tiene_datos = bool(entidades.placa or entidades.telefono or entidades.dni or entidades.placa_invalida)
        intencion, docs, heredada = self._resolver_intencion(mensaje, sid, tiene_datos)

        # --- Postventa: buscar pólizas del cliente por placa o DNI ------------
        polizas = buscar(entidades.placa, entidades.dni)
        consulta_poliza = intencion in POSTVENTA_CONSULTA and bool(entidades.placa or entidades.dni)
        resuelto = False

        # --- Guardrails y respuestas deterministas -----------------------
        if entidades.placa_invalida:
            respuesta, modo = RESPUESTAS["placa_invalida"], "regla"
        elif consulta_poliza and polizas:
            # Datos reales: se responden sin LLM para no inventar fechas ni estados
            respuesta, modo, resuelto = respuesta_consulta(polizas, intencion), "datos", True
        elif consulta_poliza:
            respuesta, modo = RESPUESTAS["no_encontrada"], "regla"
        elif intencion in it.DETERMINISTAS:
            respuesta, modo = respuesta_fija(intencion, mensaje), "regla"
        elif self.llm:
            try:
                respuesta = self.llm.generar(
                    intencion=intencion,
                    entidades=entidades.model_dump_json(),
                    contexto="\n\n".join(f.contenido for f, _ in docs) or "(sin contexto)",
                    precios=json.dumps(catalogo(), ensure_ascii=False),
                    historial="\n".join(f"{h['rol']}: {h['contenido']}" for h in historial) or "(inicio)",
                    pregunta=mensaje,
                )
                modo = "deepseek"
            except Exception as exc:  # red caída, clave inválida, sin saldo...
                log.warning("DeepSeek no respondió: %s", exc)
                respuesta = "(DeepSeek no respondió; muestro una respuesta local)\n\n" + self._fija(intencion, mensaje, docs)
                modo = "demo_fallback"
        else:
            respuesta, modo = self._fija(intencion, mensaje, docs), "demo"

        # --- Derivación a asesor -----------------------------------------
        solicitud_id = None
        if not resuelto and (entidades.placa or entidades.telefono) and intencion in it.DERIVABLES | {"emergencia"}:
            previa = self.repo.solicitud_de_sesion(sid, intencion)
            if previa:
                self.repo.actualizar_solicitud(previa["id"], entidades.placa, entidades.telefono)
                solicitud_id = previa["id"]
            else:
                solicitud_id = self.repo.registrar_solicitud(sid, intencion, entidades.placa, entidades.telefono)
            sol = self.repo.solicitud_de_sesion(sid, intencion)
            if heredada and modo not in ("deepseek", "regla"):  # sin LLM, no repetimos la respuesta anterior
                respuesta = "🚨 Caso marcado como PRIORITARIO." if intencion == "emergencia" else "¡Gracias por los datos!"
            respuesta += confirmacion_solicitud(solicitud_id, sol["placa"], sol["telefono"])
            if polizas and intencion in ("grua", "accidente", "siniestro", "emergencia"):
                respuesta += resumen_cobertura(polizas)

        # --- Persistencia --------------------------------------------------
        self.repo.guardar_mensaje(sid, "usuario", mensaje, intencion)
        self.repo.guardar_mensaje(sid, "asistente", respuesta, intencion, modo)

        return ChatResponse(
            session_id=sid,
            respuesta=respuesta,
            intencion=intencion,
            modo=modo,
            modelo=self.settings.deepseek_model if modo == "deepseek" else "reglas",
            requiere_asesor=not resuelto and (intencion in it.REQUIEREN_ASESOR or solicitud_id is not None),
            fuentes=[f.seccion for f, _ in docs],
            entidades=entidades,
            solicitud_id=solicitud_id,
            turno=len(historial) // 2 + 1,
        )

    @staticmethod
    def _fija(intencion: str, mensaje: str, docs: list) -> str:
        """Respuesta sin LLM. Para preguntas generales devuelve la sección más relevante."""
        if intencion in ("general", "consulta") and docs:
            fragmento = docs[0][0]
            cuerpo = fragmento.contenido.split("\n", 1)[-1].strip()
            return f"Según nuestra información ({fragmento.seccion}): {cuerpo}\n\n¿Te ayudo con algo más?"
        return respuesta_fija(intencion, mensaje)
