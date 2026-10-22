"""Pruebas UNITARIAS de ServicioAvistamientos con dobles del repositorio.

- RepositorioEnMemoria = FAKE  (verificamos el ESTADO resultante)
- Mock(spec=...)       = MOCK  (verificamos una INTERACCIÓN: qué NO se llamó)
- RelojFijo            = STUB  (fecha enlatada para el validador)
"""
from datetime import date
from unittest.mock import Mock

import pytest

from repositorio import RepositorioSQLite
from servicio import AvistamientoInvalido, AvistamientoNoEncontrado, ServicioAvistamientos
from tests.dobles import RelojFijo, RepositorioEnMemoria
from validador import ValidadorDeAvistamiento

VALIDO = {
    "especie": "colibrí",
    "lugar": "Parque Simón Bolívar",
    "fecha": "2026-10-01",
    "observador": "Sebastián",
}


def armar_servicio(repositorio):
    return ServicioAvistamientos(repositorio, ValidadorDeAvistamiento(RelojFijo(date(2026, 10, 21))))


@pytest.fixture
def repo():
    return RepositorioEnMemoria()


@pytest.fixture
def servicio(repo):
    return armar_servicio(repo)


def test_crear_con_datos_validos_guarda_y_devuelve_el_avistamiento_con_id(servicio, repo):
    # Arrange
    datos = dict(VALIDO)
    # Act
    creado = servicio.crear(datos)
    # Assert
    assert creado == {"id": 1, **VALIDO}
    assert repo.obtener(1) == creado


def test_crear_con_datos_invalidos_lanza_error_con_el_campo_y_no_guarda(servicio, repo):
    # Arrange
    datos = {**VALIDO, "especie": "ab"}
    # Act
    with pytest.raises(AvistamientoInvalido) as error:
        servicio.crear(datos)
    # Assert
    assert [e.campo for e in error.value.errores] == ["especie"]
    assert repo.listar() == []


def test_crear_con_datos_invalidos_nunca_llama_al_repositorio():
    # Arrange: MOCK del repositorio para verificar la interacción
    repo_mock = Mock(spec=RepositorioSQLite)
    servicio = armar_servicio(repo_mock)
    # Act
    with pytest.raises(AvistamientoInvalido):
        servicio.crear({**VALIDO, "fecha": "2026-10-22"})  # mañana
    # Assert
    repo_mock.crear.assert_not_called()


def test_crear_con_datos_validos_llama_al_repositorio_una_sola_vez():
    # Arrange
    repo_mock = Mock(spec=RepositorioSQLite)
    repo_mock.crear.return_value = {"id": 7, **VALIDO}
    servicio = armar_servicio(repo_mock)
    # Act
    creado = servicio.crear(dict(VALIDO))
    # Assert
    repo_mock.crear.assert_called_once_with(VALIDO)
    assert creado["id"] == 7


def test_obtener_un_id_inexistente_lanza_no_encontrado(servicio):
    # Arrange: repositorio vacío
    # Act / Assert
    with pytest.raises(AvistamientoNoEncontrado):
        servicio.obtener(999)


def test_actualizar_un_avistamiento_existente_cambia_sus_datos(servicio, repo):
    # Arrange
    id_ = servicio.crear(dict(VALIDO))["id"]
    # Act
    actualizado = servicio.actualizar(id_, {**VALIDO, "lugar": "Humedal Córdoba"})
    # Assert
    assert actualizado["lugar"] == "Humedal Córdoba"
    assert repo.obtener(id_)["lugar"] == "Humedal Córdoba"


def test_actualizar_con_datos_invalidos_lanza_error_y_no_modifica_el_original(servicio, repo):
    # Arrange
    id_ = servicio.crear(dict(VALIDO))["id"]
    # Act
    with pytest.raises(AvistamientoInvalido):
        servicio.actualizar(id_, {**VALIDO, "observador": ""})
    # Assert
    assert repo.obtener(id_) == {"id": id_, **VALIDO}


def test_actualizar_un_id_inexistente_lanza_no_encontrado(servicio):
    # Arrange: repositorio vacío
    # Act / Assert
    with pytest.raises(AvistamientoNoEncontrado):
        servicio.actualizar(999, dict(VALIDO))


def test_eliminar_un_avistamiento_existente_lo_quita_del_repositorio(servicio, repo):
    # Arrange
    id_ = servicio.crear(dict(VALIDO))["id"]
    # Act
    servicio.eliminar(id_)
    # Assert
    assert repo.obtener(id_) is None


def test_eliminar_un_id_inexistente_lanza_no_encontrado(servicio):
    # Arrange: repositorio vacío
    # Act / Assert
    with pytest.raises(AvistamientoNoEncontrado):
        servicio.eliminar(999)