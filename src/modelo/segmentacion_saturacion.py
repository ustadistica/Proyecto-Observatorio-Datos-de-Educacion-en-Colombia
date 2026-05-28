"""
Módulo para Detección de Programas en Riesgo de Saturación
Sprint 7 - Issue 7.3: Detección y Agrupación de Programas Académicos en "Riesgo de Saturación"

Autor: Andrés
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
import logging
from datetime import datetime
from utils import (
    save_dbscan_model,
    create_experiment_metadata,
    save_metrics
)

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rutas
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATOS_DIR = PROJECT_ROOT / 'datos' / 'processed'
ARTIFACTS_DIR = PROJECT_ROOT / 'artifacts'
VISUALIZACIONES_DIR = ARTIFACTS_DIR / 'visualizaciones'

# Asegurar directorios
VISUALIZACIONES_DIR.mkdir(parents=True, exist_ok=True)


def cargar_datos_saturacion(ruta_base: str = "datos/processed"):
    """
    Carga datos para análisis de saturación de programas
    - Datos de correlación matrícula-rendimiento del Issue 6.5
    - O genera los datos desde las fuentes originales
    """
    logger.info("Cargando datos para análisis de saturación...")
    
    # Intentar cargar datos pre-procesados del Issue 6.5
    try:
        correlaciones = pd.read_parquet(Path(ruta_base) / "correlaciones_por_programa.parquet")
        logger.info(f"Correlaciones cargadas: {len(correlaciones)} programas")
    except FileNotFoundError:
        logger.warning("No se encontraron correlaciones pre-procesadas. Generando desde cero...")
        correlaciones = None
    
    # Cargar datos cruzados del Issue 6.5
    try:
        cruce = pd.read_parquet(Path(ruta_base) / "cruce_matricula_rendimiento.parquet")
        logger.info(f"Datos cruzados cargados: {len(cruce)} registros")
    except FileNotFoundError:
        logger.warning("No se encontraron datos cruzados. Creando dataset vacío...")
        cruce = pd.DataFrame()
    
    # Cargar Saber Pro para calcular crecimiento si es necesario
    try:
        saber_pro = pd.read_parquet(Path(ruta_base) / "saber_pro/saber_pro_consolidado.parquet")
        logger.info(f"Saber Pro cargado: {saber_pro.shape[0]:,} registros")
    except FileNotFoundError:
        saber_pro = None
    
    return correlaciones, cruce, saber_pro


def calcular_metricas_saturacion(cruce, saber_pro):
    """
    Calcula métricas de saturación para cada programa:
    - Crecimiento de matrícula acumulado
    - Cambio en puntajes (calidad)
    - Nivel actual de matrícula
    """
    logger.info("Calculando métricas de saturación...")
    
    if cruce.empty:
        logger.error("No hay datos cruzados disponibles. No se pueden calcular métricas.")
        return pd.DataFrame()
    
    # Asegurar que tenemos las columnas necesarias
    columnas_necesarias = ['codigo_snies_programa', 'programa_academico', 'nombre_ies', 
                          'anio', 'total_matriculados', 'promedio_puntaje']
    
    columnas_existentes = [col for col in columnas_necesarias if col in cruce.columns]
    
    if len(columnas_existentes) < len(columnas_necesarias):
        logger.warning(f"Faltan columnas necesarias. Encontradas: {columnas_existentes}")
        logger.warning(f"Columnas disponibles: {cruce.columns.tolist()}")
        return pd.DataFrame()
    
    # Verificar si ya existen las columnas calculadas (del Issue 6.5)
    if 'crecimiento_acumulado' in cruce.columns:
        logger.info("Columna crecimiento_acumulado encontrada")
        
        # Calcular cambio_puntaje si no existe
        if 'cambio_puntaje' not in cruce.columns:
            logger.info("Calculando cambio_puntaje...")
            cruce = cruce.sort_values(['codigo_snies_programa', 'anio'])
            cruce['puntaje_anterior'] = cruce.groupby('codigo_snies_programa')['promedio_puntaje'].shift(1)
            cruce['cambio_puntaje'] = cruce['promedio_puntaje'] - cruce['puntaje_anterior']
        
        # Usar datos directamente
        metricas_programas = cruce.groupby(['codigo_snies_programa', 'programa_academico', 'nombre_ies']).agg(
            crecimiento_acumulado=('crecimiento_acumulado', 'max'),
            cambio_puntaje_promedio=('cambio_puntaje', 'mean'),
            matricula_actual=('total_matriculados', 'max'),
            puntaje_actual=('promedio_puntaje', 'mean'),
            anios_analisis=('anio', 'nunique')
        ).reset_index()
        
        # Filtrar programas con al menos 3 años de datos
        metricas_programas = metricas_programas[metricas_programas['anios_analisis'] >= 3].copy()
        logger.info(f"Programas con métricas calculadas: {len(metricas_programas)}")
        return metricas_programas
    
    # Calcular crecimiento de matrícula por programa
    cruce = cruce.sort_values(['codigo_snies_programa', 'anio'])
    
    # Crecimiento acumulado (desde el primer año)
    cruce['primer_anio'] = cruce.groupby('codigo_snies_programa')['anio'].transform('min')
    cruce['matricula_inicial'] = cruce.groupby(['codigo_snies_programa', 'primer_anio'])['total_matriculados'].transform('first')
    cruce['crecimiento_acumulado'] = np.where(
        cruce['matricula_inicial'] > 0,
        (cruce['total_matriculados'] - cruce['matricula_inicial']) / cruce['matricula_inicial'] * 100,
        np.nan
    )
    
    # Cambio en puntajes (calidad)
    cruce['puntaje_anterior'] = cruce.groupby('codigo_snies_programa')['promedio_puntaje'].shift(1)
    cruce['cambio_puntaje'] = cruce['promedio_puntaje'] - cruce['puntaje_anterior']
    
    # Obtener último año por programa
    ultimo_anio = cruce.groupby('codigo_snies_programa')['anio'].max().reset_index()
    ultimo_anio = ultimo_anio.rename(columns={'anio': 'ultimo_anio'})
    
    # Datos del último año
    datos_ultimo = cruce[cruce['anio'] == cruce.groupby('codigo_snies_programa')['anio'].transform('max')].copy()
    
    # Agregar métricas por programa
    metricas_programas = datos_ultimo.groupby(['codigo_snies_programa', 'programa_academico', 'nombre_ies']).agg(
        crecimiento_acumulado=('crecimiento_acumulado', 'max'),
        cambio_puntaje_promedio=('cambio_puntaje', 'mean'),
        matricula_actual=('total_matriculados', 'max'),
        puntaje_actual=('promedio_puntaje', 'mean'),
        anios_analisis=('anio', 'nunique')
    ).reset_index()
    
    # Filtrar programas con al menos 3 años de datos
    metricas_programas = metricas_programas[metricas_programas['anios_analisis'] >= 3].copy()
    
    logger.info(f"Programas con métricas calculadas: {len(metricas_programas)}")
    
    return metricas_programas


def aplicar_dbscan(metricas, eps=0.5, min_samples=5):
    """
    Aplica DBSCAN para detectar programas atípicos (riesgo de saturación)
    """
    logger.info(f"Aplicando DBSCAN (eps={eps}, min_samples={min_samples})...")
    
    # Features para clustering
    feature_cols = ['crecimiento_acumulado', 'cambio_puntaje_promedio', 'matricula_actual']
    
    # Verificar columnas
    feature_cols = [col for col in feature_cols if col in metricas.columns]
    
    if len(feature_cols) < 2:
        logger.error(f"Se necesitan al menos 2 features. Encontradas: {feature_cols}")
        return None, None, feature_cols
    
    # Estandarizar
    X = metricas[feature_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Aplicar DBSCAN
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(X_scaled)
    
    # Contar clusters y outliers
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_outliers = list(labels).count(-1)
    
    logger.info(f"DBSCAN completado: {n_clusters} clusters, {n_outliers} outliers")
    
    return dbscan, scaler, feature_cols


def clasificar_programas(metricas, dbscan, scaler, feature_cols):
    """
    Clasifica programas en tres estados:
    - Crecimiento Sostenible
    - Madurez/Estabilidad
    - Alerta de Saturación por Pérdida de Calidad
    """
    logger.info("Clasificando programas...")
    
    X = metricas[feature_cols].values
    X_scaled = scaler.transform(X)
    
    # Predecir clusters
    metricas['cluster_dbscan'] = dbscan.fit_predict(X_scaled)
    
    # Clasificación basada en reglas
    def asignar_estado(row):
        crecimiento = row['crecimiento_acumulado']
        cambio_puntaje = row['cambio_puntaje_promedio']
        
        # Alerta de Saturación: alto crecimiento + caída de puntajes
        if crecimiento > 50 and cambio_puntaje < -10:
            return 'Alerta de Saturación'
        
        # Crecimiento Sostenible: crecimiento moderado + puntajes estables/mejorando
        elif 0 < crecimiento <= 50 and cambio_puntaje >= -5:
            return 'Crecimiento Sostenible'
        
        # Madurez/Estabilidad: bajo crecimiento + puntajes estables
        elif -10 <= crecimiento <= 10 and -5 <= cambio_puntaje <= 5:
            return 'Madurez/Estabilidad'
        
        # Casos especiales
        elif crecimiento > 50 and cambio_puntaje >= 0:
            return 'Crecimiento Sostenible'  # Crecimiento sin pérdida de calidad
        
        elif crecimiento < -10:
            return 'En Declive'  # Programa en contracción
        
        else:
            return 'Otros'
    
    metricas['estado'] = metricas.apply(asignar_estado, axis=1)
    
    # Distribución
    distribucion = metricas['estado'].value_counts()
    logger.info(f"Distribución de estados:\n{distribucion}")
    
    return metricas


def visualizar_clusters_saturacion(metricas, feature_cols, guardar=True):
    """
    Genera visualización de clusters de saturación
    """
    logger.info("Generando visualización de clusters...")
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Scatter: Crecimiento vs Cambio de Puntaje
    scatter1 = axes[0].scatter(
        metricas['crecimiento_acumulado'],
        metricas['cambio_puntaje_promedio'],
        c=metricas['cluster_dbscan'],
        cmap='viridis',
        alpha=0.6,
        s=50,
        edgecolors='white'
    )
    axes[0].set_xlabel('Crecimiento Acumulado (%)', fontsize=12)
    axes[0].set_ylabel('Cambio Promedio de Puntaje', fontsize=12)
    axes[0].set_title('Programas por Crecimiento vs Calidad', fontsize=13, fontweight='bold')
    axes[0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    axes[0].axvline(x=0, color='gray', linestyle='--', alpha=0.5)
    axes[0].grid(alpha=0.3)
    plt.colorbar(scatter1, ax=axes[0], label='Cluster')
    
    # Scatter: Crecimiento vs Matrícula Actual
    scatter2 = axes[1].scatter(
        metricas['matricula_actual'],
        metricas['crecimiento_acumulado'],
        c=metricas['estado'].map({
            'Alerta de Saturación': 'red',
            'Crecimiento Sostenible': 'green',
            'Madurez/Estabilidad': 'blue',
            'En Declive': 'orange',
            'Otros': 'gray'
        }),
        alpha=0.6,
        s=50,
        edgecolors='white'
    )
    axes[1].set_xlabel('Matrícula Actual', fontsize=12)
    axes[1].set_ylabel('Crecimiento Acumulado (%)', fontsize=12)
    axes[1].set_title('Programas por Tamaño vs Crecimiento', fontsize=13, fontweight='bold')
    axes[1].grid(alpha=0.3)
    
    # Leyenda personalizada
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Alerta de Saturación'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='Crecimiento Sostenible'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Madurez/Estabilidad'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=10, label='En Declive'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label='Otros')
    ]
    axes[1].legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    
    if guardar:
        ruta = VISUALIZACIONES_DIR / f'saturacion_clusters_{datetime.now().strftime("%Y%m%d")}.png'
        plt.savefig(ruta, dpi=150, bbox_inches='tight')
        logger.info(f"Gráfico guardado: {ruta}")
    
    plt.show()
    return ruta if guardar else None


def ejecutar_segmentacion_completa():
    """
    Función principal que ejecuta todo el pipeline de segmentación de saturación
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISIS DE SATURACIÓN DE PROGRAMAS")
    logger.info("=" * 60)
    
    # 1. Cargar datos
    correlaciones, cruce, saber_pro = cargar_datos_saturacion()
    
    # 2. Calcular métricas de saturación
    metricas = calcular_metricas_saturacion(cruce, saber_pro)
    
    if metricas.empty:
        logger.error("No se pudieron calcular métricas. Verificando datos de entrada...")
        return None, None, None
    
    # 3. Aplicar DBSCAN
    dbscan, scaler, feature_cols = aplicar_dbscan(metricas, eps=0.5, min_samples=5)
    
    if dbscan is None:
        logger.error("DBSCAN no pudo ser aplicado.")
        return None, None, None
    
    # 4. Clasificar programas
    metricas = clasificar_programas(metricas, dbscan, scaler, feature_cols)
    
    # 5. Visualizar
    ruta_viz = visualizar_clusters_saturacion(metricas, feature_cols)
    
    # 6. Guardar modelo
    metadata = create_experiment_metadata(
        experiment_name="DBSCAN Saturación de Programas",
        model_type="DBSCAN",
        description="Detección de programas académicos en riesgo de saturación por crecimiento de matrícula",
        author="Andrés",
        issue="Sprint 7.3",
        hyperparameters={
            "eps": 0.5,
            "min_samples": 5
        },
        metrics={
            "n_clusters": int(len(set(metricas['cluster_dbscan'])) - (1 if -1 in metricas['cluster_dbscan'].values else 0)),
            "n_outliers": int((metricas['cluster_dbscan'] == -1).sum()),
            "distribucion_estados": metricas['estado'].value_counts().to_dict()
        },
        data_info={
            "n_programas": len(metricas),
            "features": feature_cols,
            "periodo": "2015-2024"
        }
    )
    
    saved_files = save_dbscan_model(dbscan, scaler, feature_cols, metadata)
    
    # 7. Guardar dataset con etiquetas
    output_path = DATOS_DIR / "programas_con_cluster_saturacion.parquet"
    metricas.to_parquet(output_path, index=False)
    logger.info(f"Dataset con clusters guardado: {output_path}")
    
    # 8. Imprimir resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL ANÁLISIS DE SATURACIÓN")
    print("=" * 60)
    print(f"\nTotal programas analizados: {len(metricas)}")
    print(f"\nDistribución por estado:")
    print(metricas['estado'].value_counts())
    
    # Programas en alerta
    alertas = metricas[metricas['estado'] == 'Alerta de Saturación']
    if not alertas.empty:
        print(f"\n{'='*60}")
        print("PROGRAMAS EN ALERTA DE SATURACIÓN:")
        print(f"{'='*60}")
        columns_to_show = ['programa_academico', 'nombre_ies', 'crecimiento_acumulado', 
                          'cambio_puntaje_promedio', 'matricula_actual']
        print(alertas[columns_to_show].head(20).to_string(index=False))
    
    logger.info("=" * 60)
    logger.info("ANÁLISIS DE SATURACIÓN COMPLETADO EXITOSAMENTE")
    logger.info("=" * 60)
    
    return metricas, dbscan, scaler


if __name__ == "__main__":
    metricas, dbscan, scaler = ejecutar_segmentacion_completa()