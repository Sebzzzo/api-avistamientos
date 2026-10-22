from datetime import date

import pytest

from tests.dobles import RelojFijo
from validador import ValidadorDeAvistamiento

HOY = date(2026, 10, 21)


@pytest.fixture
def validador():
    return ValidadorDeAvistamiento(RelojFijo(HOY))

def datos_validos(**cambios):
    base = {
        "especie": "colibrí",
        "lugar": "Parque Simón Bolívar",
        "fecha": "2026-10-01",
        "observador": "Sebastián",
    }
    return {**base, **cambios}


def campos_con_error(errores):
    return [e.campo for e in errores]


# ---------- Caso base ----------

def test_avistamiento_con_todos_los_datos_validos_no_tiene_errores(validador):

    datos = datos_validos()

    errores = validador.validar(**datos)

    assert errores == []


# ---------- Especie: partición {<3 inválida | 3..50 válida | >50 inválida} ----------

def test_especie_de_2_caracteres_es_rechazada(validador):  # límite inferior - 1

    datos = datos_validos(especie="ab")

    errores = validador.validar(**datos)

    assert campos_con_error(errores) == ["especie"]


def test_especie_de_3_caracteres_es_aceptada(validador):  # límite inferior

    datos = datos_validos(especie="abc")

    errores = validador.validar(**datos)
  
    assert errores == []


def test_especie_de_50_caracteres_es_aceptada(validador):  # límite superior

    datos = datos_validos(especie="a" * 50)

    errores = validador.validar(**datos)

    assert errores == []


def test_especie_de_51_caracteres_es_rechazada(validador):  # límite superior + 1

    datos = datos_validos(especie="a" * 51)

    errores = validador.validar(**datos)

    assert campos_con_error(errores) == ["especie"]


@pytest.mark.parametrize("especie", ["", "     "], ids=["vacia", "solo_espacios"])
def test_especie_vacia_o_solo_espacios_es_rechazada(validador, especie):

    datos = datos_validos(especie=especie)

    errores = validador.validar(**datos)
  
    assert campos_con_error(errores) == ["especie"]


def test_espacios_alrededor_de_la_especie_no_cuentan_como_caracteres(validador):
 
    datos = datos_validos(especie="  ab  ")

    errores = validador.validar(**datos)

    assert campos_con_error(errores) == ["especie"]


# ---------- Fecha: partición {formato malo | no existe | futura | <= hoy} ----------

def test_fecha_de_hoy_es_aceptada(validador):  # límite: hoy

    datos = datos_validos(fecha="2026-10-21")

    errores = validador.validar(**datos)

    assert errores == []


def test_fecha_de_manana_es_rechazada(validador):  # límite: hoy + 1

    datos = datos_validos(fecha="2026-10-22")

    errores = validador.validar(**datos)

    assert campos_con_error(errores) == ["fecha"]
    assert "posterior a hoy" in errores[0].mensaje


def test_fecha_de_ayer_es_aceptada(validador):  # límite: hoy - 1

    datos = datos_validos(fecha="2026-10-20")

    errores = validador.validar(**datos)

    assert errores == []


@pytest.mark.parametrize(
    "fecha",
    ["29/09/2026", "2026-9-29", "20260929", "", "ayer"],
    ids=["con_barras", "sin_cero", "sin_guiones", "vacia", "texto"],
)
def test_fecha_con_formato_distinto_de_aaaa_mm_dd_es_rechazada(validador, fecha):

    datos = datos_validos(fecha=fecha)

    errores = validador.validar(**datos)

    assert campos_con_error(errores) == ["fecha"]
    assert "AAAA-MM-DD" in errores[0].mensaje


@pytest.mark.parametrize(
    "fecha",
    ["2026-02-30", "2026-02-29", "2026-13-01", "2026-00-10"],
    ids=["30_de_febrero", "29_feb_año_no_bisiesto", "mes_13", "mes_0"],
)
def test_fecha_con_formato_correcto_pero_inexistente_es_rechazada(validador, fecha):

    datos = datos_validos(fecha=fecha)

    errores = validador.validar(**datos)

    assert campos_con_error(errores) == ["fecha"]
    assert "no existe" in errores[0].mensaje


def test_29_de_febrero_de_un_año_bisiesto_es_aceptado(validador):

    datos = datos_validos(fecha="2024-02-29")

    errores = validador.validar(**datos)
  
    assert errores == []


# ---------- Lugar y observador: partición ----------

@pytest.mark.parametrize("campo", ["lugar", "observador"])
@pytest.mark.parametrize("valor", ["", "   "], ids=["vacio", "solo_espacios"])
def test_lugar_u_observador_vacio_es_rechazado(validador, campo, valor):

    datos = datos_validos(**{campo: valor})

    errores = validador.validar(**datos)

    assert campos_con_error(errores) == [campo]


# ---------- Mensajes y varios errores ----------

def test_el_mensaje_de_error_nombra_el_campo_que_fallo(validador):
  
    datos = datos_validos(especie="ab")
   
    errores = validador.validar(**datos)
  
    assert errores[0].campo == "especie"
    assert "entre 3 y 50" in errores[0].mensaje


def test_con_varios_campos_invalidos_se_reportan_todos(validador):

    datos = datos_validos(especie="ab", lugar="", fecha="2026-10-22", observador=" ")

    errores = validador.validar(**datos)

    assert campos_con_error(errores) == ["especie", "lugar", "fecha", "observador"]