"""
Módulo para el Análisis de Desplazamiento e Impacto Territorial de las IES
Issue 6.4: Movilidad estudiantil interdepartamental
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from mapeo_columnas_saber_pro import aplicar_mapeo_columnas

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def cargar_datos_saber_pro(ruta_base: str = "datos/processed"):
    """
    Carga los datos de Saber Pro para análisis de movilidad
    """
    logger.info("Cargando datos de Saber Pro para análisis de movilidad...")
    saber_pro = pd.read_parquet(Path(ruta_base) / "saber_pro/saber_pro_consolidado.parquet")
    
    logger.info(f"Saber Pro cargado: {saber_pro.shape[0]:,} registros")
    return saber_pro


def preparar_datos_movilidad(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara los datos para análisis de movilidad
    - Aplica mapeo de columnas
    - Extrae año del periodo
    - Selecciona columnas relevantes
    - Limpia datos de departamentos (corrige BOGOT, BOGOTÁ, ATLANTA -> ATLANTICO, etc.)
    - Corrige encoding de caracteres especiales
    """
    # Aplicar mapeo de columnas primero
    df = aplicar_mapeo_columnas(df)
    
    df_prep = df.copy()
    
    # Extraer año del periodo (si no existe)
    if 'anio' not in df_prep.columns:
        df_prep['anio'] = df_prep['periodo'].astype(str).str[:4].astype(int)
    
    # Seleccionar columnas relevantes para movilidad
    columnas_movilidad = [
        'periodo', 'estu_consecutivo', 'anio',
        'depto_presentacion', 'cod_depto_presentacion',  # Dónde presentó el examen
        'depto_residencia', 'cod_depto_residencia',      # Dónde reside
        'depto_ies', 'codigo_ies', 'nombre_ies',         # Dónde está la IES
        'depto_programa', 'codigo_snies_programa',       # Dónde se ofrece el programa
        'programa_academico', 'caracter_ies', 'origen_ies',
        'genero', 'nse_individual', 'nse_ies'
    ]
    
    # Filtrar solo columnas que existen
    columnas_existentes = [col for col in columnas_movilidad if col in df_prep.columns]
    df_movilidad = df_prep[columnas_existentes].dropna(subset=['depto_presentacion', 'depto_ies'])
    
    # Diccionario de corrección de departamentos
    # Corrige errores comunes de encoding y nombres duplicados
    correcciones_deptos = {
        # Bogotá (múltiples variantes)
        'BOGOT': 'BOGOTÁ',
        'BOGOTA': 'BOGOTÁ',
        
        # Departamentos con errores de encoding (caracteres corruptos)
        'ANTIOQUIA': 'ANTIOQUIA',
        'BOLIVAR': 'BOLÍVAR',
        'BOLVAR': 'BOLÍVAR',
        'BOYAC': 'BOYACÁ',
        'BOYACA': 'BOYACÁ',
        'CAQUET': 'CAQUETÁ',
        'CAQUETA': 'CAQUETÁ',
        'CHOC': 'CHOCÓ',
        'CHOCO': 'CHOCÓ',
        'CORDOBA': 'CÓRDOBA',
        'CRDOBA': 'CÓRDOBA',
        'NARIO': 'NARIÑO',
        'QUINDO': 'QUINDÍO',
        'QUINDIO': 'QUINDÍO',
        'SAN ANDRS': 'SAN ANDRÉS',
        'SAN ANDRES': 'SAN ANDRÉS',
        'ATLNTICO': 'ATLÁNTICO',
        'ATLANTICO': 'ATLÁNTICO',
        
        # Ciudades extranjeras que no son departamentos colombianos
        'ATLANTA': 'EXTRANJERO',
        'BARCELONA': 'EXTRANJERO',
        'BERLIN': 'EXTRANJERO',
        'CALGARY': 'EXTRANJERO',
        'FLANDES ORIENTAL': 'EXTRANJERO',
        'GUADALAJARA': 'EXTRANJERO',
        'LIMA': 'EXTRANJERO',
        'MADRID': 'EXTRANJERO',
        'MELBOURNE': 'EXTRANJERO',
        'MIAMI': 'EXTRANJERO',
        'NUEVA YORK': 'EXTRANJERO',
        'PARIS': 'EXTRANJERO',
        'SYDNEY': 'EXTRANJERO',
        'VALENCIA': 'EXTRANJERO',
    }
    
    # Limpiar nombres de departamentos (pueden tener caracteres corruptos)
    for col in ['depto_presentacion', 'depto_residencia', 'depto_ies', 'depto_programa']:
        if col in df_movilidad.columns:
            # Primero corregir encoding latin-1 -> utf-8
            try:
                df_movilidad[col] = df_movilidad[col].str.encode('latin-1').str.decode('utf-8', errors='ignore')
            except:
                pass
            
            # Estandarizar a mayúsculas
            df_movilidad[col] = df_movilidad[col].str.strip().str.upper()
            
            # Aplicar correcciones
            df_movilidad[col] = df_movilidad[col].replace(correcciones_deptos)
            
            # Limpiar posibles espacios adicionales
            df_movilidad[col] = df_movilidad[col].str.strip()
    
    logger.info(f"Datos de movilidad preparados: {df_movilidad.shape[0]:,} registros")
    logger.info(f"Departamentos únicos después de limpieza: {df_movilidad['depto_ies'].nunique()}")
    return df_movilidad


def crear_matriz_origen_destino(df_movilidad: pd.DataFrame, nivel: str = 'departamento') -> pd.DataFrame:
    """
    Issue 6.4: Crea matriz de origen-destino de estudiantes
    
    Args:
        df_movilidad: DataFrame con datos de movilidad
        nivel: Nivel de agregación ('departamento' o 'municipio')
        
    Returns:
        DataFrame con matriz origen-destino
    """
    logger.info(f"Creando matriz origen-destino a nivel {nivel}...")
    
    if nivel == 'departamento':
        origen = 'depto_residencia'
        destino = 'depto_ies'
    else:
        origen = 'mcpio_residencia'
        destino = 'mcpio_ies'
    
    # Verificar que las columnas existan
    if origen not in df_movilidad.columns or destino not in df_movilidad.columns:
        logger.warning(f"Columnas {origen} o {destino} no disponibles, usando alternativas...")
        if nivel == 'departamento':
            origen = 'depto_presentacion'
            destino = 'depto_ies'
        else:
            origen = 'mcpio_presentacion'
            destino = 'mcpio_ies'
    
    # Agrupar por origen-destino
    matriz = df_movilidad.groupby([origen, destino]).agg(
        total_estudiantes=('estu_consecutivo', 'nunique'),
        total_presentaciones=('periodo', 'count')
    ).reset_index()
    
    # Renombrar columnas
    matriz = matriz.rename(columns={
        origen: 'origen',
        destino: 'destino'
    })
    
    # Calcular porcentajes
    matriz['porcentaje'] = matriz.groupby('origen')['total_estudiantes'].transform(
        lambda x: (x / x.sum() * 100) if x.sum() > 0 else 0
    )
    
    logger.info(f"Matriz origen-destino creada: {matriz.shape[0]} registros")
    return matriz


def calcular_metricas_concentracion(df_movilidad: pd.DataFrame) -> pd.DataFrame:
    """
    Issue 6.4: Calcula métricas de concentración de oferta educativa por departamento
    
    Returns:
        DataFrame con métricas de concentración por departamento
    """
    logger.info("Calculando métricas de concentración...")
    
    # Agrupar por departamento de la IES
    concentracion = df_movilidad.groupby('depto_ies').agg(
        total_estudiantes=('estu_consecutivo', 'nunique'),
        total_programas=('codigo_snies_programa', 'nunique'),
        total_ies=('nombre_ies', 'nunique'),
        total_presentaciones=('periodo', 'count')
    ).reset_index()
    
    # Calcular métricas derivadas
    concentracion['promedio_estudiantes_por_programa'] = (
        concentracion['total_estudiantes'] / concentracion['total_programas']
    )
    
    concentracion['promedio_estudiantes_por_ies'] = (
        concentracion['total_estudiantes'] / concentracion['total_ies']
    )
    
    # Porcentaje del total nacional
    total_nacional = concentracion['total_estudiantes'].sum()
    concentracion['porcentaje_nacional'] = (concentracion['total_estudiantes'] / total_nacional * 100)
    
    # Ranking
    concentracion = concentracion.sort_values('total_estudiantes', ascending=False)
    concentracion['ranking'] = range(1, len(concentracion) + 1)
    
    logger.info(f"Métricas de concentración calculadas: {concentracion.shape[0]} departamentos")
    return concentracion


def analizar_movilidad_interdepartamental(df_movilidad: pd.DataFrame) -> pd.DataFrame:
    """
    Issue 6.4: Analiza flujos de movilidad interdepartamental
    
    Returns:
        DataFrame con análisis de flujos netos por departamento
    """
    logger.info("Analizando movilidad interdepartamental...")
    
    # Filtrar solo estudiantes que se mueven entre departamentos
    df_movilidad_interna = df_movilidad[df_movilidad['depto_residencia'] != df_movilidad['depto_ies']].copy()
    
    # Calcular flujos de salida (estudiantes que residen en X pero estudian en otro lado)
    flujos_salida = df_movilidad_interna.groupby('depto_residencia').agg(
        estudiantes_salida=('estu_consecutivo', 'nunique')
    ).reset_index().rename(columns={'depto_residencia': 'departamento'})
    
    # Calcular flujos de entrada (estudiantes que estudian en X pero residen en otro lado)
    flujos_entrada = df_movilidad_interna.groupby('depto_ies').agg(
        estudiantes_entrada=('estu_consecutivo', 'nunique')
    ).reset_index().rename(columns={'depto_ies': 'departamento'})
    
    # Unir flujos
    flujos = pd.merge(flujos_salida, flujos_entrada, on='departamento', how='outer').fillna(0)
    
    # Calcular flujo neto
    flujos['flujo_neto'] = flujos['estudiantes_entrada'] - flujos['estudiantes_salida']
    flujos['balance_movilidad'] = np.where(
        flujos['flujo_neto'] > 0, 'Importador', 'Exportador'
    )
    
    # Calcular porcentaje de movilidad
    total_por_depto = df_movilidad.groupby('depto_ies').agg(
        total_estudiantes=('estu_consecutivo', 'nunique')
    ).reset_index().rename(columns={'depto_ies': 'departamento'})
    
    flujos = pd.merge(flujos, total_por_depto, on='departamento', how='left')
    flujos['porcentaje_movilidad'] = (
        (flujos['estudiantes_salida'] + flujos['estudiantes_entrada']) / 
        flujos['total_estudiantes'] * 100
    )
    
    # Ordenar por flujo neto
    flujos = flujos.sort_values('flujo_neto', ascending=False)
    
    logger.info(f"Análisis de movilidad completado: {flujos.shape[0]} departamentos")
    return flujos


def top_rutas_movilidad(matriz_od: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """
    Issue 6.4: Identifica las top N rutas de movilidad más frecuentes
    
    Args:
        matriz_od: Matriz origen-destino
        n: Número de rutas a retornar
        
    Returns:
        DataFrame con las top N rutas
    """
    logger.info(f"Identificando top {n} rutas de movilidad...")
    
    # Filtrar solo movilidad interestatal
    matriz_interna = matriz_od[matriz_od['origen'] != matriz_od['destino']].copy()
    
    # Ordenar por total de estudiantes
    top_rutas = matriz_interna.nlargest(n, 'total_estudiantes')
    
    logger.info(f"Top {n} rutas identificadas")
    return top_rutas


def guardar_resultados_movilidad(matriz_od: pd.DataFrame, metricas: pd.DataFrame, 
                                 flujos: pd.DataFrame, top_rutas: pd.DataFrame,
                                 ruta_salida: str = "datos/processed"):
    """
    Guarda los resultados del análisis de movilidad
    """
    logger.info("Guardando resultados de movilidad...")
    
    ruta = Path(ruta_salida)
    ruta.mkdir(parents=True, exist_ok=True)
    
    # Guardar matriz origen-destino
    matriz_od.to_parquet(ruta / "matriz_origen_destino.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'matriz_origen_destino.parquet'}")
    
    # Guardar métricas de concentración
    metricas.to_parquet(ruta / "metricas_concentracion.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'metricas_concentracion.parquet'}")
    
    # Guardar flujos de movilidad
    flujos.to_parquet(ruta / "flujos_movilidad.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'flujos_movilidad.parquet'}")
    
    # Guardar top rutas
    top_rutas.to_parquet(ruta / "top_rutas_movilidad.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'top_rutas_movilidad.parquet'}")


def ejecutar_analisis_movilidad():
    """
    Función principal que ejecuta todo el pipeline de análisis de movilidad
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISIS DE MOVILIDAD ESTUDIANTIL")
    logger.info("=" * 60)
    
    # 1. Cargar datos
    saber_pro = cargar_datos_saber_pro()
    
    # 2. Preparar datos de movilidad
    df_movilidad = preparar_datos_movilidad(saber_pro)
    
    # 3. Crear matriz origen-destino
    matriz_od = crear_matriz_origen_destino(df_movilidad, nivel='departamento')
    
    # 4. Calcular métricas de concentración
    metricas = calcular_metricas_concentracion(df_movilidad)
    
    # 5. Analizar flujos de movilidad
    flujos = analizar_movilidad_interdepartamental(df_movilidad)
    
    # 6. Identificar top rutas
    top_rutas = top_rutas_movilidad(matriz_od, n=20)
    
    # 7. Guardar resultados
    guardar_resultados_movilidad(matriz_od, metricas, flujos, top_rutas)
    
    logger.info("=" * 60)
    logger.info("ANÁLISIS DE MOVILIDAD COMPLETADO EXITOSAMENTE")
    logger.info("=" * 60)
    
    return df_movilidad, matriz_od, metricas, flujos, top_rutas


if __name__ == "__main__":
    # Ejecutar análisis
    df_movilidad, matriz_od, metricas, flujos, top_rutas = ejecutar_analisis_movilidad()
    
    # Imprimir resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL ANÁLISIS DE MOVILIDAD")
    print("=" * 60)
    
    print(f"\nTotal estudiantes analizados: {df_movilidad['estu_consecutivo'].nunique():,}")
    print(f"Departamentos analizados: {metricas.shape[0]}")
    
    print(f"\nTop 5 departamentos con más estudiantes:")
    print(metricas[['depto_ies', 'total_estudiantes', 'porcentaje_nacional']].head().to_string(index=False))
    
    print(f"\nTop 5 departamentos importadores (flujo neto positivo):")
    importadores = flujos[flujos['balance_movilidad'] == 'Importador'].nlargest(5, 'flujo_neto')
    print(importadores[['departamento', 'flujo_neto', 'porcentaje_movilidad']].to_string(index=False))
    
    print(f"\nTop 5 departamentos exportadores (flujo neto negativo):")
    exportadores = flujos[flujos['balance_movilidad'] == 'Exportador'].nsmallest(5, 'flujo_neto')
    print(exportadores[['departamento', 'flujo_neto', 'porcentaje_movilidad']].to_string(index=False))
    
    print(f"\nTop 10 rutas de movilidad más frecuentes:")
    print(top_rutas[['origen', 'destino', 'total_estudiantes', 'porcentaje']].head(10).to_string(index=False))