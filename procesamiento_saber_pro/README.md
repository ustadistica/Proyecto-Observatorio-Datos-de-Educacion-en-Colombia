# Procesamiento de Bases de Datos - Saber Pro (2012-2024)

## Descripción

Este módulo contiene scripts para el procesamiento completo de las bases de datos del examen Saber Pro (competencias genéricas) de los años 2012 a 2024. El procesamiento incluye:

1. **Validación**: Verifica la existencia y estructura de cada archivo
2. **Limpieza**: Elimina duplicados, filas vacías y estandariza formatos
3. **Conversión**: Transforma los datos a formato Parquet (más eficiente)
4. **Consolidación**: Une todos los años en un único archivo Parquet

## Estructura del Directorio

```
procesamiento_saber_pro/
├── procesar_saber_pro.py    # Script principal de procesamiento
├── requirements.txt          # Dependencias necesarias
├── README.md                 # Esta documentación
└── datos_procesados/         # Directorio de salida (se genera automáticamente)
    ├── saber_pro_2012.parquet
    ├── saber_pro_2013.parquet
    ├── ...
    ├── saber_pro_2024.parquet
    ├── saber_pro_consolidado_YYYYMMDD.parquet
    └── reporte_procesamiento.txt
```

## Requisitos

- Python 3.8 o superior
- Las siguientes librerías (instaladas vía pip):
  - pandas
  - pyarrow
  - numpy

## Instalación

1. Navegar al directorio del script:
```bash
cd Códigos/procesamiento_saber_pro
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### 1. Ejecutar procesamiento completo

```bash
python procesar_saber_pro.py
```

Este comando:
- Procesará cada año disponible (2012-2024)
- Generará un archivo `.parquet` por cada año
- Creará un archivo consolidado con todos los años
- Generará un reporte detallado del procesamiento

### 2. Ejecutar Dashboard Interactivo (Streamlit)

```bash
streamlit run app_streamlit.py
```

La aplicación web incluye:
- 📊 **KPIs principales**: Total de registros, años procesados, calidad de datos
- 📈 **Gráficos interactivos**: Evolución anual, distribución porcentual, métricas de calidad
- 🔍 **Análisis detallado por año**: Explora cada año individualmente
- 🧹 **Detalle del proceso de limpieza**: Documentación completa del procesamiento
- 📋 **Muestra de datos**: Visualiza ejemplos de los datos procesados

**Características del Dashboard:**
- Paleta de colores ejecutiva (azules, blancos, naranjas)
- Interfaz moderna y responsiva
- Gráficos interactivos con Plotly
- Navegación intuitiva por secciones

### 3. Ejecutar Análisis Descriptivo

```bash
python analisis_descriptivo.py
```

Este script genera un análisis completo que incluye:
- 🏫 **Instituciones que más presentan el examen** (Top 20)
- 🗺️ **Análisis por departamentos** con tasa por 1000 habitantes
- 📊 **Puntajes por categoría**: género, nivel académico, carácter institucional, estrato
- 📈 **Evolución temporal** de puntajes y número de estudiantes
- ⚖️ **Análisis de diferencias de género** en puntajes
- 📄 **Reporte HTML completo** con gráficos interactivos e interpretaciones

**Archivos generados:**
- `analisis_resultados/reporte_completo.html` - Reporte principal con todos los análisis
- `analisis_resultados/top_instituciones.html` - Gráfico interactivo de instituciones
- `analisis_resultados/departamentos_*.html` - Gráficos por departamento
- `analisis_resultados/puntajes_por_*.html` - Gráficos de puntajes por categoría
- `analisis_resultados/evolucion_temporal.html` - Evolución anual

### Procesar un año específico

Puedes modificar el script para procesar solo un año específico cambiando la variable `ANIOS_DISPONIBLES`:

```python
ANIOS_DISPONIBLES = [2021]  # Solo procesar 2021
```

## Características del Procesamiento

### Validación
- Verifica existencia de archivos
- Valida columnas esenciales
- Reporta filas vacías y duplicados

### Limpieza
- Elimina filas completamente vacías
- Elimina registros duplicados exactos
- Estandariza nombres de columnas (minúsculas, guiones bajos)
- Convierte columnas numéricas a su tipo correspondiente
- Agrega columnas de metadatos (año_procesamiento, fecha_procesamiento)

### Salida
- Archivos Parquet individuales por año
- Archivo Parquet consolidado con todos los años
- Reporte en texto con detalles del procesamiento

## Archivos de Entrada

Los archivos de entrada deben estar en el directorio `datos/` con el siguiente formato:
- Nombre: `Examen_Saber_Pro_Genericas_{AAAA}.txt`
- Formato: CSV con delimitador `;`
- Encoding: UTF-8

## Archivos de Salida

Todos los archivos procesados se guardan en:
`Códigos/procesamiento_saber_pro/datos_procesados/`

### Archivos Parquet Individuales
- `saber_pro_{AAAA}.parquet` - Datos procesados de cada año

### Archivo Consolidado
- `saber_pro_consolidado_YYYYMMDD.parquet` - Todos los años unidos

### Reporte
- `reporte_procesamiento.txt` - Detalles del procesamiento

## Notas Importantes

1. **No modificar archivos originales**: Este script solo lee los archivos del directorio `datos/` y genera nuevos archivos en `datos_procesados/`

2. **Compatibilidad entre años**: Las columnas pueden variar entre diferentes años. El script maneja estas diferencias al consolidar.

3. **Memoria**: El procesamiento de todos los años puede requerir memoria RAM significativa. Se recomienda al menos 8GB de RAM.

4. **Espacio en disco**: Los archivos Parquet son más compactos que los CSV originales, pero aún así se requiere espacio para el procesamiento.

## Solución de Problemas

### Error: "No se reconoce el término python"
- Asegúrate de tener Python instalado y agregado al PATH
- Intenta con `py` en lugar de `python` en Windows

### Error: "ModuleNotFoundError: No module named 'pandas'"
- Ejecuta: `pip install pandas pyarrow numpy`

### Error: "No se encontraron archivos"
- Verifica que los archivos estén en el directorio `datos/`
- Verifica que los nombres sigan el formato: `Examen_Saber_Pro_Genericas_{AAAA}.txt`

## Autor

Equipo de Análisis de Datos - Proyecto Observatorio de Educación en Colombia

## Fecha

Abril 2026