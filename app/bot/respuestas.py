"""Respuestas fijas: se usan en modo demo, como respaldo si el LLM falla
y como 'guardrails' en casos sensibles (emergencias, fuera de alcance)."""
from __future__ import annotations

from app.bot.precios import cotizar

ALCANCE = "SOAT, seguro vehicular y postventa (certificados, accidentes, grúa, siniestros y renovación)"

RESPUESTAS = {
    "emergencia": (
        "🚨 Si hay personas heridas o peligro inmediato, llama a emergencias (SAMU 106 / Bomberos 116 / "
        "Policía 105) y ponte a salvo. Este asistente no atiende emergencias médicas. "
        "Estoy marcando tu caso para que un asesor humano te contacte de inmediato. "
        "¿Me compartes tu placa y un teléfono?"
    ),
    "fuera_de_alcance": (
        "Esa consulta está fuera de lo que puedo atender 🙂. Soy el asistente de CHULLS Seguros y "
        f"te ayudo con {ALCANCE}. ¿Te gustaría cotizar un SOAT o comparar planes vehiculares?"
    ),
    "saludo": (
        "¡Hola! Soy CHULLS Bot 👋. Te ayudo con " + ALCANCE + ". ¿Qué necesitas hoy?"
    ),
    "menu": (
        "¡Con gusto! Estas son las opciones:\n"
        "• 🚗 SOAT (auto o moto): obligatorio para circular\n"
        "• 🛡️ Seguro vehicular: planes Básico, Intermedio y Premium\n"
        "• 🧰 Postventa: accidente, grúa, certificado, siniestro o renovación\n"
        "¿Cuál te interesa?"
    ),
    "despedida": "¡Gracias por escribirnos! Si necesitas algo más sobre tu seguro, aquí estaré. 🚗",
    "asesor": (
        "Claro, te derivo con un asesor humano. Para que te contacten, compárteme tu placa "
        "(ej. ABC-123) y un celular de 9 dígitos."
    ),
    "grua": (
        "Puedo registrar tu solicitud de grúa, pero no despacharla directamente. "
        "¿En qué zona estás, cuál es tu placa y un teléfono de contacto?"
    ),
    "accidente": (
        "Primero verifica que estés en un lugar seguro y si hay heridos. Si no hay heridos: toma fotos, "
        "anota la placa del otro vehículo y sus datos. No puedo aprobar un siniestro, pero puedo "
        "derivarte a un asesor. ¿Me das tu placa y teléfono?"
    ),
    "siniestro": (
        "No tengo conexión con el sistema real de siniestros. Indícame tu número de siniestro y un "
        "teléfono, y lo derivo para seguimiento."
    ),
    "certificado": (
        "Puedo revisar la vigencia y darte el certificado. "
        "Indícame tu placa (ej. ABC-123) o tu DNI."
    ),
    "renovacion": (
        "Te ayudo con la renovación. Indícame tu placa (ej. ABC-123) o tu DNI y reviso "
        "cuándo vencen tus pólizas."
    ),
    "no_encontrada": (
        "No encontré pólizas con esos datos. Verifica la placa o el DNI; si el dato es correcto, "
        "un asesor lo revisará."
    ),
    "placa_invalida": (
        "⚠️ No reconozco ese formato de placa. Debe ser como ABC-123 (auto) o 1234-AB (moto). "
        "¿Puedes revisarla y escribirla de nuevo?"
    ),
}


def respuesta_fija(intencion: str, texto: str) -> str:
    if intencion == "soat":
        return cotizar("soat", texto) + " Para continuar, indícame tu placa y un celular; un asesor validaría la compra."
    if intencion == "vehicular":
        return (
            cotizar("vehicular", texto)
            + "\n\nCoberturas específicas (p. ej. robo de espejos) se confirman con la póliza. "
            "¿Qué plan te interesa?"
        )
    return RESPUESTAS.get(intencion, RESPUESTAS["saludo"])


def confirmacion_solicitud(solicitud_id: int, placa: str | None, telefono: str | None) -> str:
    datos = ", ".join(x for x in (f"placa {placa}" if placa else "", f"celular {telefono}" if telefono else "") if x)
    texto = f"\n\n📋 Solicitud #{solicitud_id} registrada ({datos})."
    if not telefono:
        return texto + " ¿Me compartes un celular de 9 dígitos para que el asesor te contacte?"
    if not placa:
        return texto + " ¿Cuál es la placa del vehículo?"
    return texto + " Un asesor te contactará pronto (simulado en esta demo)."
