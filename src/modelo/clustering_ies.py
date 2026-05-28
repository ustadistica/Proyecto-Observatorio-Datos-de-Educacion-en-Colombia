#!/usr/bin/env python3
"""
clustering_ies.py - Issue 7.2: Clustering IES por Desempeño
===========================================================
Clustering de instituciones de educación superior usando:
  - Puntajes promedio Saber Pro por IES
  - Métricas SNIES (graduados, matriculados, tasa graduación)
  - Proporción de estudiantes en P75+ (alto desempeño)

Salidas:
  - Modelo: artifacts/modelos/clasificacion_ies_cluster_YYYYMMDD.pkl
  - Métricas: artifacts/metricas/metricas_clustering_YYYYMMDD.json
  - Visualización: artifacts/visualizaciones/clusters_ies_2d_YYYYMMDD.png

Autor: German Chamorro
Fecha: 2026-05-17
"""

from pathlib import Path
from datetime import datetime
import json
import pickle

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SABER_PRO_PATH = PROJECT_ROOT / "datos" / "processed" / "saber_pro" / "saber_pro_consolidado.parquet"
SNIES_GRAD_PATH = PROJECT_ROOT / "datos" / "processed" / "snies" / "snies_graduados_limpio_consolidado.parquet"
SNIES_MATRIC_PATH = PROJECT_ROOT / "datos" / "processed" / "snies" / "snies_matriculados_limpio_consolidado.parquet"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODELOS_DIR = ARTIFACTS_DIR / "modelos"
METRICAS_DIR = ARTIFACTS_DIR / "metricas"
VIZ_DIR = ARTIFACTS_DIR / "visualizaciones"

FECHA = datetime.now().strftime("%Y%m%d")

# Parámetros del clustering
N_CLUSTERS = 4  # Ajustar según análisis del elbow
RANDOM_STATE = 42

# ============================================================================
# FUNCIONES
# ============================================================================

def cargar_datos():
    """
    Carga y prepara los datos de Saber Pro y SNIES.
    
    Returns:
        pd.DataFrame: DataFrame consolidado por IES
    """
    print("📥 Cargando datos...")
    
    # Saber Pro
    df_sp = pd.read_parquet(SABER_PRO_PATH)
    print(f"   Saber Pro: {len(df_sp):,} registros")
    
    # SNIES Graduados
    df_grad = pd.read_parquet(SNIES_GRAD_PATH)
    print(f"   SNIES Graduados: {len(df_grad):,} registros")
    
    # SNIES Matriculados (opcional para features adicionales)
    df_matric = pd.read_parquet(SNIES_MATRIC_PATH)
    print(f"   SNIES Matriculados: {len(df_matric):,} registros")
    
    return df_sp, df_grad, df_matric


def crear_features_ies(df_sp, df_grad, df_matric):
    """
    Crea features agregadas por IES para el clustering.
    
    Features:
      - Puntaje global promedio
      - Puntajes por módulo (razonamiento, lectura, inglés)
      - Número de presentaciones
      - Proporción en P75+ (percentil 75 superior)
      - Número de graduados (de SNIES)
      - Tasa de graduación (si disponible)
    
    Returns:
        pd.DataFrame: Features por IES
    """
    print("\n🔧 Creando features por IES...")
    
    # TODO: Implementar lógica de agregación
    # Ejemplo básico:
    
    # Puntajes promedio por IES
    features_sp = df_sp.groupby('inst_nombre_institucion').agg({
        'puntaje_global': 'mean',
        'punt_razona_cuantitativa': 'mean',
        'punt_lectura_critica': 'mean',
        'punt_ingles': 'mean',
        'estu_consecutivo': 'count'  # Número de presentaciones
    }).rename(columns={'estu_consecutivo': 'n_presentaciones'})
    
    # Calcular proporción en P75+
    p75_global = df_sp['puntaje_global'].quantile(0.75)
    prop_p75 = df_sp.groupby('inst_nombre_institucion').apply(
        lambda x: (x['puntaje_global'] >= p75_global).mean()
    ).rename('prop_p75_plus')
    
    features_sp = features_sp.join(prop_p75)
    
    # Agregar graduados de SNIES (si tienen match)
    # TODO: Implementar join con SNIES
    
    print(f"   Features creadas para {len(features_sp)} IES")
    return features_sp


def entrenar_clustering(X, n_clusters=N_CLUSTERS):
    """
    Entrena modelo de clustering K-means.
    
    Args:
        X: Features normalizadas
        n_clusters: Número de clusters
    
    Returns:
        tuple: (modelo, scaler, métricas)
    """
    print(f"\n🤖 Entrenando K-means con {n_clusters} clusters...")
    
    # Normalización
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    # Métricas
    metricas = {
        "silhouette_score": float(silhouette_score(X_scaled, labels)),
        "davies_bouldin_index": float(davies_bouldin_score(X_scaled, labels)),
        "calinski_harabasz_score": float(calinski_harabasz_score(X_scaled, labels)),
        "inertia": float(kmeans.inertia_)
    }
    
    print(f"   Silhouette Score: {metricas['silhouette_score']:.3f}")
    print(f"   Davies-Bouldin Index: {metricas['davies_bouldin_index']:.3f}")
    print(f"   Calinski-Harabasz Score: {metricas['calinski_harabasz_score']:.1f}")
    
    return kmeans, scaler, labels, metricas


def visualizar_clusters(X, labels, feature_names):
    """
    Visualiza clusters en 2D usando PCA.
    
    Args:
        X: Features originales
        labels: Etiquetas de cluster
        feature_names: Nombres de features
    
    Returns:
        matplotlib.figure.Figure
    """
    print("\n📊 Generando visualización...")
    
    # PCA a 2 componentes
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    X_pca = pca.fit_transform(X)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, cmap='viridis', 
                         s=100, alpha=0.6, edgecolors='k')
    
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} varianza)', fontsize=12)
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} varianza)', fontsize=12)
    ax.set_title('Clustering de IES - Proyección PCA 2D', fontsize=14, fontweight='bold')
    
    # Leyenda
    handles, _ = scatter.legend_elements()
    labels_legend = [f'Cluster {i}' for i in range(len(handles))]
    ax.legend(handles, labels_legend, title='Clusters', loc='best')
    
    ax.grid(alpha=0.3)
    plt.tight_layout()
    
    return fig


def guardar_resultados(modelo, scaler, labels, metricas, feature_names):
    """
    Guarda modelo, métricas y visualizaciones.
    
    Args:
        modelo: Modelo K-means entrenado
        scaler: Scaler usado para normalización
        labels: Etiquetas de cluster
        metricas: Diccionario de métricas
        feature_names: Nombres de features
    """
    print("\n💾 Guardando resultados...")
    
    # Guardar modelo
    modelo_path = MODELOS_DIR / f"clasificacion_ies_cluster_{FECHA}.pkl"
    with open(modelo_path, 'wb') as f:
        pickle.dump({'modelo': modelo, 'scaler': scaler}, f)
    print(f"   Modelo guardado: {modelo_path}")
    
    # Guardar métricas
    metricas_completas = {
        "metadata": {
            "modelo": "kmeans_ies_desempeno",
            "fecha_entrenamiento": datetime.now().isoformat(),
            "autor": "German",
            "issue": "Sprint 7.2 - Clustering IES por desempeño"
        },
        "hiperparametros": {
            "algoritmo": "KMeans",
            "n_clusters": N_CLUSTERS,
            "random_state": RANDOM_STATE
        },
        "metricas_clustering": metricas,
        "features_utilizadas": feature_names
    }
    
    metricas_path = METRICAS_DIR / f"metricas_clustering_{FECHA}.json"
    with open(metricas_path, 'w') as f:
        json.dump(metricas_completas, f, indent=2)
    print(f"   Métricas guardadas: {metricas_path}")


def main():
    """Función principal del pipeline de clustering."""
    print("="*70)
    print("CLUSTERING DE IES POR DESEMPEÑO - Sprint 7.2")
    print("="*70)
    
    # 1. Cargar datos
    df_sp, df_grad, df_matric = cargar_datos()
    
    # 2. Crear features
    features_df = crear_features_ies(df_sp, df_grad, df_matric)
    
    # 3. Preparar matriz de features
    X = features_df.values
    feature_names = features_df.columns.tolist()
    
    # 4. Entrenar clustering
    modelo, scaler, labels, metricas = entrenar_clustering(X)
    
    # 5. Visualizar
    fig = visualizar_clusters(StandardScaler().fit_transform(X), labels, feature_names)
    viz_path = VIZ_DIR / f"clusters_ies_2d_{FECHA}.png"
    fig.savefig(viz_path, dpi=150, bbox_inches='tight')
    print(f"   Visualización guardada: {viz_path}")
    plt.close(fig)
    
    # 6. Guardar resultados
    guardar_resultados(modelo, scaler, labels, metricas, feature_names)
    
    print("\n✅ Pipeline completado exitosamente!")
    print(f"   Revisa artifacts/ para ver los resultados.")


if __name__ == "__main__":
    main()
