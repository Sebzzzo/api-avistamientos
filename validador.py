import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

ESPECIE_MIN = 3
ESPECIE_MAX = 50
_PATRON_FECHA = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class Reloj(Protocol):

    def hoy(self) -> date: ...


class RelojSistema:

    def hoy(self) -> date:
        return date.today()


@dataclass(frozen=True)
class ErrorDeCampo:
    campo: str
    mensaje: str


class ValidadorDeAvistamiento:
    def __init__(self, reloj: Reloj):
        self._reloj = reloj

    def validar(self, especie: str, lugar: str, fecha: str, observador: str) -> list[ErrorDeCampo]:
        errores: list[ErrorDeCampo] = []
        errores += self._validar_especie(especie)
        errores += self._validar_no_vacio("lugar", lugar)
        errores += self._validar_fecha(fecha)
        errores += self._validar_no_vacio("observador", observador)
        return errores

    def _validar_especie(self, especie: str) -> list[ErrorDeCampo]:
        largo = len(especie.strip())
        if ESPECIE_MIN <= largo <= ESPECIE_MAX:
            return []
        return [
            ErrorDeCampo(
                "especie",
                f"La especie debe tener entre {ESPECIE_MIN} y {ESPECIE_MAX} caracteres (tiene {largo})",
            )
        ]

    def _validar_no_vacio(self, campo: str, valor: str) -> list[ErrorDeCampo]:
        if valor.strip():
            return []
        return [ErrorDeCampo(campo, f"El campo {campo} no puede estar vacío")]

    def _validar_fecha(self, fecha: str) -> list[ErrorDeCampo]:
        if not _PATRON_FECHA.fullmatch(fecha):
            return [ErrorDeCampo("fecha", "La fecha debe tener el formato AAAA-MM-DD")]
        try:
            valor = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            return [ErrorDeCampo("fecha", "La fecha no existe en el calendario")]
        if valor > self._reloj.hoy():
            return [ErrorDeCampo("fecha", "La fecha no puede ser posterior a hoy")]
        return []
