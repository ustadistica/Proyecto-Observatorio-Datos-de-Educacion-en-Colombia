# Estructura de Código Fuente

Este directorio contiene el código fuente organizado según la arquitectura del proyecto.

## Estructura de Directorios

```
src/
├── ingesta/              # Módulos para la ingesta de datos
│   ├── extrae_pte_educacion_full.py  # Extracción de datos PTE Educación
│   ├── scraper_snies.py              # Web scraping SNIES
│   └── snies_renamed_registros.py    # Procesamiento de registros SNIES
├── transformacion/       # Módulos para transformación de datos
│   └── main.py           # Procesamiento principal de bases de datos Saber Pro
├── modelo/              # Módulos para análisis y modelado
│   ├── analisis_descriptivo.py       # Análisis descriptivo de datos
│   └── analizar_departamentos.py     # Análisis por departamentos
└── visualizacion/       # Módulos para visualización
    └── app_streamlit.py              # Dashboard Streamlit
```

## Descripción de Módulos

### Ingesta (`src/ingesta/`)
- **extrae_pte_educacion_full.py**: Extrae datos completos del PTE Educación
- **scraper_snies.py**: Realiza web scraping de la base de datos SNIES
- **snies_renamed_registros.py**: Procesa y normaliza registros SNIES

### Transformación (`src/transformacion/`)
- **main.py**: Procesamiento principal de las bases de datos del Saber Pro (2012-2024)
  - Validación de archivos por año
  - Limpieza de datos (valores nulos, duplicados, estandarización)
  - Generación de archivos Parquet individuales
  - Consolidación en archivo único

### Modelo (`src/modelo/`)
- **analisis_descriptivo.py**: Realiza análisis descriptivo de los datos
  - Instituciones que más presentan el examen
  - Análisis por departamentos y tasas por 1000 habitantes
  - Puntajes por categorías (género, nivel académico, etc.)
  - Evolución temporal
  - Generación de reportes HTML interactivos
- **analizar_departamentos.py**: Análisis específico de valores de departamentos

### Visualización (`src/visualizacion/`)
- **app_streamlit.py**: Dashboard ejecutivo en Streamlit
  - Métricas de procesamiento
  - Análisis descriptivo interactivo
  - Visualización de hallazgos importantes (ciudades internacionales)
  - Muestra de datos procesados

## Uso

### Ejecución del Pipeline ETL
```bash
# Ingesta de datos
python src/ingesta/extrae_pte_educacion_full.py
python src/ingesta/scraper_snies.py

# Transformación de datos
python src/transformacion/main.py

# Análisis de datos
python src/modelo/analisis_descriptivo.py
python src/modelo/analizar_departamentos.py
```

### Dashboard Streamlit
```bash
streamlit run src/visualizacion/app_streamlit.py
```

## Integración con GitHub Actions

El workflow `.github/workflows/etl_update.yml` automatiza la ejecución del pipeline ETL:
- Se ejecuta diariamente a las 2 AM UTC
- Instala dependencias
- Ejecuta todos los módulos del pipeline
- Guarda resultados en `datos/` y `artifacts/`
- Realiza commit automático de cambios

## Rutas de Datos

- **Datos crudos**: `datos/raw/`
- **Datos procesados**: `datos/processed/`
- **Resultados de análisis**: `artifacts/analisis_resultados/`
- **Reportes**: `artifacts/analisis_resultados/reportes/`

## Dependencias

Las dependencias principales están especificadas en `requirements.txt`:
- pandas, numpy: Manipulación de datos
- plotly: Visualizaciones interactivas
- streamlit: Dashboard web
- pyarrow: Lectura/escritura Parquet