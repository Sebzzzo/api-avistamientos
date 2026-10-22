"""Pruebas de INTEGRACIÓN: la API completa por HTTP, con SQLite real.

- Cada prueba recibe su propia base de datos temporal (fixture `client`): son independientes.
- El reloj es un STUB (RelojFijo): "hoy" siempre es 2026-10-21, sin depender de la fecha real.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from main import crear_app
from repositorio import RepositorioSQLite
from tests.dobles import RelojFijo

VALIDO = {
    "especie": "colibrí",
    "lugar": "Parque Simón Bolívar",
    "fecha": "2026-10-01",
    "observador": "Sebastián",
}


@pytest.fixture
def client(tmp_path):
    repo = RepositorioSQLite(str(tmp_path / "test.db"))  # base nueva y vacía por prueba
    app = crear_app(repositorio=repo, reloj=RelojFijo(date(2026, 10, 21)))
    return TestClient(app)


def registrar(client, **cambios):
    """Prepara datos: crea un avistamiento por la API y devuelve el JSON creado."""
    respuesta = client.post("/avistamientos", json={**VALIDO, **cambios})
    assert respuesta.status_code == 201
    return respuesta.json()


def campos_del_error(respuesta):
    return [e["campo"] for e in respuesta.json()["errores"]]


# ---------- GET /avistamientos ----------

def test_listar_sin_datos_responde_200_y_lista_vacia(client):
    # Arrange: base vacía
    # Act
    r = client.get("/avistamientos")
    # Assert
    assert r.status_code == 200
    assert r.json() == []


def test_listar_devuelve_todos_los_avistamientos_en_orden_de_registro(client):
    # Arrange
    a = registrar(client, especie="colibrí")
    b = registrar(client, especie="tucán")
    # Act
    r = client.get("/avistamientos")
    # Assert
    assert r.status_code == 200
    assert r.json() == [a, b]


# ---------- GET /avistamientos/{id} ----------

def test_obtener_existente_responde_200_con_todos_los_campos(client):
    # Arrange
    creado = registrar(client)
    # Act
    r = client.get(f"/avistamientos/{creado['id']}")
    # Assert
    assert r.status_code == 200
    assert r.json() == {"id": creado["id"], **VALIDO}


def test_obtener_inexistente_responde_404_con_mensaje(client):
    # Arrange: base vacía
    # Act
    r = client.get("/avistamientos/999")
    # Assert
    assert r.status_code == 404
    assert r.json() == {"detail": "Avistamiento no encontrado"}


def test_obtener_con_id_que_no_es_numero_responde_404(client):
    # Arrange / Act
    r = client.get("/avistamientos/abc")
    # Assert
    assert r.status_code == 404


# ---------- POST /avistamientos ----------

def test_crear_valido_responde_201_con_id_asignado_y_queda_guardado(client):
    # Arrange
    datos = dict(VALIDO)
    # Act
    r = client.post("/avistamientos", json=datos)
    # Assert (respuesta)
    assert r.status_code == 201
    creado = r.json()
    assert creado == {"id": 1, **VALIDO}
    # Assert (efecto): un GET al nuevo id lo devuelve
    assert client.get(f"/avistamientos/{creado['id']}").json() == creado


def test_crear_con_campos_faltantes_responde_400_y_no_guarda(client):
    # Arrange
    datos = {"especie": "colibrí"}
    # Act
    r = client.post("/avistamientos", json=datos)
    # Assert
    assert r.status_code == 400
    assert set(campos_del_error(r)) == {"lugar", "fecha", "observador"}
    assert client.get("/avistamientos").json() == []


def test_crear_con_especie_muy_corta_responde_400_nombrando_el_campo_y_no_guarda(client):
    # Arrange
    datos = {**VALIDO, "especie": "ab"}
    # Act
    r = client.post("/avistamientos", json=datos)
    # Assert
    assert r.status_code == 400
    assert campos_del_error(r) == ["especie"]
    assert client.get("/avistamientos").json() == []


def test_crear_con_fecha_de_manana_responde_400(client):
    # Arrange: el reloj fijo dice que hoy es 2026-10-21
    datos = {**VALIDO, "fecha": "2026-10-22"}
    # Act
    r = client.post("/avistamientos", json=datos)
    # Assert
    assert r.status_code == 400
    assert campos_del_error(r) == ["fecha"]


def test_crear_con_json_malformado_responde_400(client):
    # Arrange
    cuerpo = "{esto no es json"
    # Act
    r = client.post("/avistamientos", content=cuerpo, headers={"Content-Type": "application/json"})
    # Assert
    assert r.status_code == 400


def test_crear_con_tipo_de_dato_incorrecto_responde_400(client):
    # Arrange
    datos = {**VALIDO, "especie": 12345}
    # Act
    r = client.post("/avistamientos", json=datos)
    # Assert
    assert r.status_code == 400


# ---------- PUT /avistamientos/{id} ----------

def test_actualizar_existente_responde_200_y_el_cambio_persiste(client):
    # Arrange
    id_ = registrar(client)["id"]
    nuevos = {**VALIDO, "lugar": "Humedal Córdoba", "especie": "tucán"}
    # Act
    r = client.put(f"/avistamientos/{id_}", json=nuevos)
    # Assert
    assert r.status_code == 200
    assert r.json() == {"id": id_, **nuevos}
    assert client.get(f"/avistamientos/{id_}").json() == {"id": id_, **nuevos}


def test_actualizar_inexistente_responde_404(client):
    # Arrange: base vacía
    # Act
    r = client.put("/avistamientos/999", json=VALIDO)
    # Assert
    assert r.status_code == 404


def test_actualizar_con_datos_invalidos_responde_400_y_no_modifica_el_original(client):
    # Arrange
    id_ = registrar(client)["id"]
    # Act
    r = client.put(f"/avistamientos/{id_}", json={**VALIDO, "observador": ""})
    # Assert
    assert r.status_code == 400
    assert campos_del_error(r) == ["observador"]
    assert client.get(f"/avistamientos/{id_}").json() == {"id": id_, **VALIDO}


def test_actualizar_con_campos_faltantes_responde_400(client):
    # Arrange
    id_ = registrar(client)["id"]
    # Act
    r = client.put(f"/avistamientos/{id_}", json={"lugar": "x"})
    # Assert
    assert r.status_code == 400


# ---------- DELETE /avistamientos/{id} ----------

def test_eliminar_existente_responde_204_y_luego_el_id_da_404(client):
    # Arrange
    id_ = registrar(client)["id"]
    # Act
    r = client.delete(f"/avistamientos/{id_}")
    # Assert
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/avistamientos/{id_}").status_code == 404


def test_eliminar_borra_solo_el_avistamiento_indicado(client):
    # Arrange
    a = registrar(client, especie="colibrí")
    b = registrar(client, especie="tucán")
    # Act
    client.delete(f"/avistamientos/{a['id']}")
    # Assert
    assert client.get("/avistamientos").json() == [b]


def test_eliminar_inexistente_responde_404(client):
    # Arrange: base vacía
    # Act
    r = client.delete("/avistamientos/999")
    # Assert
    assert r.status_code == 404


# ---------- GET /avistamientos/resumen (bonus) ----------

def test_resumen_cuenta_avistamientos_por_especie(client):
    # Arrange
    registrar(client, especie="colibrí")
    registrar(client, especie="colibrí")
    registrar(client, especie="tucán")
    # Act
    r = client.get("/avistamientos/resumen")
    # Assert
    assert r.status_code == 200
    assert r.json() == [{"especie": "colibrí", "total": 2}, {"especie": "tucán", "total": 1}]


def test_resumen_sin_datos_responde_200_y_lista_vacia(client):
    # Arrange: base vacía
    # Act
    r = client.get("/avistamientos/resumen")
    # Assert
    assert r.status_code == 200
    assert r.json() == []