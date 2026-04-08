"""
Modulo Unificado de Ingesta: ICFES Saber 11
------------------------------------------
Fuentes:
1. 2000-2009: Procesamiento de archivos locales .txt (Semestrales unificados).
2. 2010-2022: Descarga automatica via API Socrata (ID: kgxf-xxbe).
"""
import os
import time
import subprocess
import sys

# Forzar salida inmediata en terminal
print("="*60, flush=True)
print("🚀 INICIANDO MÓDULO DE INGESTA: ICFES SABER 11", flush=True)
print(f"📍 Directorio: {os.getcwd()}", flush=True)
print("="*60, flush=True)

# os.environ["OPENBLAS_NUM_THREADS"] = "1"
# os.environ["MKL_NUM_THREADS"] = "1"

# Instalar dependencias automáticamente si no están disponibles
def instalar_dependencias():
    """Instala las dependencias necesarias para el script."""
    dependencias = ['pandas', 'requests', 'sodapy', 'pyarrow', 'fastparquet']
    
    for dependencia in dependencias:
        try:
            print(f"🔍 Verificando {dependencia}...", end=" ", flush=True)
            __import__(dependencia)
            print("✅ OK", flush=True)
        except ImportError:
            print(f"\n📦 Instalando {dependencia}...", flush=True)
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', dependencia])
                print(f"✅ {dependencia} instalado exitosamente")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error instalando {dependencia}: {e}")
                return False
        except Exception as e:
            print(f"❌ Error al cargar {dependencia}: {e}")
            return False
    return True

# Verificar e instalar dependencias antes de importar
if not instalar_dependencias():
    print("❌ No se pudieron instalar todas las dependencias. Saliendo...")
    sys.exit(1)

import logging
import pandas as pd
from pathlib import Path
from sodapy import Socrata

# Configuracion de Logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(levelname)s | %(message)s",
    force=True
)
logger = logging.getLogger(__name__)

# Ajustar base al directorio del proyecto
BASE_DIR = Path(".")
RAW_ICFES = BASE_DIR / "datos" / "raw" / "icfes" / "saber_11"
DATASET_ID = "kgxf-xxbe"

def ingesta_legacy_txt(years):
    """Procesa archivos .txt de 2000-2009 unificando semestres como strings."""
    for anio in years:
        # Buscamos archivos en la carpeta raw
        archivos = list(RAW_ICFES.rglob(f"*{anio}*.txt"))
        if not archivos:
            continue
        logger.info(f"--- Procesando Legacy TXT {anio} ({len(archivos)} archivos) ---")
        dfs = []
        for f in archivos:
            try:
                # Delimitador ';' detectado en auditoria, procesar en chunks para evitar error de memoria
                chunk_iter = pd.read_csv(
                    f,
                    sep=';',
                    engine='python',
                    encoding='latin-1',
                    on_bad_lines='skip',
                    chunksize=50000
                )
                for chunk in chunk_iter:
                    dfs.append(chunk.astype(str))
                logger.info(f"  Cargado: {f.name}")
            except Exception as e:
                logger.error(f"  Error en {f.name}: {e}")

        if dfs:
            out_dir = RAW_ICFES / str(anio)
            out_dir.mkdir(parents=True, exist_ok=True)
            pd.concat(dfs, ignore_index=True).to_parquet(
                out_dir / f"saber11_{anio}_consolidado.parquet",
                index=False
            )
            logger.info(f"Creado Parquet consolidado {anio}")


def descargar_dataset_completo(anio, client, limite_por_chunk=20000, delay=2):
    """
    Descarga el dataset completo con paginación y delays para evitar throttling.
    
    Args:
        anio: Año a descargar (ej. 2018, 2019)
        client: Cliente Socrata
        limite_por_chunk: Número de registros por chunk (default: 1000)
        delay: Segundos de espera entre chunks (default: 2)
    
    Returns:
        Lista con todos los registros descargados
    """
    logger.info(f"=== INICIANDO DESCARGA COMPLETA PARA {anio} ===")
    logger.info(f"Chunk size: {limite_por_chunk} registros")
    logger.info(f"Delay entre chunks: {delay} segundos")
    
    registros_totales = []
    offset = 0
    chunk_num = 0
    
    while True:
        chunk_num += 1
        
        try:
            # Descargar chunk
            chunk = client.get(
                DATASET_ID,
                where=f"periodo like '{anio}%'",
                limit=limite_por_chunk,
                offset=offset
            )
            
            if not chunk:
                logger.info(f"✅ DESCARGA COMPLETA PARA {anio}")
                logger.info(f"Total chunks: {chunk_num - 1}")
                logger.info(f"Total registros: {len(registros_totales)}")
                break
            
            registros_totales.extend(chunk)
            offset += limite_por_chunk
            
            # Esperar para evitar throttling
            if chunk_num % 5 == 0:  # Pausa más larga cada 5 chunks
                logger.info(f"   Pausa larga de {delay * 3} segundos...")
                time.sleep(delay * 3)
            else:
                time.sleep(delay)
            
            logger.info(f"   Chunk #{chunk_num}: {len(chunk)} registros")
            logger.info(f"   Acumulado: {len(registros_totales)} registros")
            
        except Exception as e:
            logger.warning(f"   ⚠️ Error en chunk #{chunk_num}: {e}")
            logger.info("   Esperando 10 segundos antes de reintentar...")
            time.sleep(10)
            continue
    
    return registros_totales


def ingesta_api_socrata(years):
    """Descarga datos 2010-2022 usando paginación con delays para evitar throttling."""
    client = Socrata("www.datos.gov.co", None)
    
    for anio in years:
        logger.info(f"--- Descargando API Socrata {anio} (con paginación) ---")
        
        try:
            # Descargar dataset completo con paginación
            registros_totales = descargar_dataset_completo(anio, client, limite_por_chunk=20000, delay=2)
            
            if registros_totales:
                out_dir = RAW_ICFES / str(anio)
                out_dir.mkdir(parents=True, exist_ok=True)
                
                # Convertir a DataFrame y guardar como parquet
                df = pd.DataFrame.from_records(registros_totales)
                output_file = out_dir / f"saber11_{anio}_api_completo.parquet"
                df.to_parquet(output_file, index=False)
                
                logger.info(f"✅ API {anio} completada con exito.")
                logger.info(f"   Archivo guardado: {output_file}")
                logger.info(f"   Tamaño: {len(df)} filas, {len(df.columns)} columnas")
                logger.info(f"   Tamaño en disco: {output_file.stat().st_size:,} bytes")
            else:
                logger.warning(f"⚠️ No se encontraron datos para {anio}")
                
        except Exception as e:
            logger.error(f"❌ Error descargando {anio}: {e}")

    client.close()


if __name__ == "__main__":
    # Ingesta Legacy
    ingesta_legacy_txt(range(2000, 2010))

    # Ingesta API
    ingesta_api_socrata(range(2010, 2023))