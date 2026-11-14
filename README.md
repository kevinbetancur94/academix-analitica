# Academix · Analítica de datos

Taller de visualización de datos del ecosistema **Academix**. Lee las tareas y calificaciones desde la API (Spring Boot), las analiza con **pandas**, genera **15 gráficas** con **matplotlib** y arma un **reporte HTML autocontenido** que se publica en el front React (ruta `/reportes`, visible para docentes).

Cada pregunta sigue la fórmula del taller: **pregunta → cálculo → visualización → interpretación**.

## Ecosistema Academix

| Repositorio | Qué es | Tecnología |
|---|---|---|
| [`academix-analitica`](https://github.com/kevinbetancur94/academix-analitica) (este) | Análisis y reporte | Python + pandas + matplotlib |
| [`proyecto-academix`](https://github.com/kevinbetancur94/proyecto-academix) | API REST que provee los datos | Spring Boot + PostgreSQL |
| [`Academix-Front-Final`](https://github.com/kevinbetancur94/Academix-Front-Final) | Interfaz web que muestra el reporte | React + Vite |

```
API Spring Boot ──GET /api/tareas, /api/calificaciones──▶ generar_reporte.py
                                                           │  ejecuta taller_academix.ipynb (gráficas)
                                                           ▼
                           reporte/index.html ──(--front)──▶ Academix-Front-Final/public/reportes/
```

## Equipo

| Integrante |
|---|
| Kevin Betancur ([@kevinbetancur94](https://github.com/kevinbetancur94)) |
| Nataly Quintero |
| Karen Urrutia |
| Alex Chavarriaga |

Proyecto del **CESDE** (Medellín, Colombia) · Visualización de datos · Docente: Gustavo Montoya Escobar.

## Tecnologías y versiones

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.14 (versión del kernel con que se ejecutó el notebook). Probado también con 3.12 | Lenguaje |
| pandas | sin fijar en `requirements.txt` · probado con 3.0.6 | Carga, limpieza y agregaciones |
| NumPy | dependencia de pandas · probado con 2.5.4 | Cálculos y tendencia (`polyfit`) |
| matplotlib | sin fijar · probado con 3.11.2 | Gráficas PNG |
| requests | sin fijar · probado con 2.34.2 | Llamadas a la API |
| ipykernel, nbformat, nbclient | sin fijar | Ejecutar el notebook desde `generar_reporte.py` |
| Jupyter (VS Code o JupyterLab) | — | Para abrir y ejecutar `taller_academix.ipynb` |
| HTML + CSS | — | Reporte autocontenido (`plantilla.css`, gráficas incrustadas en base64) |

## Estructura del proyecto

```
academix-analitica/
├── generar_reporte.py        Orquesta todo: datos → notebook → métricas → HTML → (front)
├── taller_academix.ipynb     Notebook con las 15 preguntas (se ejecuta con "Run All")
├── plantilla.css             Estilos del reporte HTML
├── requirements.txt          Dependencias de Python
├── datos/
│   ├── tareas.csv            Datos de respaldo (420 tareas)
│   └── calificaciones.csv    Datos de respaldo (320 registros de notas)
├── graficas/                 15 PNG generados por el notebook (p01_…, p02_…, …)
└── reporte/index.html        Reporte final (≈ 1 MB, todo incrustado)
```

## Datos

Los datos salen de dos recursos de la API:

| Recurso | Endpoint | Columnas que se usan |
|---|---|---|
| Tareas | `GET /api/tareas` | `materiaNombre`, `tipo`, `grado`, `fecha` (fecha de entrega), `estadoActivo` |
| Calificaciones | `GET /api/calificaciones` | `materiaNombre`, `estudianteNombre`, `act1`, `act2`, `act3`, `promedio` |

**Fuente `api` (por defecto):** lee la API. Si no responde, devuelve error o llega vacía, el script avisa y usa los CSV de `datos/`.
**Fuente `csv`:** usa solo los CSV de ejemplo (datos simulados: ocho materias, de febrero a noviembre de 2026). Sirven para trabajar sin backend, pero **no coinciden con lo que hay en la base de datos real**.

El estado de una tarea se deriva: `Inactiva` si `estadoActivo` es falso, `Fecha cumplida` si su fecha ya pasó, `Por entregar` en otro caso. Se calcula contra **la fecha de hoy**, así que el reporte cambia con el tiempo aunque los datos no cambien. "Fecha cumplida" significa que la fecha pasó, no que el estudiante haya entregado.

## Preguntas analizadas

| Bloque | Preguntas | Gráfica |
|---|---|---|
| 01 · Tendencias en el tiempo | P1 Tareas por mes · P2 Entregas por día de la semana · P3 Mes actual vs. anterior | `p01`, `p02`, `p03` |
| 02 · Participación y composición | P7 Participación por materia · P8 Estado de las tareas | `p07`, `p08` |
| 03 · Promedios | P13 Nota promedio por materia | `p13` |
| 04 · Máximos, mínimos y rankings | P18 Top 5 con más tareas · P19 Las 3 con menos · P20 Mes máximo y mínimo | `p18`, `p19`, `p20` |
| 08 · Comparaciones | P39 Entre semana vs. fin de semana · P40 Evolución del top 3 | `p39`, `p40` |
| 09 · Reporte final | P44 Situación general · P45 Tres hallazgos · P46 Materia que requiere atención · P47 Decisión a partir de los datos | `p44`, `p45`, `p46`, `p47` |

La **materia que requiere atención** (P46) se elige por alertas: total de tareas por encima de la media, tareas por entregar por encima de la media y nota promedio por debajo de la media; el empate se resuelve por tareas por entregar.

## Cómo usarlo

### 1. Instalar

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Generar el reporte

```bash
# a) API local (backend encendido en localhost:8080; si no responde, usa los CSV)
python generar_reporte.py

# b) API desplegada en Render
python generar_reporte.py --api https://proyecto-academix.onrender.com/api

# c) Solo los CSV de ejemplo
python generar_reporte.py --fuente csv

# d) Generar y publicar en el front en un solo paso
python generar_reporte.py --api https://proyecto-academix.onrender.com/api --front "RUTA/A/Academix-Front-Final"
```

| Opción | Valor por defecto | Qué hace |
|---|---|---|
| `--fuente` | `api` | `api` (con respaldo a CSV) o `csv` |
| `--api` | `http://localhost:8080/api` | URL base de la API |
| `--salida` | `reporte` | Carpeta donde se escribe `index.html` |
| `--front` | — | Raíz del front React; copia el reporte a `public/reportes/index.html` |
| `--sin-notebook` | — | No vuelve a ejecutar el notebook: reutiliza las gráficas existentes de `graficas/` |

El script ejecuta el notebook con la misma fuente de datos, regenera las gráficas, calcula las métricas y escribe `reporte/index.html`.

> **Revisa siempre la línea `Fuente:` del encabezado del reporte.** Debe decir `API Academix (…)`. Si dice `CSV de ejemplo`, la API no respondió y se usaron datos simulados. Con la API en Render, la primera petición puede tardar hasta un minuto (el script espera hasta 90 s por recurso).

### 3. Actualizar el reporte del front

El front muestra `public/reportes/index.html`. Cuando cambien los datos (o la fecha de corte), vuelve a correr el comando **d)** y haz commit del archivo actualizado en `Academix-Front-Final`.

### 4. Ejecutar el notebook a mano

Abre `taller_academix.ipynb` y usa **Run All**. En la primera celda de código puedes fijar la fuente con las variables de entorno `ACADEMIX_FUENTE` (`api` o `csv`) y `ACADEMIX_API` (URL base). También se puede fijar la fecha de corte descomentando la línea `HOY = pd.Timestamp("2026-10-30")` para repetir resultados.

## Resultado

- `graficas/`: 15 imágenes `pNN_nombre.png`.
- `reporte/index.html`: encabezado con periodo, fuente y fecha de generación; tarjetas con indicadores (tareas totales, por entregar, nota promedio, materia principal); y una sección por bloque con gráfica, **Hallazgo** e **Interpretación** por pregunta. No depende de archivos externos.
