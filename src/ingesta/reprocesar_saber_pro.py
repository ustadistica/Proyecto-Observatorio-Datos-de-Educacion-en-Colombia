"""
Script para reprocesar el dataset de Saber Pro
Consolida todos los archivos de 2012 a 2024 en un solo archivo parquet
Corrige el campo periodo para extraer correctamente el año
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def cargar_archivo_saber_pro(ruta_archivo: str) -> pd.DataFrame:
    """
    Carga un archivo .txt de Saber Pro
    
    Args:
        ruta_archivo: Ruta al archivo .txt
        
    Returns:
        DataFrame con los datos cargados
    """
    logger.info(f"Cargando archivo: {ruta_archivo}")
    
    try:
        # Intentar cargar con separador ;
        df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8')
        logger.info(f"Archivo cargado exitosamente: {len(df):,} registros")
        return df
    except Exception as e:
        logger.warning(f"Error con encoding utf-8, intentando latin-1: {e}")
        try:
            df = pd.read_csv(ruta_archivo, sep=';', encoding='latin-1')
            logger.info(f"Archivo cargado con encoding latin-1: {len(df):,} registros")
            return df
        except Exception as e2:
            logger.error(f"Error cargando archivo {ruta_archivo}: {e2}")
            return pd.DataFrame()


def corregir_periodo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Corrige el campo periodo para extraer correctamente el año
    
    El campo periodo viene en formato YYYYNN donde NN es el número de periodo
    (ej: 20241 = primer periodo 2024, 20242 = segundo periodo 2024)
    
    Args:
        df: DataFrame con campo periodo
        
    Returns:
        DataFrame con campo anio corregido
    """
    logger.info("Corrigiendo campo periodo...")
    
    # Extraer año de los primeros 4 dígitos
    df['anio'] = df['periodo'].astype(str).str[:4].astype(int)
    
    # Contar registros por año
    logger.info("Distribución por año:")
    for anio, count in df['anio'].value_counts().sort_index().items():
        logger.info(f"  {anio}: {count:,} registros")
    
    return df


def consolidar_saber_pro(ruta_base: str = "datos/raw", 
                         ruta_salida: str = "datos/processed/saber_pro"):
    """
    Consolida todos los archivos de Saber Pro en un solo archivo parquet
    
    Args:
        ruta_base: Ruta a los archivos originales .txt
        ruta_salida: Ruta donde se guardará el archivo consolidado
    """
    logger.info("=" * 60)
    logger.info("INICIANDO REPROCESAMIENTO DE SABER PRO")
    logger.info("=" * 60)
    
    # Lista de archivos a procesar (2012-2024)
    anios = list(range(2012, 2025))
    archivos = [Path(ruta_base) / f"Examen_Saber_Pro_Genericas_{anio}.txt" for anio in anios]
    
    # Filtrar solo archivos que existen
    archivos_existentes = [f for f in archivos if f.exists()]
    
    logger.info(f"Archivos encontrados: {len(archivos_existentes)}")
    for archivo in archivos_existentes:
        logger.info(f"  - {archivo.name}")
    
    # Cargar y consolidar todos los archivos
    dataframes = []
    for archivo in archivos_existentes:
        df = cargar_archivo_saber_pro(archivo)
        if not df.empty:
            dataframes.append(df)
    
    if not dataframes:
        logger.error("No se encontraron datos para procesar")
        return
    
    # Unir todos los dataframes
    logger.info("Uniéndolo todos los dataframes...")
    df_consolidado = pd.concat(dataframes, ignore_index=True)
    
    logger.info(f"Total registros consolidados: {len(df_consolidado):,}")
    
    # Corregir campo periodo
    df_consolidado = corregir_periodo(df_consolidado)
    
    # Eliminar duplicados si los hay
    logger.info("Eliminando duplicados...")
    antes = len(df_consolidado)
    df_consolidado = df_consolidado.drop_duplicates()
    despues = len(df_consolidado)
    logger.info(f"Duplicados eliminados: {antes - despues:,}")
    
    # Convertir TODAS las columnas objeto a string para evitar errores de conversión
    logger.info("Convirtiendo columnas problemáticas a string...")
    columnas_objeto = df_consolidado.select_dtypes(include=['object']).columns
    for col in columnas_objeto:
        # Forzar todas las columnas objeto a string para evitar errores
        df_consolidado[col] = df_consolidado[col].astype(str)
    
    # Guardar archivo consolidado
    ruta = Path(ruta_salida)
    ruta.mkdir(parents=True, exist_ok=True)
    
    archivo_salida = ruta / "saber_pro_consolidado.parquet"
    
    # Si el archivo existe, hacer backup
    if archivo_salida.exists():
        backup = ruta / f"saber_pro_consolidado_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        logger.info(f"Haciendo backup del archivo anterior: {backup}")
        archivo_salida.rename(backup)
    
    logger.info(f"Guardando archivo consolidado: {archivo_salida}")
    df_consolidado.to_parquet(archivo_salida, index=False)
    
    logger.info("=" * 60)
    logger.info("REPROCESAMIENTO COMPLETADO EXITOSAMENTE")
    logger.info("=" * 60)
    
    # Imprimir resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL REPROCESAMIENTO")
    print("=" * 60)
    print(f"\nTotal registros: {len(df_consolidado):,}")
    print(f"Columnas: {len(df_consolidado.columns)}")
    print(f"\nDistribución por año:")
    for anio, count in df_consolidado['anio'].value_counts().sort_index().items():
        print(f"  {anio}: {count:,} registros ({count/len(df_consolidado)*100:.1f}%)")
    
    print(f"\nArchivo guardado en: {archivo_salida}")


if __name__ == "__main__":
    consolidar_saber_pro()