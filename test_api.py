import pytest
from fastapi.testclient import TestClient

VALIDO = {
    "especie": "colibrí",
    "lugar": "Parque Simón Bolívar",
    "fecha": "2026-09-29",
    "observador": "Sebastián",
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AVISTAMIENTOS_DB", str(tmp_path / "test.db"))
    from main import app

    with TestClient(app) as c:  # el "with" ejecuta el lifespan (crea la tabla)
        yield c


def test_listar_vacio(client):
    r = client.get("/avistamientos")
    assert r.status_code == 200
    assert r.json() == []


def test_crear_y_obtener(client):
    r = client.post("/avistamientos", json=VALIDO)
    assert r.status_code == 201
    creado = r.json()
    assert creado["id"] == 1
    assert creado["especie"] == "colibrí"

    r = client.get(f"/avistamientos/{creado['id']}")
    assert r.status_code == 200
    assert r.json() == creado


def test_crear_faltan_datos_400(client):
    r = client.post("/avistamientos", json={"especie": "colibrí"})
    assert r.status_code == 400


def test_crear_fecha_invalida_400(client):
    r = client.post("/avistamientos", json={**VALIDO, "fecha": "29/09/2026"})
    assert r.status_code == 400
    r = client.post("/avistamientos", json={**VALIDO, "fecha": "2026-13-45"})
    assert r.status_code == 400


def test_crear_json_malformado_400(client):
    r = client.post(
        "/avistamientos", content="{no es json", headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 400


def test_obtener_inexistente_404(client):
    assert client.get("/avistamientos/999").status_code == 404


def test_actualizar(client):
    id_ = client.post("/avistamientos", json=VALIDO).json()["id"]
    r = client.put(f"/avistamientos/{id_}", json={**VALIDO, "lugar": "Humedal Córdoba"})
    assert r.status_code == 200
    assert r.json()["lugar"] == "Humedal Córdoba"
    assert client.get(f"/avistamientos/{id_}").json()["lugar"] == "Humedal Córdoba"


def test_actualizar_inexistente_404(client):
    assert client.put("/avistamientos/999", json=VALIDO).status_code == 404


def test_actualizar_datos_invalidos_400(client):
    id_ = client.post("/avistamientos", json=VALIDO).json()["id"]
    assert client.put(f"/avistamientos/{id_}", json={"lugar": "x"}).status_code == 400


def test_eliminar(client):
    id_ = client.post("/avistamientos", json=VALIDO).json()["id"]
    assert client.delete(f"/avistamientos/{id_}").status_code == 204
    assert client.get(f"/avistamientos/{id_}").status_code == 404


def test_eliminar_inexistente_404(client):
    assert client.delete("/avistamientos/999").status_code == 404


def test_resumen_por_especie(client):
    client.post("/avistamientos", json=VALIDO)
    client.post("/avistamientos", json=VALIDO)
    client.post("/avistamientos", json={**VALIDO, "especie": "tucán"})
    r = client.get("/avistamientos/resumen")
    assert r.status_code == 200
    assert r.json() == [
        {"especie": "colibrí", "total": 2},
        {"especie": "tucán", "total": 1},
    ]
