"""Pruebas de la API HTTP con el cliente de pruebas de FastAPI."""
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


@pytest.fixture
def cliente(entorno_demo):
    return TestClient(create_app(entorno_demo))


def test_health(cliente):
    assert cliente.get("/api/health").json()["modo"] == "demo"


def test_chat_y_sesion(cliente):
    r = cliente.post("/api/chat", json={"mensaje": "SOAT para moto"})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    assert len(cliente.get(f"/api/sesiones/{sid}").json()["mensajes"]) == 2


def test_chat_mensaje_vacio_400(cliente):
    assert cliente.post("/api/chat", json={"mensaje": "   "}).status_code == 400


def test_chat_sin_mensaje_422(cliente):
    assert cliente.post("/api/chat", json={}).status_code == 422


def test_metricas_y_solicitudes(cliente):
    cliente.post("/api/chat", json={"mensaje": "Necesito grúa, placa ABC-123, cel 987654321"})
    assert cliente.get("/api/metricas").json()["solicitudes_derivadas"] == 1
    assert cliente.get("/api/solicitudes").json()[0]["placa"] == "ABC-123"
