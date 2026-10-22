import os

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from repositorio import RepositorioSQLite
from servicio import AvistamientoInvalido, AvistamientoNoEncontrado, ServicioAvistamientos
from validador import RelojSistema, ValidadorDeAvistamiento


class AvistamientoIn(BaseModel):
  

    model_config = ConfigDict(str_strip_whitespace=True)

    especie: str = Field(examples=["colibrí"])
    lugar: str = Field(examples=["Parque Simón Bolívar"])
    fecha: str = Field(examples=["2026-10-01"])
    observador: str = Field(examples=["Sebastián"])


class AvistamientoOut(AvistamientoIn):
    id: int


def crear_app(repositorio=None, reloj=None) -> FastAPI:
    """Fábrica de la app. Las dependencias se pueden inyectar (útil para pruebas)."""
    repositorio = repositorio or RepositorioSQLite(os.environ.get("AVISTAMIENTOS_DB", "avistamientos.db"))
    reloj = reloj or RelojSistema()
    servicio = ServicioAvistamientos(repositorio, ValidadorDeAvistamiento(reloj))

    app = FastAPI(title="API de avistamientos de aves")

    @app.exception_handler(RequestValidationError)
    async def forma_invalida(request: Request, exc: RequestValidationError):

        errores = exc.errors()
        if errores and errores[0]["loc"][0] == "path":
            return JSONResponse(status_code=404, content={"detail": "Avistamiento no encontrado"})
        detalle = [
            {"campo": ".".join(str(p) for p in e["loc"][1:]), "error": e["msg"]} for e in errores
        ]
        return JSONResponse(
            status_code=400, content={"detail": "Datos inválidos o incompletos", "errores": detalle}
        )

    @app.exception_handler(AvistamientoInvalido)
    async def regla_incumplida(request: Request, exc: AvistamientoInvalido):
        detalle = [{"campo": e.campo, "error": e.mensaje} for e in exc.errores]
        return JSONResponse(status_code=400, content={"detail": "Datos inválidos", "errores": detalle})

    @app.exception_handler(AvistamientoNoEncontrado)
    async def no_encontrado(request: Request, exc: AvistamientoNoEncontrado):
        return JSONResponse(status_code=404, content={"detail": "Avistamiento no encontrado"})

    @app.get("/avistamientos", response_model=list[AvistamientoOut])
    def listar():
        return servicio.listar()

  
    @app.get("/avistamientos/resumen")
    def resumen():
        return servicio.resumen()

    @app.get("/avistamientos/{id}", response_model=AvistamientoOut)
    def obtener(id: int):
        return servicio.obtener(id)

    @app.post("/avistamientos", response_model=AvistamientoOut, status_code=201)
    def crear(datos: AvistamientoIn):
        return servicio.crear(datos.model_dump())

    @app.put("/avistamientos/{id}", response_model=AvistamientoOut)
    def actualizar(id: int, datos: AvistamientoIn):
        return servicio.actualizar(id, datos.model_dump())

    @app.delete("/avistamientos/{id}", status_code=204)
    def eliminar(id: int):
        servicio.eliminar(id)
        return Response(status_code=204)

    return app


app = crear_app()