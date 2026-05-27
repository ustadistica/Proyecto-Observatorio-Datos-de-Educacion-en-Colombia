#!/usr/bin/env python3


import pandas as pd
import os
from pathlib import Path
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rutas de los datos
RAW_DATA_DIR = Path("datos/raw/snies")

def transformar_excel_a_parquet_si_no_existe(ruta_excel, ruta_parquet):
    """
    Transformar un archivo Excel a Parquet solo si el Parquet no existe.
    
    Args:
        ruta_excel (str): Ruta del archivo Excel de entrada
        ruta_parquet (str): Ruta del archivo Parquet de salida
    """
    try:
        if ruta_parquet.exists():
            logger.info(f"⏭️  Ya existe: {ruta_parquet}")
            return True
        
        logger.info(f"Transformando {ruta_excel} a {ruta_parquet}")
        
        # Leer el archivo Excel
        df = pd.read_excel(ruta_excel)
        
        # Convertir todas las columnas a string para evitar errores de tipo
        df = df.astype(str)
        
        # Guardar en formato Parquet
        df.to_parquet(ruta_parquet, index=False)
        
        logger.info(f"✅ Creado: {ruta_parquet}")
        return True
        
    except Exception as e:
        logger.error(f"Error transformando {ruta_excel}: {str(e)}")
        return False

def procesar_matriculados():
    """Procesar todos los archivos de matriculados (2015-2024) desde Excel."""
    logger.info("Iniciando proceso de matriculados...")
    
    archivos_matriculados = []
    
    # Procesar cada año de 2015 a 2024
    for year in range(2015, 2025):
        ruta_excel = RAW_DATA_DIR / "matriculados" / str(year) / f"matriculados{year}.xlsx"
        ruta_parquet = RAW_DATA_DIR / "matriculados" / str(year) / f"matriculados_{year}.parquet"
        
        if ruta_excel.exists():
            if transformar_excel_a_parquet_si_no_existe(ruta_excel, ruta_parquet):
                # Leer el archivo Parquet (existente o recién creado)
                df = pd.read_parquet(ruta_parquet)
                archivos_matriculados.append(df)
        else:
            logger.warning(f"Archivo Excel no encontrado: {ruta_excel}")
    
    # Crear archivo consolidado de matriculados (si no existe)
    if archivos_matriculados:
        ruta_consolidado = RAW_DATA_DIR / "matriculados" / "matriculados_consolidado.parquet"
        
        if not ruta_consolidado.exists():
            logger.info("Creando archivo consolidado de matriculados...")
            df_consolidado = pd.concat(archivos_matriculados, ignore_index=True)
            df_consolidado.to_parquet(ruta_consolidado, index=False)
            logger.info(f"✅ Consolidado creado: {ruta_consolidado}")
            logger.info(f"Total de registros consolidados: {len(df_consolidado)}")
        else:
            logger.info(f"⏭️  Consolidado ya existe: {ruta_consolidado}")
    
    logger.info("Proceso de matriculados completado")

def procesar_graduados():
    """Procesar todos los archivos de graduados (2015-2024) desde Excel."""
    logger.info("Iniciando proceso de graduados...")
    
    archivos_graduados = []
    
    # Procesar cada año de 2015 a 2024
    for year in range(2015, 2025):
        ruta_excel = RAW_DATA_DIR / "graduados" / str(year) / f"Graduados_{year}.xlsx"
        ruta_parquet = RAW_DATA_DIR / "graduados" / str(year) / f"graduados_{year}.parquet"
        
        if ruta_excel.exists():
            if transformar_excel_a_parquet_si_no_existe(ruta_excel, ruta_parquet):
                # Leer el archivo Parquet (existente o recién creado)
                df = pd.read_parquet(ruta_parquet)
                archivos_graduados.append(df)
        else:
            logger.warning(f"Archivo Excel no encontrado: {ruta_excel}")
    
    # Crear archivo consolidado de graduados (si no existe)
    if archivos_graduados:
        ruta_consolidado = RAW_DATA_DIR / "graduados" / "graduados_consolidado.parquet"
        
        if not ruta_consolidado.exists():
            logger.info("Creando archivo consolidado de graduados...")
            df_consolidado = pd.concat(archivos_graduados, ignore_index=True)
            df_consolidado.to_parquet(ruta_consolidado, index=False)
            logger.info(f"✅ Consolidado creado: {ruta_consolidado}")
            logger.info(f"Total de registros consolidados: {len(df_consolidado)}")
        else:
            logger.info(f"⏭️  Consolidado ya existe: {ruta_consolidado}")
    
    logger.info("Proceso de graduados completado")

def main():
    """Función principal del pipeline de ingesta."""
    logger.info("=== Iniciando Pipeline de Ingesta SNIES ===")
    
    # Procesar matriculados
    procesar_matriculados()
    
    # Procesar graduados
    procesar_graduados()
    
    logger.info("=== Pipeline de Ingesta SNIES Completado ===")

if __name__ == "__main__":
    main()