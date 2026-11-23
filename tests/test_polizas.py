"""Postventa: consulta de pólizas desde data/polizas.csv."""
from datetime import date

from app.bot.polizas import buscar, cargar_polizas, respuesta_consulta
from app.bot.textos import extraer_entidades

HOY = date(2026, 11, 22)


def test_csv_se_carga_completo():
    assert len(cargar_polizas()) == 174


def test_buscar_por_placa_y_dni():
    assert {p.nro for p in buscar(placa="ABC-123")} == {"SOAT-000123", "VEH-000045"}
    assert len(buscar(dni="53251559")) == 3
    assert buscar(placa="ZZZ-999") == []


def test_estado_se_calcula_con_fechas():
    soat = next(p for p in buscar(placa="ABC-123") if p.producto == "SOAT")
    # En el CSV figura 'vigente', pero venció el 19/11/2026
    assert soat.estado(HOY) == "vencida"
    hzh = next(p for p in buscar(placa="HZH-407") if p.producto == "SOAT")
    assert hzh.estado(HOY) == "por_vencer"


def test_respuesta_certificado_incluye_link_solo_si_no_esta_vencida():
    texto = respuesta_consulta(buscar(placa="ABC-123"), "certificado", HOY)
    assert "VEH-000045.pdf" in texto and "SOAT-000123.pdf" not in texto
    assert "SOAT vencido" in texto


def test_extrae_dni_sin_confundir_celular():
    assert extraer_entidades("mi dni es 45678912").dni == "45678912"
    e = extraer_entidades("mi celular es 987654321")
    assert e.dni is None and e.telefono == "987654321"


def test_flujo_postventa_resuelve_sin_asesor(bot):
    r1 = bot.responder("¿Mi SOAT está vigente?")
    assert r1.intencion == "certificado"
    r2 = bot.responder("ABC-123", r1.session_id)  # memoria: sigue en 'certificado'
    assert r2.modo == "datos" and "VEH-000045" in r2.respuesta
    assert not r2.requiere_asesor and r2.solicitud_id is None


def test_poliza_no_encontrada_deriva(bot):
    r = bot.responder("necesito mi certificado, placa ZZZ-999")
    assert "No encontré" in r.respuesta and r.solicitud_id is not None


def test_grua_muestra_cobertura(bot):
    r = bot.responder("Necesito una grúa, placa KHV-426, cel 987654321")
    assert r.solicitud_id and "Seguro vehicular Total" in r.respuesta
