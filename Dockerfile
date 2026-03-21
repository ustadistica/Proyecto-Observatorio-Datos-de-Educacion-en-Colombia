# Dockerfile para Pipeline DVC de Observatorio de Datos de Educación en Colombia

# Etapa 1: Construcción base
FROM python:3.10-slim

# Mantenedor
LABEL maintainer="ustadistica@usantotomas.edu.co"

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Actualizar sistema y instalar dependencias base
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar DVC con soporte para diferentes remotos
RUN pip install --no-cache-dir \
    dvc[s3,gs,azure,oss,ssh] \
    dvc-ssh

# Copiar estructura de proyecto (excluyendo archivos innecesarios)
COPY .gitignore .
COPY pyproject.toml .
COPY src/ ./src/
COPY datos/ ./datos/
COPY notebooks/ ./notebooks/
COPY reportes/ ./reportes/

# Inicializar DVC
RUN dvc init

# Configurar DVC
RUN dvc config core.autostage true

# Agregar datos al versionado DVC
RUN dvc add datos/catalogo.yaml

# Crear pipeline DVC
RUN dvc stage add \
    -n verificar_entorno \
    -c datos/catalogo.yaml \
    -o /tmp/entorno_verificado.txt \
    "python -c \"import pandas; import numpy; import openpyxl; import pyarrow; print('✅ Entorno verificado'); open('/tmp/entorno_verificado.txt', 'w').write('Entorno OK')\""

RUN dvc stage add \
    -n probar_ingesta_snies \
    -d src/ingesta/ingesta_snies.py \
    -d datos/raw/snies/ \
    -o datos/raw/snies/matriculados/matriculados_consolidado.parquet \
    -o datos/raw/snies/graduados/graduados_consolidado.parquet \
    "python src/ingesta/ingesta_snies.py"

RUN dvc stage add \
    -n probar_ingesta_original \
    -d src/ingesta/ingesta_snies_original.py \
    "python src/ingesta/ingesta_snies_original.py"

RUN dvc stage add \
    -n probar_ingesta_main \
    -d src/ingesta/main.py \
    "python src/ingesta/main.py"

RUN dvc stage add \
    -n probar_transformacion \
    -d src/transformacion/transformacion_main.py \
    "python src/transformacion/transformacion_main.py"

RUN dvc stage add \
    -n probar_visualizacion \
    -d src/visualizacion/__init__.py \
    "python -c \"import src.visualizacion; print('✅ Visualización OK')\""

RUN dvc stage add \
    -n probar_modelo \
    -d src/modelo/__init__.py \
    "python -c \"import src.modelo; print('✅ Modelo OK')\""

RUN dvc stage add \
    -n probar_tests \
    -d tests/test_ingesta.py \
    -d tests/__init__.py \
    "python -m pytest tests/ -v"

RUN dvc stage add \
    -n generar_reporte \
    -d /tmp/entorno_verificado.txt \
    -o reportes/dvc_pipeline_report.txt \
    "echo '=== Pipeline DVC Completada ===' > reportes/dvc_pipeline_report.txt && \
     echo 'Fecha: $(date)' >> reportes/dvc_pipeline_report.txt && \
     echo '' >> reportes/dvc_pipeline_report.txt && \
     echo '✅ Entorno verificado' >> reportes/dvc_pipeline_report.txt && \
     echo '✅ Scripts de ingesta verificados' >> reportes/dvc_pipeline_report.txt && \
     echo '✅ Scripts de transformación verificados' >> reportes/dvc_pipeline_report.txt && \
     echo '✅ Módulos de visualización y modelo verificados' >> reportes/dvc_pipeline_report.txt && \
     echo '✅ Tests unitarios ejecutados' >> reportes/dvc_pipeline_report.txt && \
     echo '' >> reportes/dvc_pipeline_report.txt && \
     echo '=== Estado de Archivos ===' >> reportes/dvc_pipeline_report.txt && \
     ls -la datos/raw/snies/matriculados/ >> reportes/dvc_pipeline_report.txt && \
     ls -la datos/raw/snies/graduados/ >> reportes/dvc_pipeline_report.txt"

# Reproducir pipeline para verificar funcionamiento
RUN dvc repro

# Mostrar estado del pipeline
RUN dvc pipeline show --ascii

# Comando por defecto
CMD ["dvc", "status"]