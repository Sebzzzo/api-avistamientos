"""Acceso a datos: todo el SQL vive aquí."""
import sqlite3
from contextlib import contextmanager


class RepositorioSQLite:
    def __init__(self, ruta: str = "avistamientos.db"):
        self._ruta = ruta
        self._tabla_lista = False

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self._ruta)
        conn.row_factory = sqlite3.Row
        try:
            if not self._tabla_lista:
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
                self._tabla_lista = True
            yield conn
            conn.commit()
        finally:
            conn.close()

    def listar(self) -> list[dict]:
        with self._conn() as conn:
            filas = conn.execute("SELECT * FROM avistamientos ORDER BY id").fetchall()
        return [dict(f) for f in filas]

    def obtener(self, id: int) -> dict | None:
        with self._conn() as conn:
            fila = conn.execute("SELECT * FROM avistamientos WHERE id = ?", (id,)).fetchone()
        return dict(fila) if fila else None

    def crear(self, datos: dict) -> dict:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO avistamientos (especie, lugar, fecha, observador) VALUES (?, ?, ?, ?)",
                (datos["especie"], datos["lugar"], datos["fecha"], datos["observador"]),
            )
            nuevo_id = cur.lastrowid
        return {"id": nuevo_id, **datos}

    def actualizar(self, id: int, datos: dict) -> dict | None:
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE avistamientos SET especie = ?, lugar = ?, fecha = ?, observador = ? WHERE id = ?",
                (datos["especie"], datos["lugar"], datos["fecha"], datos["observador"], id),
            )
            if cur.rowcount == 0:
                return None
        return {"id": id, **datos}

    def eliminar(self, id: int) -> bool:
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM avistamientos WHERE id = ?", (id,))
            return cur.rowcount > 0

    def resumen(self) -> list[dict]:
        with self._conn() as conn:
            filas = conn.execute(
                """
                SELECT especie, COUNT(*) AS total
                FROM avistamientos
                GROUP BY especie
                ORDER BY total DESC, especie
                """
            ).fetchall()
        return [dict(f) for f in filas]