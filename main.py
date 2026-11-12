import os

from fastapi import FastAPI

from adaptadores.entrada.api_http import crear_app_http
from adaptadores.salida.reloj_sistema import RelojSistema
from adaptadores.salida.repositorio_sqlite import RepositorioSQLite
from aplicacion.servicio import ServicioAvistamientos
from dominio.validador import ValidadorDeAvistamiento


def crear_app(repositorio=None, reloj=None) -> FastAPI:
    repositorio = repositorio or RepositorioSQLite(os.environ.get("AVISTAMIENTOS_DB", "avistamientos.db"))
    reloj = reloj or RelojSistema()
    servicio = ServicioAvistamientos(repositorio, ValidadorDeAvistamiento(reloj))
    return crear_app_http(servicio)


app = crear_app()