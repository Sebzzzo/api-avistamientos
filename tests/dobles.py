"""Dobles de prueba compartidos."""
from collections import Counter
from datetime import date


class RelojFijo:
    """STUB: devuelve siempre la misma fecha, para que las pruebas no dependan del día real."""

    def __init__(self, fecha: date):
        self._fecha = fecha

    def hoy(self) -> date:
        return self._fecha


class RepositorioEnMemoria:
    """FAKE: implementación funcional del repositorio, pero con un diccionario en vez de SQLite."""

    def __init__(self):
        self._filas: dict[int, dict] = {}
        self._siguiente_id = 1

    def listar(self):
        return [dict(f) for f in self._filas.values()]

    def obtener(self, id):
        fila = self._filas.get(id)
        return dict(fila) if fila else None

    def crear(self, datos):
        fila = {"id": self._siguiente_id, **datos}
        self._filas[fila["id"]] = fila
        self._siguiente_id += 1
        return dict(fila)

    def actualizar(self, id, datos):
        if id not in self._filas:
            return None
        self._filas[id] = {"id": id, **datos}
        return dict(self._filas[id])

    def eliminar(self, id):
        return self._filas.pop(id, None) is not None

    def resumen(self):
        conteo = Counter(f["especie"] for f in self._filas.values())
        return [{"especie": e, "total": t} for e, t in sorted(conteo.items(), key=lambda x: (-x[1], x[0]))]