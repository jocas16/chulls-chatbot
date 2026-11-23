"""Configuración central: lee variables de entorno (.env) en un solo lugar."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = Path(__file__).resolve().parent / "static"

load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str
    deepseek_model: str
    deepseek_base_url: str
    modo: str  # "auto" | "demo"
    db_path: Path
    max_caracteres: int
    turnos_historial: int

    @property
    def usa_llm(self) -> bool:
        """El LLM se usa solo si hay clave y no se forzó el modo demo."""
        return self.modo != "demo" and bool(self.deepseek_api_key)


def get_settings() -> Settings:
    """Se lee en cada llamada para que los tests puedan cambiar el entorno."""
    db = os.getenv("DB_PATH", "data/chulls.db")
    db_path = Path(db) if Path(db).is_absolute() else BASE_DIR / db
    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        modo=os.getenv("MODO", "auto").strip().lower(),
        db_path=db_path,
        max_caracteres=int(os.getenv("MAX_CARACTERES", "1000")),
        turnos_historial=int(os.getenv("TURNOS_HISTORIAL", "6")),
    )
