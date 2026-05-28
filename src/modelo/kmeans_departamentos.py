"""
Módulo para Segmentación de Departamentos mediante K-Means
Sprint 7 - Issue 7.2: Segmentación de Departamentos según Brechas y Dinámica Educativa

Autor: Andrés
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import logging
from datetime import datetime
from utils import (
    save_kmeans_model,
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


def cargar_datos_departamentales(ruta_base: str = "datos/processed"):
    """
    Carga y consolida datos a nivel departamental para clustering
    """
    logger.info("Cargando datos departamentales...")
    
    # 1. Cargar métricas de concentración (del Issue 6.4)
    try:
        metricas_concentracion = pd.read_parquet(Path(ruta_base) / "metricas_concentracion.parquet")
        logger.info(f"Métricas de concentración cargadas: {len(metricas_concentracion)} departamentos")
    except FileNotFoundError:
        logger.warning("No se encontraron métricas de concentración. Generando desde Saber Pro...")
        # Generar métricas básicas desde Saber Pro
        saber_pro = pd.read_parquet(Path(ruta_base) / "saber_pro/saber_pro_consolidado.parquet")
        
        # Determinar columna de departamento
        col_depto = 'depto_ies' if 'depto_ies' in saber_pro.columns else 'depto_presentacion'
        
        metricas_concentracion = saber_pro.groupby(col_depto).agg(
            total_estudiantes=('estu_consecutivo', 'nunique'),
            promedio_puntaje=('puntaje_global', 'mean'),
            promedio_lectura_critica=('punt_lectura_critica', 'mean'),
            promedio_razona_cuantitativa=('punt_razona_cuantitativa', 'mean'),
            promedio_ingles=('punt_ingles', 'mean')
        ).reset_index()
        
        metricas_concentracion = metricas_concentracion.rename(columns={col_depto: 'departamento'})
    
    # 2. Cargar flujos de movilidad (del Issue 6.4)
    try:
        flujos_movilidad = pd.read_parquet(Path(ruta_base) / "flujos_movilidad.parquet")
        flujos_movilidad = flujos_movilidad[['departamento', 'flujo_neto', 'porcentaje_movilidad']]
        logger.info(f"Flujos de movilidad cargados: {len(flujos_movilidad)} departamentos")
    except FileNotFoundError:
        logger.warning("No se encontraron flujos de movilidad. Usando datos básicos...")
        flujos_movilidad = pd.DataFrame(columns=['departamento', 'flujo_neto', 'porcentaje_movilidad'])
    
    # 3. Cargar datos PTE (presupuesto) - si existen
    try:
        pte_data = pd.read_parquet(Path(ruta_base) / "pte_departamental.parquet")
        pte_data = pte_data.groupby('departamento').agg(
            presupuesto_ejecutado=('monto_ejecutado', 'sum'),
            presupuesto_total=('monto_total', 'sum')
        ).reset_index()
        pte_data['ejecucion_presupuestal'] = (pte_data['presupuesto_ejecutado'] / pte_data['presupuesto_total'] * 100)
        logger.info(f"Datos PTE cargados: {len(pte_data)} departamentos")
    except FileNotFoundError:
        logger.warning("No se encontraron datos PTE. Continuando sin presupuesto...")
        pte_data = pd.DataFrame(columns=['departamento', 'ejecucion_presupuestal'])
    
    return metricas_concentracion, flujos_movilidad, pte_data


def consolidar_datos_departamentales(metricas, flujos, pte):
    """
    Consolida todos los datos departamentales en un solo DataFrame
    """
    logger.info("Consolidando datos departamentales...")
    
    # Renombrar columnas para统一 - metricas usa 'depto_ies', flujos usa 'departamento'
    metricas_renamed = metricas.rename(columns={'depto_ies': 'departamento'})
    
    # Unir métricas con flujos
    df_deptos = pd.merge(metricas_renamed, flujos, on='departamento', how='left')
    
    # Unir con PTE
    if not pte.empty:
        df_deptos = pd.merge(df_deptos, pte[['departamento', 'ejecucion_presupuestal']], 
                            on='departamento', how='left')
    
    # Rellenar valores faltantes con la mediana
    columnas_numericas = df_deptos.select_dtypes(include=[np.number]).columns
    for col in columnas_numericas:
        if df_deptos[col].isnull().any():
            mediana = df_deptos[col].median()
            df_deptos[col] = df_deptos[col].fillna(mediana)
            logger.info(f"  {col}: {df_deptos[col].isnull().sum()} NaN rellenados con mediana ({mediana:.2f})")
    
    logger.info(f"Departamentos consolidados: {len(df_deptos)}")
    logger.info(f"Columnas: {df_deptos.columns.tolist()}")
    
    return df_deptos


def seleccionar_features_clustering(df_deptos):
    """
    Selecciona las features para clustering
    """
    logger.info("Seleccionando features para clustering...")
    
    # Features disponibles (ajustar según datos reales)
    features_possibles = [
        'promedio_puntaje',           # Calidad educativa
        'promedio_lectura_critica',   # Competencia específica
        'promedio_razona_cuantitativa', # Competencia específica
        'promedio_ingles',            # Competencia específica
        'flujo_neto',                 # Atracción/exportación de estudiantes
        'porcentaje_movilidad',       # Intensidad de movilidad
        'ejecucion_presupuestal',     # Eficiencia presupuestal (si existe)
    ]
    
    # Seleccionar solo las que existen
    features = [f for f in features_possibles if f in df_deptos.columns]
    
    logger.info(f"Features seleccionadas: {features}")
    
    return features


def determinar_k_optimo(X_scaled, k_max=10):
    """
    Determina el K óptimo usando método del codo y silhouette score
    """
    logger.info(f"Determinando K óptimo (2 a {k_max})...")
    
    k_range = range(2, k_max + 1)
    inertias = []
    silhouette_scores = []
    davies_bouldin_scores = []
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(X_scaled)
        
        inertias.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(X_scaled, labels))
        davies_bouldin_scores.append(davies_bouldin_score(X_scaled, labels))
    
    # Seleccionar K óptimo (mejor silhouette score)
    k_optimo = k_range[np.argmax(silhouette_scores)]
    
    logger.info(f"K óptimo seleccionado: {k_optimo}")
    logger.info(f"Mejor Silhouette Score: {max(silhouette_scores):.3f}")
    logger.info(f"Mejor Davies-Bouldin: {min(davies_bouldin_scores):.3f}")
    
    return k_optimo, k_range, inertias, silhouette_scores, davies_bouldin_scores


def visualizar_k_optimo(k_range, inertias, silhouette_scores, davies_bouldin_scores, guardar=True):
    """
    Genera gráfico para determinación de K óptimo
    """
    logger.info("Generando gráfico de K óptimo...")
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Método del codo
    axes[0].plot(k_range, inertias, 'bo-', linewidth=2, markersize=8)
    axes[0].set_xlabel('Número de Clusters (K)', fontsize=12)
    axes[0].set_ylabel('Inertia (WCSS)', fontsize=12)
    axes[0].set_title('Método del Codo', fontsize=13, fontweight='bold')
    axes[0].grid(alpha=0.3)
    
    # Silhouette Score
    axes[1].plot(k_range, silhouette_scores, 'go-', linewidth=2, markersize=8)
    axes[1].set_xlabel('Número de Clusters (K)', fontsize=12)
    axes[1].set_ylabel('Silhouette Score', fontsize=12)
    axes[1].set_title('Silhouette Score por K', fontsize=13, fontweight='bold')
    axes[1].axhline(y=0.5, color='r', linestyle='--', label='Umbral 0.5')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    # Davies-Bouldin Index
    axes[2].plot(k_range, davies_bouldin_scores, 'ro-', linewidth=2, markersize=8)
    axes[2].set_xlabel('Número de Clusters (K)', fontsize=12)
    axes[2].set_ylabel('Davies-Bouldin Index', fontsize=12)
    axes[2].set_title('Davies-Bouldin Index por K', fontsize=13, fontweight='bold')
    axes[2].grid(alpha=0.3)
    
    plt.tight_layout()
    
    if guardar:
        ruta = VISUALIZACIONES_DIR / f'kmeans_k_optimo_{datetime.now().strftime("%Y%m%d")}.png'
        plt.savefig(ruta, dpi=150, bbox_inches='tight')
        logger.info(f"Gráfico guardado: {ruta}")
    
    plt.show()
    return ruta if guardar else None


def visualizar_coordenadas_paralelas(df_deptos, feature_cols, cluster_col='cluster', guardar=True):
    """
    Genera gráfico de coordenadas paralelas para caracterización de clusters
    """
    logger.info("Generando gráfico de coordenadas paralelas...")
    
    # Normalizar datos para visualización
    df_viz = df_deptos[feature_cols + [cluster_col]].copy()
    
    # Estandarizar por columna
    for col in feature_cols:
        df_viz[col] = (df_viz[col] - df_viz[col].mean()) / df_viz[col].std()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Colores para cada cluster
    n_clusters = df_viz[cluster_col].nunique()
    colors = plt.cm.Set1(np.linspace(0, 1, n_clusters))
    
    # Trazar líneas para cada departamento
    for idx, row in df_viz.iterrows():
        cluster_idx = int(row[cluster_col])
        ax.plot(feature_cols, row[feature_cols], 
               color=colors[cluster_idx], alpha=0.3, linewidth=1)
    
    # Trazar medias por cluster
    means = df_viz.groupby(cluster_col)[feature_cols].mean()
    for cluster_idx, row in means.iterrows():
        ax.plot(feature_cols, row, 'o-', linewidth=3, markersize=10,
               color=colors[cluster_idx], label=f'Cluster {cluster_idx}')
    
    ax.set_xlabel('Features', fontsize=12)
    ax.set_ylabel('Valor Estandarizado', fontsize=12)
    ax.set_title('Coordenadas Paralelas - Caracterización de Clusters', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    
    if guardar:
        ruta = VISUALIZACIONES_DIR / f'kmeans_coordenadas_paralelas_{datetime.now().strftime("%Y%m%d")}.png'
        plt.savefig(ruta, dpi=150, bbox_inches='tight')
        logger.info(f"Gráfico guardado: {ruta}")
    
    plt.show()
    return ruta if guardar else None


def ejecutar_kmeans_completo():
    """
    Función principal que ejecuta todo el pipeline de K-Means departamental
    """
    logger.info("=" * 60)
    logger.info("INICIANDO K-MEANS PARA SEGMENTACIÓN DEPARTAMENTAL")
    logger.info("=" * 60)
    
    # 1. Cargar datos
    metricas, flujos, pte = cargar_datos_departamentales()
    
    # 2. Consolidar datos
    df_deptos = consolidar_datos_departamentales(metricas, flujos, pte)
    
    # 3. Seleccionar features
    feature_cols = seleccionar_features_clustering(df_deptos)
    
    if len(feature_cols) < 2:
        raise ValueError(f"Se necesitan al menos 2 features, pero solo se encontraron {len(feature_cols)}")
    
    # 4. Estandarizar datos
    X = df_deptos[feature_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 5. Determinar K óptimo
    k_optimo, k_range, inertias, silhouette_scores, davies_bouldin_scores = determinar_k_optimo(X_scaled)
    
    # 6. Visualizar K óptimo
    ruta_k_optimo = visualizar_k_optimo(k_range, inertias, silhouette_scores, davies_bouldin_scores)
    
    # 7. Entrenar K-Means final
    logger.info(f"Entrenando K-Means con K={k_optimo}...")
    kmeans = KMeans(n_clusters=k_optimo, random_state=42, n_init=20, max_iter=500)
    df_deptos['cluster'] = kmeans.fit_predict(X_scaled)
    
    # Métricas finales
    silh_final = silhouette_score(X_scaled, df_deptos['cluster'])
    db_final = davies_bouldin_score(X_scaled, df_deptos['cluster'])
    ch_final = calinski_harabasz_score(X_scaled, df_deptos['cluster'])
    
    logger.info(f"Métricas finales: Silhouette={silh_final:.3f}, DB={db_final:.3f}, CH={ch_final:.1f}")
    
    # 8. Visualizar coordenadas paralelas
    ruta_coordenadas = visualizar_coordenadas_paralelas(df_deptos, feature_cols)
    
    # 9. Guardar modelo
    metadata = create_experiment_metadata(
        experiment_name="K-Means Departamentos",
        model_type="KMeans",
        description="Segmentación de departamentos según brechas y dinámica educativa",
        author="Andrés",
        issue="Sprint 7.2",
        hyperparameters={
            "n_clusters": k_optimo,
            "random_state": 42,
            "n_init": 20,
            "max_iter": 500
        },
        metrics={
            "silhouette_score": float(silh_final),
            "davies_bouldin_index": float(db_final),
            "calinski_harabasz_score": float(ch_final)
        },
        data_info={
            "n_departamentos": len(df_deptos),
            "n_features": len(feature_cols),
            "features": feature_cols,
            "periodo": "2015-2024"
        }
    )
    
    saved_files = save_kmeans_model(kmeans, scaler, feature_cols, metadata)
    
    # 10. Guardar dataset con clusters
    output_path = DATOS_DIR / "departamentos_con_cluster.parquet"
    df_deptos.to_parquet(output_path, index=False)
    logger.info(f"Dataset con clusters guardado: {output_path}")
    
    # 11. Imprimir perfiles de clusters
    print("\n" + "=" * 60)
    print("PERFILES DE CLUSTERS")
    print("=" * 60)
    perfiles = df_deptos.groupby('cluster')[feature_cols].mean()
    print(perfiles.round(2))
    
    print("\n" + "=" * 60)
    print("DISTRIBUCIÓN DE DEPARTAMENTOS POR CLUSTER")
    print("=" * 60)
    print(df_deptos['cluster'].value_counts().sort_index())
    
    logger.info("=" * 60)
    logger.info("K-MEANS DEPARTAMENTAL COMPLETADO EXITOSAMENTE")
    logger.info("=" * 60)
    
    return df_deptos, kmeans, scaler, feature_cols, metadata


if __name__ == "__main__":
    df_deptos, kmeans, scaler, feature_cols, metadata = ejecutar_kmeans_completo()