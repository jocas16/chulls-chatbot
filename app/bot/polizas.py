"""Consulta de pólizas (postventa) desde data/polizas.csv.

Permite al bot responder con datos del cliente: vigencia, certificado y
renovación, buscando por placa o DNI. El estado se RECALCULA con las fechas
(no se confía en la columna 'estado', que puede estar desactualizada).
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from app.config import DATA_DIR

log = logging.getLogger("chulls")

DIAS_AVISO = 30  # "por vencer" si faltan 30 días o menos

NOMBRE_PLAN = {"VEH_BASICO": "Básico", "VEH_INTERMEDIO": "Intermedio", "VEH_TOTAL": "Total"}


@dataclass(frozen=True)
class Poliza:
    nro: str
    producto: str  # SOAT | VEH
    plan: str
    dni: str
    placa: str
    inicio: date
    fin: date
    moneda: str
    prima: float
    renovacion_automatica: bool
    certificado_url: str

    @property
    def nombre(self) -> str:
        return "SOAT" if self.producto == "SOAT" else f"Seguro vehicular {NOMBRE_PLAN.get(self.plan, self.plan)}"

    def dias_restantes(self, hoy: date) -> int:
        return (self.fin - hoy).days

    def estado(self, hoy: date) -> str:
        dias = self.dias_restantes(hoy)
        if dias < 0:
            return "vencida"
        return "por_vencer" if dias <= DIAS_AVISO else "vigente"


@lru_cache
def cargar_polizas(ruta=DATA_DIR / "polizas.csv") -> tuple[Poliza, ...]:
    """Lee y limpia el CSV. Las filas con datos inválidos se omiten (y se registran en el log)."""
    if not ruta.exists():
        log.warning("No se encontró %s: la consulta de pólizas está desactivada.", ruta)
        return ()
    polizas, descartadas = [], 0
    with ruta.open(encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            try:
                polizas.append(
                    Poliza(
                        nro=fila["nro_poliza"].strip(),
                        producto=fila["producto"].strip().upper(),
                        plan=fila["plan_id"].strip(),
                        dni=fila["dni"].strip(),
                        placa=fila["placa"].strip().upper(),
                        inicio=date.fromisoformat(fila["inicio_vigencia"].strip()),
                        fin=date.fromisoformat(fila["fin_vigencia"].strip()),
                        moneda=fila["moneda"].strip(),
                        prima=float(fila["prima_anual"] or 0),
                        renovacion_automatica=fila["renovacion_automatica"].strip().lower() == "si",
                        certificado_url=fila["certificado_url"].strip(),
                    )
                )
            except (KeyError, ValueError):
                descartadas += 1
    if descartadas:
        log.warning("polizas.csv: %d filas descartadas por datos inválidos", descartadas)
    return tuple(polizas)


def buscar(placa: str | None = None, dni: str | None = None) -> list[Poliza]:
    if not placa and not dni:
        return []
    return [p for p in cargar_polizas() if (placa and p.placa == placa) or (dni and p.dni == dni)]


def _fecha(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _linea_estado(p: Poliza, hoy: date) -> str:
    dias = p.dias_restantes(hoy)
    estado = p.estado(hoy)
    if estado == "vencida":
        return f"❌ VENCIDA desde el {_fecha(p.fin)} (hace {-dias} días)"
    if estado == "por_vencer":
        return f"⚠️ Por vencer: vence el {_fecha(p.fin)} (en {dias} días)"
    return f"✅ Vigente hasta el {_fecha(p.fin)}"


def respuesta_consulta(polizas: list[Poliza], intencion: str, hoy: date | None = None) -> str:
    """Texto con el detalle de las pólizas encontradas (vigencia / certificado / renovación)."""
    hoy = hoy or date.today()
    bloques = []
    for p in sorted(polizas, key=lambda x: (x.placa, x.producto)):
        lineas = [f"**{p.nombre}** · {p.nro} · placa {p.placa}", _linea_estado(p, hoy)]
        if intencion == "certificado" and p.estado(hoy) != "vencida":
            lineas.append(f"📄 Certificado: {p.certificado_url}")
        if intencion == "renovacion" and p.estado(hoy) != "vigente":
            if p.renovacion_automatica:
                lineas.append("🔁 Tiene renovación automática activada.")
            else:
                lineas.append(f"💳 Renovación referencial: {p.moneda} {p.prima:,.2f}/año (lo confirma un asesor).")
        bloques.append("\n".join(lineas))

    texto = "Encontré estas pólizas:\n\n" + "\n\n".join(bloques)
    if any(p.estado(hoy) == "vencida" and p.producto == "SOAT" for p in polizas):
        texto += "\n\n🚫 Circular con el SOAT vencido no está permitido. ¿Quieres que un asesor te ayude a renovarlo?"
    elif any(p.estado(hoy) == "por_vencer" for p in polizas):
        texto += "\n\n¿Quieres que un asesor te contacte para renovar a tiempo?"
    else:
        texto += "\n\n¿Necesitas algo más?"
    return texto


def resumen_cobertura(polizas: list[Poliza], hoy: date | None = None) -> str:
    """Línea corta para accidentes/grúa/siniestros: qué seguros activos tiene el vehículo."""
    hoy = hoy or date.today()
    activas = [p.nombre for p in polizas if p.estado(hoy) != "vencida"]
    if not activas:
        return "\n\n⚠️ No encontré pólizas vigentes para ese vehículo; el asesor lo revisará."
    return "\n\n🛡️ En nuestro registro el vehículo tiene vigente: " + ", ".join(activas) + "."
