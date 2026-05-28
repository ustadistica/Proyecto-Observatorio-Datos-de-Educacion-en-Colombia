"""
Módulo para el cruce entre Saber Pro (ICFES) y Graduados SNIES
Issues 6.1 y 6.2: Análisis de eficiencia de culminación
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from mapeo_columnas_saber_pro import aplicar_mapeo_columnas

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def cargar_datos(ruta_base: str = "datos/processed"):
    """
    Carga los datos de Saber Pro y Graduados SNIES
    
    Args:
        ruta_base: Ruta base del directorio de datos procesados
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: DataFrames de Saber Pro y SNIES
    """
    logger.info("Cargando datos de Saber Pro...")
    saber_pro = pd.read_parquet(Path(ruta_base) / "saber_pro/saber_pro_consolidado.parquet")
    
    logger.info("Cargando datos de Graduados SNIES...")
    snies_graduados = pd.read_parquet(Path(ruta_base) / "snies/snies_graduados_consolidado.parquet")
    
    logger.info(f"Saber Pro: {saber_pro.shape[0]:,} registros, {saber_pro.shape[1]} columnas")
    logger.info(f"SNIES Graduados: {snies_graduados.shape[0]:,} registros, {snies_graduados.shape[1]} columnas")
    
    return saber_pro, snies_graduados


def preparar_saber_pro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara el DataFrame de Saber Pro para el cruce
    - Aplica mapeo de columnas
    - Extrae año del periodo
    - Convierte codigo_snies_programa a entero/string para cruce
    - Agrega columnas necesarias
    """
    # Aplicar mapeo de columnas primero
    df = aplicar_mapeo_columnas(df)
    
    df_prep = df.copy()
    
    # Extraer año del periodo (ej: 20241 -> 2024, 20242 -> 2024)
    if 'anio' not in df_prep.columns:
        df_prep['anio'] = df_prep['periodo'].astype(str).str[:4].astype(int)
    
    # Convertir codigo_snies_programa a entero para cruce (puede tener NaN)
    if 'codigo_snies_programa' in df_prep.columns:
        df_prep['codigo_snies_programa'] = pd.to_numeric(df_prep['codigo_snies_programa'], errors='coerce')
        df_prep['codigo_snies_programa'] = df_prep['codigo_snies_programa'].astype('Int64')
    
    # Calcular puntaje promedio por estudiante (promedio de los 4 módulos)
    modulos = ['punt_comuni_escrita', 'punt_razona_cuantitativa', 'punt_ingles', 'punt_lectura_critica', 'punt_comp_ciudadanas']
    modulos_existentes = [m for m in modulos if m in df_prep.columns]
    if modulos_existentes:
        df_prep['puntaje_promedio'] = df_prep[modulos_existentes].mean(axis=1, skipna=True)
    
    logger.info(f"Saber Pro preparado: {df_prep.shape[0]:,} registros")
    return df_prep


def preparar_snies_graduados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara el DataFrame de Graduados SNIES para el cruce
    - Convierte codigo_snies_programa a entero/string
    - Agrega columnas necesarias
    """
    df_prep = df.copy()
    
    # Renombrar anio_proceso a anio para consistencia
    df_prep = df_prep.rename(columns={'anio_proceso': 'anio'})
    
    # Asegurar que codigo_snies_programa sea del mismo tipo
    df_prep['codigo_snies_programa'] = pd.to_numeric(df_prep['codigo_snies_programa'], errors='coerce')
    df_prep['codigo_snies_programa'] = df_prep['codigo_snies_programa'].astype('Int64')
    
    logger.info(f"SNIES Graduados preparado: {df_prep.shape[0]:,} registros")
    return df_prep


def cruce_por_ies(df_saber: pd.DataFrame, df_snies: pd.DataFrame) -> pd.DataFrame:
    """
    Issue 6.1: Cruce de Saber Pro con Graduados SNIES a nivel de IES y año
    Incluye desglose por acreditación y universidades específicas
    
    Returns:
        DataFrame con agregación por IES y año
    """
    logger.info("Realizando cruce por IES y año...")
    
    # Limpiar nombres de departamentos (BOGOTA -> BOGOTÁ)
    df_saber = df_saber.copy()
    df_snies = df_snies.copy()
    
    if 'depto_ies' in df_saber.columns:
        df_saber['depto_ies'] = df_saber['depto_ies'].str.replace('BOGOTA', 'BOGOTÁ', regex=False)
    if 'depto_ies' in df_snies.columns:
        df_snies['depto_ies'] = df_snies['depto_ies'].str.replace('BOGOTA', 'BOGOTÁ', regex=False)
    
    # Verificar si existe columna de acreditación en SNIES
    tiene_acreditacion = 'ies_acreditada' in df_snies.columns
    
    # Agregación Saber Pro por IES y año
    saber_agg = df_saber.groupby(['nombre_ies', 'anio']).agg(
        promedio_puntaje=('puntaje_promedio', 'mean'),
        mediana_puntaje=('puntaje_promedio', 'median'),
        total_presentados=('estu_consecutivo', 'nunique'),
        desviacion_puntaje=('puntaje_promedio', 'std')
    ).reset_index()
    
    # Agregación SNIES Graduados por IES y año (con y sin acreditación)
    if tiene_acreditacion:
        # Agregación total (sin desglose)
        snies_total = df_snies.groupby(['nombre_institucion', 'anio']).agg(
            total_graduados=('graduados', 'sum'),
            programas_ofertados=('codigo_snies_programa', 'nunique')
        ).reset_index()
        snies_total = snies_total.rename(columns={'nombre_institucion': 'nombre_ies'})
        
        # Crear desglose por acreditación
        snies_acred = df_snies.groupby(['nombre_institucion', 'anio', 'ies_acreditada']).agg(
            graduados_acreditada=('graduados', 'sum')
        ).reset_index()
        
        # Pivotar para tener columnas separadas
        snies_pivot = snies_acred.pivot_table(
            index=['nombre_institucion', 'anio'],
            columns='ies_acreditada',
            values='graduados_acreditada',
            fill_value=0
        ).reset_index()
        
        # Renombrar columnas del pivote
        nuevas_columnas = ['nombre_institucion', 'anio']
        for col in snies_pivot.columns[2:]:
            if col == 'NO':
                nuevas_columnas.append('graduados_no_acreditada')
            elif col == 'SI':
                nuevas_columnas.append('graduados_acreditada')
            else:
                nuevas_columnas.append(f'graduados_{col}')
        
        snies_pivot.columns = nuevas_columnas
        snies_pivot = snies_pivot.rename(columns={'nombre_institucion': 'nombre_ies'})
        
        # Unir total con desglose por acreditación
        snies_agg = pd.merge(snies_total, snies_pivot, on=['nombre_ies', 'anio'], how='left')
    else:
        snies_agg = df_snies.groupby(['nombre_institucion', 'anio']).agg(
            total_graduados=('graduados', 'sum'),
            programas_ofertados=('codigo_snies_programa', 'nunique')
        ).reset_index()
        snies_agg = snies_agg.rename(columns={'nombre_institucion': 'nombre_ies'})
    
    # Cruce outer para incluir todas las IES
    cruce_ies = pd.merge(saber_agg, snies_agg, on=['nombre_ies', 'anio'], how='outer')
    
    # Llenar NaN con 0 para conteos
    cruce_ies['total_graduados'] = cruce_ies['total_graduados'].fillna(0)
    cruce_ies['total_presentados'] = cruce_ies['total_presentados'].fillna(0)
    
    # Llenar NaN en columnas de acreditación si existen
    if 'graduados_acreditada' in cruce_ies.columns:
        cruce_ies['graduados_acreditada'] = cruce_ies['graduados_acreditada'].fillna(0)
    if 'graduados_no_acreditada' in cruce_ies.columns:
        cruce_ies['graduados_no_acreditada'] = cruce_ies['graduados_no_acreditada'].fillna(0)
    
    # Calcular tasa de presentación (presentados / graduados)
    cruce_ies['tasa_presentacion'] = np.where(
        cruce_ies['total_graduados'] > 0,
        cruce_ies['total_presentados'] / cruce_ies['total_graduados'],
        np.nan
    )
    
    # Identificar las 3 universidades específicas
    universidades_especificas = [
        'UNIVERSIDAD SANTO TOMAS',
        'UNIVERSIDAD NACIONAL DE COLOMBIA',
        'CORPORACION UNIFICADA NACIONAL DE EDUCACION SUPERIOR-CUN-'
    ]
    cruce_ies['es_universidad_especifica'] = cruce_ies['nombre_ies'].isin(universidades_especificas)
    
    logger.info(f"Cruce por IES completado: {cruce_ies.shape[0]} registros")
    return cruce_ies


def cruce_por_programa(df_saber: pd.DataFrame, df_snies: pd.DataFrame) -> pd.DataFrame:
    """
    Issue 6.2: Cruce de Saber Pro con Graduados SNIES a nivel de programa y año
    
    Returns:
        DataFrame con agregación por programa y año
    """
    logger.info("Realizando cruce por programa y año...")
    
    # Agregación Saber Pro por programa y año
    saber_prog = df_saber.groupby(['codigo_snies_programa', 'programa_academico', 'nombre_ies', 'anio']).agg(
        promedio_puntaje=('puntaje_promedio', 'mean'),
        mediana_puntaje=('puntaje_promedio', 'median'),
        total_presentados=('estu_consecutivo', 'nunique'),
        desviacion_puntaje=('puntaje_promedio', 'std')
    ).reset_index()
    
    # Agregación SNIES Graduados por programa y año
    snies_prog = df_snies.groupby(['codigo_snies_programa', 'nombre_programa', 'nombre_institucion', 'anio']).agg(
        total_graduados=('graduados', 'sum'),
        programas_ofertados=('codigo_snies_programa', 'nunique')
    ).reset_index()
    
    # Renombrar para cruce
    snies_prog = snies_prog.rename(columns={
        'nombre_programa': 'programa_academico',
        'nombre_institucion': 'nombre_ies'
    })
    
    # Cruce outer
    cruce_prog = pd.merge(saber_prog, snies_prog, 
                          on=['codigo_snies_programa', 'programa_academico', 'nombre_ies', 'anio'], 
                          how='outer')
    
    # Llenar NaN con 0
    cruce_prog['total_graduados'] = cruce_prog['total_graduados'].fillna(0)
    cruce_prog['total_presentados'] = cruce_prog['total_presentados'].fillna(0)
    
    # Calcular tasa de presentación
    cruce_prog['tasa_presentacion'] = np.where(
        cruce_prog['total_graduados'] > 0,
        cruce_prog['total_presentados'] / cruce_prog['total_graduados'],
        np.nan
    )
    
    # Calcular brecha (diferencia entre presentados y graduados)
    cruce_prog['brecha_absoluta'] = cruce_prog['total_presentados'] - cruce_prog['total_graduados']
    cruce_prog['brecha_relativa'] = np.where(
        cruce_prog['total_graduados'] > 0,
        (cruce_prog['total_presentados'] - cruce_prog['total_graduados']) / cruce_prog['total_graduados'],
        np.nan
    )
    
    logger.info(f"Cruce por programa completado: {cruce_prog.shape[0]} registros")
    return cruce_prog


def calcular_correlaciones(cruce_ies: pd.DataFrame) -> dict:
    """
    Issue 6.1: Calcula coeficientes de correlación de Pearson y Spearman
    entre puntaje promedio y volumen de graduados
    
    Returns:
        Dict con coeficientes de correlación
    """
    logger.info("Calculando correlaciones...")
    
    # Filtrar datos válidos
    datos_validos = cruce_ies.dropna(subset=['promedio_puntaje', 'total_graduados'])
    datos_validos = datos_validos[datos_validos['total_graduados'] > 0]
    
    # Correlación de Pearson
    pearson_corr = datos_validos[['promedio_puntaje', 'total_graduados']].corr(method='pearson')
    
    # Correlación de Spearman
    spearman_corr = datos_validos[['promedio_puntaje', 'total_graduados']].corr(method='spearman')
    
    resultados = {
        'pearson': pearson_corr.iloc[0, 1],
        'spearman': spearman_corr.iloc[0, 1],
        'n_observaciones': len(datos_validos)
    }
    
    logger.info(f"Correlación Pearson: {resultados['pearson']:.4f}")
    logger.info(f"Correlación Spearman: {resultados['spearman']:.4f}")
    logger.info(f"Número de observaciones: {resultados['n_observaciones']}")
    
    return resultados


def top_programas_mayor_desfase(cruce_prog: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Issue 6.2: Retorna el top N de programas con mayor desfase entre evaluados y graduados
    
    Args:
        cruce_prog: DataFrame con cruce por programa
        n: Número de programas a retornar
        
    Returns:
        DataFrame con los top N programas
    """
    logger.info(f"Identificando top {n} programas con mayor desfase...")
    
    # Filtrar datos válidos
    datos_validos = cruce_prog.dropna(subset=['brecha_absoluta'])
    datos_validos = datos_validos[datos_validos['total_graduados'] > 0]
    
    # Agrupar por programa y sumar brechas en el tiempo
    brecha_por_programa = datos_validos.groupby(['codigo_snies_programa', 'programa_academico', 'nombre_ies']).agg(
        brecha_total=('brecha_absoluta', 'sum'),
        graduados_totales=('total_graduados', 'sum'),
        presentados_totales=('total_presentados', 'sum'),
        anios_analisis=('anio', 'nunique')
    ).reset_index()
    
    # Calcular brecha promedio
    brecha_por_programa['brecha_promedio'] = brecha_por_programa['brecha_total'] / brecha_por_programa['anios_analisis']
    
    # Ordenar por brecha total (valor absoluto)
    brecha_por_programa['brecha_abs_total'] = brecha_por_programa['brecha_total'].abs()
    top_programas = brecha_por_programa.nlargest(n, 'brecha_abs_total')
    
    logger.info(f"Top {n} programas identificados")
    return top_programas


def guardar_resultados(cruce_ies: pd.DataFrame, cruce_prog: pd.DataFrame, 
                       correlaciones: dict, top_programas: pd.DataFrame,
                       ruta_salida: str = "datos/processed"):
    """
    Guarda los resultados del análisis en archivos parquet
    """
    logger.info("Guardando resultados...")
    
    ruta = Path(ruta_salida)
    ruta.mkdir(parents=True, exist_ok=True)
    
    # Guardar cruce por IES
    cruce_ies.to_parquet(ruta / "cruce_saber_pro_graduados_ies.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'cruce_saber_pro_graduados_ies.parquet'}")
    
    # Guardar cruce por programa
    cruce_prog.to_parquet(ruta / "cruce_saber_pro_graduados_programa.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'cruce_saber_pro_graduados_programa.parquet'}")
    
    # Guardar top programas
    top_programas.to_parquet(ruta / "top_programas_mayor_desfase.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'top_programas_mayor_desfase.parquet'}")
    
    # Guardar correlaciones como JSON
    import json
    with open(ruta / "correlaciones.json", 'w') as f:
        json.dump(correlaciones, f, indent=4)
    logger.info(f"Guardado: {ruta / 'correlaciones.json'}")


def ejecutar_analisis_completo():
    """
    Función principal que ejecuta todo el pipeline de análisis
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISIS DE CRUCE SABER PRO - GRADUADOS SNIES")
    logger.info("=" * 60)
    
    # 1. Cargar datos
    saber_pro, snies_graduados = cargar_datos()
    
    # 2. Preparar datos
    saber_pro_prep = preparar_saber_pro(saber_pro)
    snies_graduados_prep = preparar_snies_graduados(snies_graduados)
    
    # 3. Realizar cruces
    cruce_ies = cruce_por_ies(saber_pro_prep, snies_graduados_prep)
    cruce_prog = cruce_por_programa(saber_pro_prep, snies_graduados_prep)
    
    # 4. Calcular correlaciones
    correlaciones = calcular_correlaciones(cruce_ies)
    
    # 5. Identificar top programas con mayor desfase
    top_programas = top_programas_mayor_desfase(cruce_prog, n=10)
    
    # 6. Guardar resultados
    guardar_resultados(cruce_ies, cruce_prog, correlaciones, top_programas)
    
    logger.info("=" * 60)
    logger.info("ANÁLISIS COMPLETADO EXITOSAMENTE")
    logger.info("=" * 60)
    
    return cruce_ies, cruce_prog, correlaciones, top_programas


if __name__ == "__main__":
    # Ejecutar análisis
    cruce_ies, cruce_prog, correlaciones, top_programas = ejecutar_analisis_completo()
    
    # Imprimir resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL ANÁLISIS")
    print("=" * 60)
    print(f"\nCorrelación entre puntaje promedio y graduados (Pearson): {correlaciones['pearson']:.4f}")
    print(f"Correlación entre puntaje promedio y graduados (Spearman): {correlaciones['spearman']:.4f}")
    print(f"Número de observaciones: {correlaciones['n_observaciones']}")
    
    print(f"\nTop 10 programas con mayor desfase:")
    print(top_programas[['programa_academico', 'nombre_ies', 'brecha_total', 'graduados_totales', 'presentados_totales']].to_string(index=False))