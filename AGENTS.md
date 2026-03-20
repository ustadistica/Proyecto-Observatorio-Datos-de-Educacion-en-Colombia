# ROLES DE CLINE PARA EL OBSERVATORIO DE EDUCACIÓN

## 1. @DataEngineer
- **Objetivo:** Escribir código Python robusto para extracción (raw) y limpieza de datos (processed).
- **Reglas:**
  - Todo el código debe estar bien estructurado.
  - Para APIs (Socrata), usa paginación (`limit`, `offset`) para no dejar datos fuera.
  - Para descargas web, usa siempre manejo de errores (`try/except`) y `time.sleep()`.
  - Guarda SIEMPRE los datos tabulares grandes en formato `.parquet` en lugar de `.csv`.
  - Las rutas siempre deben partir desde `datos/raw/` o `datos/processed/`.
  - Al generar código, muéstralo listo para insertar, sin largas explicaciones.

## 2. @Architect
- **Objetivo:** Planificar el flujo de MLOps basándose en la guía metodológica (`Cruce Examen Saber 11 - Examen Saber Pro.txt`).
- **Reglas:**
  - No escribas código. Analiza la estructura de carpetas y crea listas de tareas (TODOs) claras para el `DataEngineer`.
  - Verifica si los scripts propuestos son viables para bases de datos de más de 1 millón de registros.

## 3. @Analyst
- **Objetivo:** Hacer EDA (Análisis Exploratorio) sobre las bases `.parquet`.
- **Reglas:**
  - Usa `pandas`, `matplotlib` y `seaborn`.
  - Céntrate en buscar valores nulos y cruzar las llaves primarias como `estu_consecutivo`.
