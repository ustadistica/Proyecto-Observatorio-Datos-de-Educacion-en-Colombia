# Observatorio de Educacion en Colombia

> **Ustadistica** -- Consultoria e Investigacion . Universidad Santo Tomas . 2026-I

Observatorio de datos abiertos de educacion en Colombia. Integracion de SNIES, ICFES y PTE para analisis territorial de brechas educativas.

## Fuentes de Datos

SNIES (matricula, graduados), ICFES (Saber 11, Saber Pro), PTE (presupuesto educativo) -- datos.gov.co

Consultar [`datos/catalogo.yaml`](datos/catalogo.yaml) para los identificadores Socrata y metadatos de cada dataset.

## Preguntas de Investigacion

- Como ha evolucionado la cobertura en educacion superior por departamento entre 2015 y 2024?
- Existe correlacion entre la ejecucion presupuestal del PTE y los puntajes Saber Pro a nivel departamental?
- Que programas academicos muestran mayor crecimiento de matricula y cuales presentan senales de saturacion?
- Cual es la brecha de genero en matricula y graduacion por area de conocimiento?

## Estructura del Proyecto

```
Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/
|-- README.md                    # Este archivo
|-- CONTRIBUTING.md              # Guia de contribucion y Git Flow
|-- pyproject.toml               # Poetry (dependencias + metadata)
|-- Dockerfile                   # Contenedor reproducible
|-- .github/
|   +-- workflows/
|       +-- etl_update.yml       # GitHub Actions para ingesta periodica
|-- src/
|   |-- ingesta/                 # Scripts de extraccion (sodapy)
|   |-- transformacion/          # Limpieza, normalizacion, joins
|   |-- modelo/                  # Modelo estrella / modelado estadistico
|   +-- visualizacion/           # Funciones de graficos reutilizables
|-- notebooks/
|   |-- 01_eda.ipynb
|   |-- 02_analisis.ipynb
|   +-- 03_modelado.ipynb
|-- app/
|   +-- streamlit_app.py         # Dashboard interactivo
|-- datos/
|   |-- raw/                     # Datos crudos (gitignored si pesados)
|   |-- processed/               # Datos limpios
|   +-- catalogo.yaml            # Metadatos de cada dataset
|-- docs/                        # Informes y documentacion
|-- tests/                       # Tests automatizados
|-- artifacts/                   # Artefactos generados (metricas, reportes)
+-- models/                      # Modelos serializados
```

## Instalacion

```bash
# Clonar el repositorio
git clone https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia.git
cd Proyecto-Observatorio-Datos-de-Educacion-en-Colombia

# Instalar dependencias con Poetry
pip install poetry
poetry install

# Ejecutar pipeline de ingesta
poetry run python -m src.ingesta.main

# Ejecutar pipeline de transformacion
poetry run python -m src.transformacion.main

# Lanzar dashboard
poetry run streamlit run app/streamlit_app.py
```

## Cronograma -- CRISP-DM

### Sprint 1 (Sem 1-2)

Ingesta automatizada: `src/ingesta/snies.py`, `src/ingesta/icfes.py`, `src/ingesta/pte.py` con sodapy. Crear `datos/catalogo.yaml`.

### Sprint 2 (Sem 3-4)

Modelo estrella en DuckDB: `fact_matricula`, `fact_graduados`, `fact_saber`, `fact_presupuesto` + dimensiones compartidas.

### Sprint 3 (Sem 5-7)

EDA territorial (mapas coropleticos), analisis de brechas (estrato, zona, genero), cruce presupuesto vs resultados. Dashboard Streamlit.

### Sprint 4 (Sem 8)

Informe Quarto reproducible. Deploy del dashboard en Streamlit Cloud. Resolver issues abiertos.


## Equipo

| Rol | GitHub |
|-----|--------|
| Lider tecnico/ETL | [@Grmng31](https://github.com/Grmng31) |
| Modelado + analisis | [@AndresFHR2002](https://github.com/AndresFHR2002) |
| Por perfilar -- Canon Gonzalez Jhonatan | (por confirmar) |

**Director:** [@Izainea](https://github.com/Izainea)

## Metodologia

- **Framework analitico:** CRISP-DM
- **Gestion de proyecto:** Sprints de 2 semanas con Kanban (GitHub Projects)
- **Control de versiones:** Git Flow (`main` / `develop` / `feature/*`)
- **Estandar operativo:** Big 4 (governance formal, auditoria cruzada, mejora continua)

Consultar [CONTRIBUTING.md](CONTRIBUTING.md) para la guia completa de contribucion.

## Stack Tecnologico

| Capa | Herramientas |
|------|-------------|
| Ingesta | sodapy, pandas, requests |
| Almacen | DuckDB (modelo estrella) |
| Analisis | pandas, scikit-learn, statsmodels |
| Visualizacion | matplotlib, seaborn, plotly, folium |
| Dashboard | Streamlit |
| Reproducibilidad | Poetry, Docker, GitHub Actions |
| Testing | pytest, pandera |

---

> *"Si no esta en el README, el proyecto no existe."* -- Ustadistica 2026-I
