"""Los 3 escenarios que pide el proyecto: flujo feliz, error y fuera de alcance."""
import pytest

from app.bot.asistente import Asistente


# ---------- 1. Flujo feliz: cotizar SOAT y dejar datos -> derivación ----------
def test_flujo_feliz_cotizacion_y_derivacion(bot):
    r1 = bot.responder("¿Cuánto cuesta el SOAT para mi moto?")
    assert r1.intencion == "soat" and "490" in r1.respuesta

    r2 = bot.responder("Mi placa es ABC-123", r1.session_id)
    assert r2.intencion == "soat"  # memoria: hereda la intención previa
    assert r2.solicitud_id is not None and "celular" in r2.respuesta

    r3 = bot.responder("987654321", r1.session_id)
    assert r3.solicitud_id == r2.solicitud_id  # completa la misma solicitud
    sol = bot.repo.listar_solicitudes()[0]
    assert sol["placa"] == "ABC-123" and sol["telefono"] == "987654321"
    assert r3.turno == 3


# ---------- 2. Errores ----------
def test_error_mensaje_vacio(bot):
    with pytest.raises(ValueError):
        bot.responder("   ")


def test_error_mensaje_muy_largo(bot):
    with pytest.raises(ValueError):
        bot.responder("a" * 5000)


def test_error_placa_invalida(bot):
    r = bot.responder("Mi placa es 12")
    assert r.entidades.placa_invalida and "formato" in r.respuesta
    assert r.solicitud_id is None


def test_error_llm_caido_usa_respaldo(bot):
    class LLMRoto:
        def generar(self, **_):
            raise ConnectionError("sin red")

    bot.llm = LLMRoto()
    r = bot.responder("¿Cuánto cuesta el SOAT para auto?")
    assert r.modo == "demo_fallback" and "135" in r.respuesta


# ---------- 3. Fuera de alcance ----------
@pytest.mark.parametrize("texto", ["¿Quién ganó el mundial de fútbol?", "Dame una receta de ceviche"])
def test_fuera_de_alcance(bot, texto):
    r = bot.responder(texto)
    assert r.intencion == "fuera_de_alcance" and r.modo == "regla"


def test_fuera_de_alcance_no_llama_al_llm(bot):
    class LLMEspia:
        llamado = False

        def generar(self, **_):
            LLMEspia.llamado = True
            return "x"

    bot.llm = LLMEspia()
    bot.responder("¿Cuál es la capital de Francia?")
    assert not LLMEspia.llamado


# ---------- Caso crítico ----------
def test_emergencia_siempre_regla_y_asesor(bot):
    r = bot.responder("Hay heridos tras el choque")
    assert r.intencion == "emergencia" and r.modo == "regla" and r.requiere_asesor
    assert "106" in r.respuesta


def test_llm_recibe_contexto(bot):
    recibido = {}

    class LLMFalso:
        def generar(self, **v):
            recibido.update(v)
            return "Respuesta del LLM"

    bot.llm = LLMFalso()
    r = bot.responder("¿Qué es un deducible?")
    assert r.modo == "deepseek" and "deducible" in recibido["contexto"].lower()


def test_historial_persistente(entorno_demo):
    r = Asistente(entorno_demo).responder("Hola")
    # Una nueva instancia (como reiniciar el servidor) conserva la conversación
    assert len(Asistente(entorno_demo).repo.historial(r.session_id)) == 2


def test_pedido_generico_muestra_opciones(bot):
    r = bot.responder("quiero sefuro")
    assert r.intencion == "menu" and "SOAT" in r.respuesta and "vehicular" in r.respuesta
