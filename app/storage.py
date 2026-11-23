"""Almacenamiento en SQLite: historial de conversaciones y solicitudes de derivación."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    rol TEXT NOT NULL,              -- usuario | asistente
    contenido TEXT NOT NULL,
    intencion TEXT,
    modo TEXT,
    creado TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_mensajes_sesion ON mensajes(session_id);
CREATE TABLE IF NOT EXISTS solicitudes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    intencion TEXT NOT NULL,
    placa TEXT,
    telefono TEXT,
    estado TEXT DEFAULT 'pendiente',
    creado TEXT DEFAULT (datetime('now', 'localtime'))
);
"""


class Repositorio:
    def __init__(self, ruta: Path):
        self.ruta = ruta
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with self._conexion() as con:
            con.executescript(ESQUEMA)

    @contextmanager
    def _conexion(self):
        con = sqlite3.connect(self.ruta)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    # --- mensajes ---------------------------------------------------------
    def guardar_mensaje(self, session_id: str, rol: str, contenido: str, intencion: str | None = None, modo: str | None = None) -> None:
        with self._conexion() as con:
            con.execute(
                "INSERT INTO mensajes (session_id, rol, contenido, intencion, modo) VALUES (?, ?, ?, ?, ?)",
                (session_id, rol, contenido, intencion, modo),
            )

    def historial(self, session_id: str, limite: int = 50) -> list[dict]:
        with self._conexion() as con:
            filas = con.execute(
                "SELECT rol, contenido, intencion, creado FROM mensajes WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limite),
            ).fetchall()
        return [dict(f) for f in reversed(filas)]

    def ultima_intencion(self, session_id: str) -> str | None:
        with self._conexion() as con:
            fila = con.execute(
                "SELECT intencion FROM mensajes WHERE session_id = ? AND rol = 'asistente' "
                "AND intencion NOT IN ('general', 'consulta', 'saludo', 'menu', 'despedida', 'fuera_de_alcance') ORDER BY id DESC LIMIT 1",
                (session_id,),
            ).fetchone()
        return fila["intencion"] if fila else None

    def borrar_sesion(self, session_id: str) -> None:
        with self._conexion() as con:
            con.execute("DELETE FROM mensajes WHERE session_id = ?", (session_id,))

    # --- solicitudes de derivación ---------------------------------------
    def registrar_solicitud(self, session_id: str, intencion: str, placa: str | None, telefono: str | None) -> int:
        with self._conexion() as con:
            cur = con.execute(
                "INSERT INTO solicitudes (session_id, intencion, placa, telefono) VALUES (?, ?, ?, ?)",
                (session_id, intencion, placa, telefono),
            )
            return int(cur.lastrowid)

    def solicitud_de_sesion(self, session_id: str, intencion: str) -> dict | None:
        """Última solicitud de la sesión para esa intención (para completarla en vez de duplicarla)."""
        with self._conexion() as con:
            fila = con.execute(
                "SELECT * FROM solicitudes WHERE session_id = ? AND intencion = ? ORDER BY id DESC LIMIT 1",
                (session_id, intencion),
            ).fetchone()
        return dict(fila) if fila else None

    def actualizar_solicitud(self, solicitud_id: int, placa: str | None, telefono: str | None) -> None:
        with self._conexion() as con:
            con.execute(
                "UPDATE solicitudes SET placa = COALESCE(?, placa), telefono = COALESCE(?, telefono) WHERE id = ?",
                (placa, telefono, solicitud_id),
            )

    def listar_solicitudes(self) -> list[dict]:
        with self._conexion() as con:
            return [dict(f) for f in con.execute("SELECT * FROM solicitudes ORDER BY id DESC").fetchall()]

    # --- métricas ----------------------------------------------------------
    def metricas(self) -> dict:
        with self._conexion() as con:
            por_intencion = con.execute(
                "SELECT intencion, COUNT(*) n FROM mensajes WHERE rol = 'asistente' GROUP BY intencion ORDER BY n DESC"
            ).fetchall()
            por_modo = con.execute(
                "SELECT modo, COUNT(*) n FROM mensajes WHERE rol = 'asistente' GROUP BY modo"
            ).fetchall()
            sesiones = con.execute("SELECT COUNT(DISTINCT session_id) FROM mensajes").fetchone()[0]
            solicitudes = con.execute("SELECT COUNT(*) FROM solicitudes").fetchone()[0]
        return {
            "conversaciones": sesiones,
            "respuestas_por_intencion": {f["intencion"]: f["n"] for f in por_intencion},
            "respuestas_por_modo": {f["modo"]: f["n"] for f in por_modo},
            "solicitudes_derivadas": solicitudes,
        }
