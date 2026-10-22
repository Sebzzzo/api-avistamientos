"""Capa de servicio: coordina validador y repositorio (sin saber nada de HTTP)."""
from validador import ErrorDeCampo, ValidadorDeAvistamiento


class AvistamientoInvalido(Exception):
    def __init__(self, errores: list[ErrorDeCampo]):
        super().__init__("Datos inválidos")
        self.errores = errores


class AvistamientoNoEncontrado(Exception):
    pass


class ServicioAvistamientos:
    def __init__(self, repositorio, validador: ValidadorDeAvistamiento):
        self._repo = repositorio
        self._validador = validador

    def _validar(self, datos: dict) -> None:
        errores = self._validador.validar(
            datos["especie"], datos["lugar"], datos["fecha"], datos["observador"]
        )
        if errores:
            raise AvistamientoInvalido(errores)

    def listar(self) -> list[dict]:
        return self._repo.listar()

    def resumen(self) -> list[dict]:
        return self._repo.resumen()

    def obtener(self, id: int) -> dict:
        avistamiento = self._repo.obtener(id)
        if avistamiento is None:
            raise AvistamientoNoEncontrado()
        return avistamiento

    def crear(self, datos: dict) -> dict:
        self._validar(datos)
        return self._repo.crear(datos)

    def actualizar(self, id: int, datos: dict) -> dict:
        # Se valida primero: un cuerpo inválido es 400 aunque el id no exista.
        self._validar(datos)
        actualizado = self._repo.actualizar(id, datos)
        if actualizado is None:
            raise AvistamientoNoEncontrado()
        return actualizado

    def eliminar(self, id: int) -> None:
        if not self._repo.eliminar(id):
            raise AvistamientoNoEncontrado()