import sys
from pathlib import Path

import pytest

# Permite ejecutar `pytest` desde la raíz sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bot.asistente import Asistente  # noqa: E402
from app.config import get_settings  # noqa: E402


@pytest.fixture
def entorno_demo(monkeypatch, tmp_path):
    """Modo demo (sin red) y base de datos temporal en cada test."""
    monkeypatch.setenv("MODO", "demo")
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    return get_settings()


@pytest.fixture
def bot(entorno_demo):
    return Asistente(entorno_demo)
