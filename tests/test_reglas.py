"""Pruebas unitarias: intenciones, extracción de datos, recuperación y precios."""
import pytest

from app.bot.conocimiento import recuperar
from app.bot.intenciones import detectar_intencion
from app.bot.precios import cotizar
from app.bot.textos import extraer_entidades


@pytest.mark.parametrize(
    "texto, esperada",
    [
        ("SOAT para moto", "soat"),
        ("¿Me mandan una grúa?", "grua"),
        ("Hay heridos tras el choque", "emergencia"),  # emergencia gana sobre accidente
        ("¿Cubren robo de espejos?", "vehicular"),
        ("Quiero renovar mi SOAT", "renovacion"),
        ("¿Qué es un deducible?", "consulta"),
        ("¿Qué espejos cubren?", "vehicular"),  # 'que es' no debe coincidir con 'que espejos'
        ("Quiero hablar con un asesor", "asesor"),
        ("Hola", "saludo"),
        ("¿Quién ganó el mundial?", "general"),
    ],
)
def test_intenciones(texto, esperada):
    assert detectar_intencion(texto) == esperada


@pytest.mark.parametrize(
    "texto, esperada",
    [
        ("quiero sefuro", "menu"),          # error de tipeo + pedido genérico
        ("quiero un seguro", "menu"),
        ("seguro vehicualr", "vehicular"),
        ("cotisar soat para moto", "soat"),
        ("tuve un acidente", "accidente"),
        ("mi carro chocó", "accidente"),
        ("quiero renobar", "renovacion"),
        ("cobertua de espejos", "vehicular"),
        ("mi robot no funciona", "general"),  # 'robot' no es 'robo'
    ],
)
def test_tolera_errores_de_tipeo(texto, esperada):
    assert detectar_intencion(texto) == esperada


def test_extrae_placa_y_telefono():
    e = extraer_entidades("Mi placa es abc123 y mi cel 987 654 321")
    assert e.placa == "ABC-123"
    assert e.telefono == "987654321"
    assert not e.placa_invalida


def test_placa_moto():
    assert extraer_entidades("placa 1234-AB").placa == "1234-AB"


def test_placa_invalida():
    e = extraer_entidades("mi placa es 12")
    assert e.placa is None and e.placa_invalida


def test_numero_sin_letras_no_es_placa():
    assert extraer_entidades("siniestro 123456").placa is None


def test_recuperacion_encuentra_seccion():
    secciones = [f.seccion for f, _ in recuperar("¿Cómo solicito una grúa?", "grua")]
    assert secciones[0] == "Grúa"


def test_recuperacion_vacia_fuera_de_alcance():
    assert recuperar("Dame una receta de ceviche") == []


def test_precios_salen_del_json():
    assert "490" in cotizar("soat", "moto")
    assert "135" in cotizar("soat", "auto")
    assert all(p in cotizar("vehicular", "") for p in ("95", "155", "235"))
