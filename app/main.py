"""API web (FastAPI): canal de entrada del chatbot + interfaz web.

Ejecutar:  python -m app   (o)   uvicorn app.main:app --reload
Docs:      http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.bot.asistente import Asistente
from app.bot.polizas import buscar
from app.bot.precios import catalogo
from app.config import STATIC_DIR, Settings
from app.models import ChatRequest, ChatResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(settings: Settings | None = None) -> FastAPI:
    bot = Asistente(settings)
    app = FastAPI(
        title="CHULLS Seguros · Chatbot",
        version="2.0",
        description="Asistente de SOAT, seguro vehicular y postventa · LangChain + DeepSeek + SQLite",
    )
    app.state.bot = bot

    @app.get("/", include_in_schema=False)
    def inicio():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health", tags=["sistema"])
    def health():
        return {"estado": "ok", "modo": bot.modo, "modelo": bot.settings.deepseek_model if bot.llm else "reglas"}

    @app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
    def chat(req: ChatRequest):
        try:
            return bot.responder(req.mensaje, req.session_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/sesiones/{session_id}", tags=["chat"])
    def ver_sesion(session_id: str):
        return {"session_id": session_id, "mensajes": bot.repo.historial(session_id)}

    @app.delete("/api/sesiones/{session_id}", tags=["chat"])
    def borrar_sesion(session_id: str):
        bot.repo.borrar_sesion(session_id)
        return {"ok": True}

    @app.get("/api/catalogo", tags=["negocio"])
    def ver_catalogo():
        return catalogo()

    @app.get("/api/polizas", tags=["negocio"])
    def ver_polizas(placa: str | None = None, dni: str | None = None):
        """Consulta de pólizas por placa (ABC-123) o DNI."""
        if not placa and not dni:
            raise HTTPException(status_code=400, detail="Indica placa o dni.")
        return [
            {**p.__dict__, "inicio": p.inicio.isoformat(), "fin": p.fin.isoformat()}
            for p in buscar(placa.upper() if placa else None, dni)
        ]

    @app.get("/api/solicitudes", tags=["negocio"])
    def ver_solicitudes():
        """Derivaciones a asesor registradas por el bot (bandeja del equipo humano)."""
        return bot.repo.listar_solicitudes()

    @app.get("/api/metricas", tags=["negocio"])
    def ver_metricas():
        return bot.repo.metricas()

    return app


app = create_app()
