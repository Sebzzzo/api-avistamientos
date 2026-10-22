# API REST de avistamientos de aves

Trabajo en clase de Ingeniería de Software 2 (ISW-2), sesión 17.
API REST pequeña para registrar avistamientos de aves, hecha con **Python + FastAPI + SQLite** (módulo `sqlite3` de la biblioteca estándar). Recibe y responde JSON.

## Uso de IA

Se usó **Claude (Anthropic), modelo Sonnet 5.5**, como asistente para generar y revisar el código. Revisé y entiendo el código publicado.

## Requisitos

- Python 3.10 o superior
- pip

## Instalación y ejecución

```bash
git clone <URL-DEL-REPOSITORIO>
cd <carpeta-del-repositorio>

python -m venv .venv
```

Activar el entorno virtual:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (cmd): `.venv\Scripts\activate.bat`
- Linux / macOS: `source .venv/bin/activate`

Instalar dependencias y levantar la API:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

La API queda en `http://127.0.0.1:8000`. La base de datos `avistamientos.db` (SQLite) se crea sola en la primera ejecución.

Documentación interactiva (Swagger), útil para probar sin curl: `http://127.0.0.1:8000/docs`

## Modelo

| Campo        | Tipo   | Descripción                                   |
|--------------|--------|-----------------------------------------------|
| `id`         | entero | Lo asigna el sistema                          |
| `especie`    | texto  | Nombre de la especie (ej. "colibrí")          |
| `lugar`      | texto  | Dónde se observó                              |
| `fecha`      | texto  | Formato `AAAA-MM-DD`                          |
| `observador` | texto  | Quién la registró                             |

## Endpoints

| Operación                   | Petición                    | Respuestas                               |
|-----------------------------|-----------------------------|------------------------------------------|
| Listar                      | `GET /avistamientos`        | 200                                      |
| Ver uno                     | `GET /avistamientos/{id}`   | 200 / 404                                |
| Registrar                   | `POST /avistamientos`       | 201 / 400 (faltan o son inválidos datos) |
| Actualizar                  | `PUT /avistamientos/{id}`   | 200 / 400 / 404                          |
| Eliminar                    | `DELETE /avistamientos/{id}`| 204 / 404                                |
| Resumen por especie (bonus) | `GET /avistamientos/resumen`| 200                                      |

### Ejemplos con curl

> En Windows PowerShell, `curl` es un alias de otro comando: usa `curl.exe` y, para el JSON, comillas dobles escapadas (`"{\"especie\":\"colibrí\"}"`), o prueba desde `/docs`. En cmd, Git Bash, Linux y macOS los ejemplos funcionan tal cual (en cmd cambia las comillas simples por dobles escapadas).

**Listar**

```bash
curl -i http://127.0.0.1:8000/avistamientos
```

**Ver uno**

```bash
curl -i http://127.0.0.1:8000/avistamientos/1
```

**Registrar**

```bash
curl -i -X POST http://127.0.0.1:8000/avistamientos \
  -H "Content-Type: application/json" \
  -d '{"especie":"colibrí","lugar":"Parque Simón Bolívar","fecha":"2026-09-29","observador":"Sebastián"}'
```

**Actualizar** (envía todos los campos)

```bash
curl -i -X PUT http://127.0.0.1:8000/avistamientos/1 \
  -H "Content-Type: application/json" \
  -d '{"especie":"colibrí","lugar":"Humedal Córdoba","fecha":"2026-09-29","observador":"Sebastián"}'
```

**Eliminar**

```bash
curl -i -X DELETE http://127.0.0.1:8000/avistamientos/1
```

**Resumen por especie**

```bash
curl -i http://127.0.0.1:8000/avistamientos/resumen
```

Respuesta de ejemplo: `[{"especie":"colibrí","total":2},{"especie":"tucán","total":1}]`

## Códigos de estado

- `200` operación correcta (listar, ver, actualizar, resumen)
- `201` avistamiento creado
- `204` avistamiento eliminado (sin cuerpo)
- `400` faltan datos, hay datos inválidos (por ejemplo, fecha que no cumple `AAAA-MM-DD`) o el JSON está mal formado
- `404` el avistamiento no existe

## Pruebas

```bash
pytest
```

Las pruebas usan una base de datos temporal, no tocan `avistamientos.db`.
