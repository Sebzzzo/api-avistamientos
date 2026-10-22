"""API REST de avistamientos de aves (FastAPI + SQLite)."""
import os
import re
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator


def db_path() -> str:
    # Se lee en cada uso para poder cambiarla en las pruebas.
    return os.environ.get("AVISTAMIENTOS_DB", "avistamientos.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS avistamientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                especie TEXT NOT NULL,
                lugar TEXT NOT NULL,
                fecha TEXT NOT NULL,
                observador TEXT NOT NULL
            )
            """
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="API de avistamientos de aves", lifespan=lifespan)


class AvistamientoIn(BaseModel):
    """Datos que envía el cliente (el id lo asigna el sistema)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    especie: str = Field(min_length=1, examples=["colibrí"])
    lugar: str = Field(min_length=1, examples=["Parque Simón Bolívar"])
    fecha: str = Field(examples=["2026-09-29"])
    observador: str = Field(min_length=1, examples=["Sebastián"])

    @field_validator("fecha")
    @classmethod
    def fecha_valida(cls, v: str) -> str:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError("La fecha debe tener el formato AAAA-MM-DD")
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("La fecha no es válida")
        return v


class AvistamientoOut(AvistamientoIn):
    id: int


@app.exception_handler(RequestValidationError)
async def validacion_handler(request: Request, exc: RequestValidationError):
    # FastAPI responde 422 por defecto; el enunciado pide 400 si faltan datos.
    # Un id inválido en la URL (p. ej. /avistamientos/abc) no existe: 404.
    errores = exc.errors()
    if errores and errores[0]["loc"][0] == "path":
        return JSONResponse(status_code=404, content={"detail": "Avistamiento no encontrado"})
    detalle = [
        {"campo": ".".join(str(p) for p in e["loc"][1:]), "error": e["msg"]}
        for e in errores
    ]
    return JSONResponse(
        status_code=400,
        content={"detail": "Datos inválidos o incompletos", "errores": detalle},
    )


def no_encontrado() -> HTTPException:
    return HTTPException(status_code=404, detail="Avistamiento no encontrado")


@app.get("/avistamientos", response_model=list[AvistamientoOut])
def listar():
    with get_conn() as conn:
        filas = conn.execute("SELECT * FROM avistamientos ORDER BY id").fetchall()
    return [dict(f) for f in filas]


# Importante: /resumen va ANTES de /{id}, si no "resumen" se interpretaría como un id.
@app.get("/avistamientos/resumen")
def resumen():
    with get_conn() as conn:
        filas = conn.execute(
            """
            SELECT especie, COUNT(*) AS total
            FROM avistamientos
            GROUP BY especie
            ORDER BY total DESC, especie
            """
        ).fetchall()
    return [dict(f) for f in filas]


@app.get("/avistamientos/{id}", response_model=AvistamientoOut)
def obtener(id: int):
    with get_conn() as conn:
        fila = conn.execute("SELECT * FROM avistamientos WHERE id = ?", (id,)).fetchone()
    if fila is None:
        raise no_encontrado()
    return dict(fila)


@app.post("/avistamientos", response_model=AvistamientoOut, status_code=201)
def crear(datos: AvistamientoIn):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO avistamientos (especie, lugar, fecha, observador) VALUES (?, ?, ?, ?)",
            (datos.especie, datos.lugar, datos.fecha, datos.observador),
        )
        nuevo_id = cur.lastrowid
    return {"id": nuevo_id, **datos.model_dump()}


@app.put("/avistamientos/{id}", response_model=AvistamientoOut)
def actualizar(id: int, datos: AvistamientoIn):
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE avistamientos SET especie = ?, lugar = ?, fecha = ?, observador = ? WHERE id = ?",
            (datos.especie, datos.lugar, datos.fecha, datos.observador, id),
        )
        if cur.rowcount == 0:
            raise no_encontrado()
    return {"id": id, **datos.model_dump()}


@app.delete("/avistamientos/{id}", status_code=204)
def eliminar(id: int):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM avistamientos WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise no_encontrado()
    return Response(status_code=204)
