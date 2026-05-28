"""
Script para el procesamiento de las bases de datos del Saber Pro (2012-2024)
=============================================================================
Este script realiza:
1. Validación de cada base de datos por año
2. Limpieza de datos (valores nulos, duplicados, estandarización)
3. Generación de archivos .parquet individuales por año
4. Ingesta total consolidada en un único archivo .parquet

Autor: Equipo de Análisis de Datos
Fecha: Abril 2026
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuración de rutas
RUTA_PROYECTO = Path(__file__).parent.parent.parent
RUTA_DATOS = RUTA_PROYECTO / "datos" / "raw"
RUTA_SALIDA = RUTA_PROYECTO / "datos" / "processed"

# Crear directorio de salida si no existe
RUTA_SALIDA.mkdir(parents=True, exist_ok=True)

# Años disponibles (ajustar según los archivos existentes)
ANIOS_DISPONIBLES = list(range(2012, 2025))


def validar_archivo_existe(anio: int) -> tuple:
    """
    Valida si el archivo del año especificado existe.
    
    Returns:
        tuple: (existe: bool, ruta: str, mensaje: str)
    """
    nombre_archivo = f"Examen_Saber_Pro_Genericas_{anio}.txt"
    ruta_archivo = RUTA_DATOS / nombre_archivo
    
    if ruta_archivo.exists():
        return True, str(ruta_archivo), f"Archivo {nombre_archivo} encontrado"
    else:
        return False, str(ruta_archivo), f"⚠️ Archivo {nombre_archivo} NO encontrado"


def cargar_datos(ruta_archivo: str, anio: int) -> pd.DataFrame:
    """
    Carga los datos desde el archivo CSV con delimitador ;
    
    Returns:
        pd.DataFrame: DataFrame con los datos cargados
    """
    try:
        df = pd.read_csv(ruta_archivo, sep=";", encoding="utf-8", dtype=str)
        print(f"  ✅ Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas")
        return df
    except Exception as e:
        print(f"  ❌ Error cargando {ruta_archivo}: {str(e)}")
        return pd.DataFrame()


def validar_estructura(df: pd.DataFrame, anio: int) -> dict:
    """
    Realiza validaciones estructurales del DataFrame.
    
    Returns:
        dict: Resultados de la validación
    """
    validacion = {
        'anio': anio,
        'filas_totales': len(df),
        'columnas_totales': len(df.columns),
        'columnas_nulas': df.columns[df.isnull().all()].tolist(),
        'filas_vacias': len(df[df.isnull().all(axis=1)]),
        'duplicados_exactos': df.duplicated().sum(),
        'columnas_nombre': df.columns.tolist()
    }
    
    # Validar columnas esenciales (las que deberían estar en todos los años)
    columnas_esenciales = [
        'periodo', 'estu_consecutivo', 'estu_genero', 
        'punt_global', 'percentil_global'
    ]
    
    columnas_faltantes = [col for col in columnas_esenciales if col not in df.columns]
    validacion['columnas_esenciales_faltantes'] = columnas_faltantes
    
    return validacion


def limpiar_datos(df: pd.DataFrame, anio: int) -> pd.DataFrame:
    """
    Realiza la limpieza de los datos:
    1. Elimina filas completamente vacías
    2. Elimina duplicados exactos
    3. Estandariza nombres de columnas (lowercase, sin espacios)
    4. Convierte columnas numéricas a su tipo correspondiente
    5. Maneja valores nulos de manera apropiada
    """
    print(f"  Limpiando datos para {anio}...")
    df_limpio = df.copy()
    
    # 1. Eliminar filas completamente vacías
    filas_vacias_antes = len(df_limpio[df_limpio.isnull().all(axis=1)])
    df_limpio = df_limpio.dropna(how='all')
    print(f"    - Filas completamente vacías eliminadas: {filas_vacias_antes}")
    
    # 2. Eliminar duplicados exactos
    duplicados_antes = df_limpio.duplicated().sum()
    df_limpio = df_limpio.drop_duplicates()
    print(f"    - Duplicados exactos eliminados: {duplicados_antes}")
    
    # 3. Estandarizar nombres de columnas
    df_limpio.columns = (
        df_limpio.columns
        .str.strip()
        .str.lower()
        .str.replace(' ', '_')
        .str.replace('-', '_')
    )
    
    # 4. Convertir columnas numéricas
    columnas_numericas = ['punt_global', 'percentil_global']
    for col in columnas_numericas:
        if col in df_limpio.columns:
            df_limpio[col] = pd.to_numeric(df_limpio[col], errors='coerce')
    
    # 5. Agregar columna de año si no existe
    if 'anio_procesamiento' not in df_limpio.columns:
        df_limpio['anio_procesamiento'] = anio
    
    # 6. Agregar columna de fecha de procesamiento
    df_limpio['fecha_procesamiento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"  ✅ Limpieza completada: {df_limpio.shape[0]} filas, {df_limpio.shape[1]} columnas")
    
    return df_limpio


def guardar_parquet(df: pd.DataFrame, anio: int, tipo: str = 'individual') -> str:
    """
    Guarda el DataFrame como archivo Parquet.
    
    Args:
        df: DataFrame a guardar
        anio: Año de los datos
        tipo: 'individual' o 'consolidado'
    
    Returns:
        str: Ruta del archivo guardado
    """
    if tipo == 'individual':
        nombre_archivo = f"saber_pro_{anio}.parquet"
    else:
        nombre_archivo = f"saber_pro_consolidado_{datetime.now().strftime('%Y%m%d')}.parquet"
    
    ruta_completa = RUTA_SALIDA / nombre_archivo
    
    try:
        df.to_parquet(ruta_completa, index=False, engine='pyarrow')
        print(f"  ✅ Archivo guardado: {ruta_completa}")
        return str(ruta_completa)
    except Exception as e:
        print(f"  ❌ Error guardando {ruta_completa}: {str(e)}")
        return None


def procesar_anio(anio: int) -> dict:
    """
    Procesa un año completo: validación, carga, limpieza y guardado.
    
    Returns:
        dict: Resultados del procesamiento
    """
    print(f"\n{'='*60}")
    print(f"Procesando año: {anio}")
    print('='*60)
    
    resultado = {
        'anio': anio,
        'exitoso': False,
        'archivo_origen': None,
        'archivo_parquet': None,
        'validacion': None,
        'mensaje': ''
    }
    
    # 1. Validar existencia del archivo
    existe, ruta, mensaje = validar_archivo_existe(anio)
    resultado['archivo_origen'] = ruta
    print(mensaje)
    
    if not existe:
        resultado['mensaje'] = mensaje
        return resultado
    
    # 2. Cargar datos
    print("Cargando datos...")
    df = cargar_datos(ruta, anio)
    
    if df.empty:
        resultado['mensaje'] = "Error cargando los datos"
        return resultado
    
    # 3. Validar estructura
    print("Validando estructura...")
    validacion = validar_estructura(df, anio)
    resultado['validacion'] = validacion
    
    if validacion['columnas_esenciales_faltantes']:
        print(f"  ⚠️ Columnas esenciales faltantes: {validacion['columnas_esenciales_faltantes']}")
    
    print(f"  Filas totales: {validacion['filas_totales']}")
    print(f"  Columnas totales: {validacion['columnas_totales']}")
    print(f"  Filas vacías: {validacion['filas_vacias']}")
    print(f"  Duplicados: {validacion['duplicados_exactos']}")
    
    # 4. Limpiar datos
    print("Limpiando datos...")
    df_limpio = limpiar_datos(df, anio)
    
    # 5. Guardar como Parquet
    print("Guardando archivo Parquet...")
    ruta_parquet = guardar_parquet(df_limpio, anio, 'individual')
    resultado['archivo_parquet'] = ruta_parquet
    
    if ruta_parquet:
        resultado['exitoso'] = True
        resultado['mensaje'] = f"Procesamiento completado exitosamente"
    else:
        resultado['mensaje'] = "Error guardando el archivo Parquet"
    
    return resultado


def consolidar_todos_anios() -> dict:
    """
    Consolida todos los archivos Parquet individuales en un único archivo.
    
    Returns:
        dict: Resultados de la consolidación
    """
    print(f"\n{'='*60}")
    print("CONSOLIDANDO TODOS LOS AÑOS")
    print('='*60)
    
    resultado = {
        'exitoso': False,
        'archivo_consolidado': None,
        'total_filas': 0,
        'total_archivos': 0,
        'mensaje': ''
    }
    
    # Buscar todos los archivos parquet individuales
    archivos_parquet = list(RUTA_SALIDA.glob("saber_pro_*.parquet"))
    archivos_parquet = [f for f in archivos_parquet if 'consolidado' not in str(f)]
    
    if not archivos_parquet:
        resultado['mensaje'] = "No se encontraron archivos Parquet individuales para consolidar"
        print(f"  ❌ {resultado['mensaje']}")
        return resultado
    
    print(f"  Archivos encontrados: {len(archivos_parquet)}")
    
    # Cargar y concatenar todos los DataFrames
    dataframes = []
    for archivo in sorted(archivos_parquet):
        try:
            df = pd.read_parquet(archivo)
            dataframes.append(df)
            print(f"    ✅ {archivo.name}: {len(df)} filas")
        except Exception as e:
            print(f"    ❌ Error cargando {archivo.name}: {str(e)}")
    
    if not dataframes:
        resultado['mensaje'] = "No se pudo cargar ningún archivo Parquet"
        return resultado
    
    # Concatenar
    df_consolidado = pd.concat(dataframes, ignore_index=True)
    resultado['total_filas'] = len(df_consolidado)
    resultado['total_archivos'] = len(dataframes)
    
    print(f"\n  Total filas consolidadas: {resultado['total_filas']}")
    print(f"  Total columnas: {len(df_consolidado.columns)}")
    
    # Guardar archivo consolidado
    ruta_consolidado = guardar_parquet(df_consolidado, 0, 'consolidado')
    
    if ruta_consolidado:
        resultado['exitoso'] = True
        resultado['archivo_consolidado'] = ruta_consolidado
        resultado['mensaje'] = "Consolidación completada exitosamente"
    else:
        resultado['mensaje'] = "Error guardando el archivo consolidado"
    
    return resultado


def generar_reporte(resultados: list, consolidacion: dict) -> str:
    """
    Genera un reporte en texto del procesamiento.
    
    Returns:
        str: Ruta del archivo de reporte
    """
    reporte_path = RUTA_SALIDA / "reporte_procesamiento.txt"
    
    with open(reporte_path, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("REPORTE DE PROCESAMIENTO - BASES DE DATOS SABER PRO\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        
        f.write("PROCESAMIENTO POR AÑO:\n")
        f.write("-"*40 + "\n")
        
        exitos = 0
        total_filas = 0
        
        for resultado in resultados:
            f.write(f"\nAño: {resultado['anio']}\n")
            f.write(f"  Estado: {'✅ Exitoso' if resultado['exitoso'] else '❌ Fallido'}\n")
            f.write(f"  Archivo origen: {resultado['archivo_origen']}\n")
            
            if resultado['exitoso'] and resultado['validacion']:
                v = resultado['validacion']
                f.write(f"  Filas originales: {v['filas_totales']}\n")
                f.write(f"  Columnas: {v['columnas_totales']}\n")
                f.write(f"  Duplicados eliminados: {v['duplicados_exactos']}\n")
                exitos += 1
                total_filas += v['filas_totales']
            
            f.write(f"  Mensaje: {resultado['mensaje']}\n")
        
        f.write(f"\n{'='*40}\n")
        f.write(f"RESUMEN:\n")
        f.write(f"  Años procesados exitosamente: {exitos}/{len(resultados)}\n")
        f.write(f"  Total filas procesadas: {total_filas}\n")
        
        if consolidacion and consolidacion['exitoso']:
            f.write(f"\nCONSOLIDACIÓN:\n")
            f.write(f"  Estado: ✅ Exitosa\n")
            f.write(f"  Archivo consolidado: {consolidacion['archivo_consolidado']}\n")
            f.write(f"  Total filas consolidadas: {consolidacion['total_filas']}\n")
            f.write(f"  Archivos consolidados: {consolidacion['total_archivos']}\n")
        
        f.write(f"\n{'='*40}\n")
        f.write(f"Archivos generados en: {RUTA_SALIDA}\n")
    
    print(f"\n✅ Reporte generado: {reporte_path}")
    return str(reporte_path)


def main():
    """
    Función principal que orquesta todo el procesamiento.
    """
    print("="*60)
    print("PROCESAMIENTO DE BASES DE DATOS SABER PRO")
    print(f"Ruta de datos: {RUTA_DATOS}")
    print(f"Ruta de salida: {RUTA_SALIDA}")
    print("="*60)
    
    # Procesar cada año
    resultados = []
    for anio in ANIOS_DISPONIBLES:
        resultado = procesar_anio(anio)
        resultados.append(resultado)
    
    # Consolidar todos los años
    consolidacion = consolidar_todos_anios()
    
    # Generar reporte
    reporte = generar_reporte(resultados, consolidacion)
    
    # Resumen final
    print("\n" + "="*60)
    print("PROCESAMIENTO COMPLETADO")
    print("="*60)
    print(f"Resultados guardados en: {RUTA_SALIDA}")
    print(f"Reporte: {reporte}")
    
    exitos = sum(1 for r in resultados if r['exitoso'])
    print(f"Años procesados exitosamente: {exitos}/{len(resultados)}")
    
    if consolidacion and consolidacion['exitoso']:
        print(f"Archivo consolidado: {consolidacion['archivo_consolidado']}")


if __name__ == "__main__":
    try:
        # Verificar dependencias
        import pyarrow
    except ImportError:
        print("❌ Error: Se requiere pyarrow para guardar archivos Parquet")
        print("Instalar con: pip install pyarrow pandas")
        sys.exit(1)
    
    main()