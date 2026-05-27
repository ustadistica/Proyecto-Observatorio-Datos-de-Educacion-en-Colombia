"""
Módulo para Análisis de Componentes Principales (PCA) de Competencias Saber Pro
Sprint 7 - Issue 7.1: Reducción Dimensional de Competencias Saber Pro mediante PCA

Autor: Jhonatan
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
import logging
from datetime import datetime
from utils import (
    save_pca_model, 
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


def cargar_datos_saber_pro(ruta_base: str = "datos/processed"):
    """
    Carga los datos de Saber Pro para análisis de PCA
    """
    logger.info("Cargando datos de Saber Pro para PCA...")
    saber_pro = pd.read_parquet(Path(ruta_base) / "saber_pro/saber_pro_consolidado.parquet")
    logger.info(f"Saber Pro cargado: {saber_pro.shape[0]:,} registros")
    return saber_pro


def preparar_datos_pca(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara los datos para PCA:
    - Agrega puntajes promedio por programa académico e IES
    - Filtra IES con al menos 100 presentaciones
    """
    logger.info("Preparando datos para PCA...")
    
    # Columnas de competencias genéricas (módulos Saber Pro)
    # Nombres originales y alternativos
    columnas_competencias_map = {
        'mod_comuni_escrita_punt': 'Comunicación Escrita',
        'mod_lectura_critica_punt': 'Lectura Crítica',
        'mod_razona_cuantitat_punt': 'Razonamiento Cuantitativo',
        'mod_competen_ciudada_punt': 'Competencias Ciudadanas',
        'mod_ingles_punt': 'Inglés',
        # Alternativas (nombres antiguos)
        'punt_comuni_escrita': 'Comunicación Escrita',
        'punt_lectura_critica': 'Lectura Crítica',
        'punt_razona_cuantitativa': 'Razonamiento Cuantitativo',
        'punt_comp_ciudadanas': 'Competencias Ciudadanas',
        'punt_ingles': 'Inglés',
    }
    
    # Verificar qué columnas existen en el dataset
    columnas_existentes = []
    for col_original in columnas_competencias_map.keys():
        if col_original in df.columns:
            columnas_existentes.append(col_original)
    
    # Si no se encuentran las columnas nuevas, intentar con las antiguas
    if len(columnas_existentes) < 3:
        columnas_existentes = [col for col in columnas_competencias_map.keys() if col in df.columns]
    
    if len(columnas_existentes) < 3:
        raise ValueError(f"Se necesitan al menos 3 competencias, pero solo se encontraron {len(columnas_existentes)}")
    
    logger.info(f"Competencias encontradas: {columnas_existentes}")
    
    # Agregar por programa académico e IES
    # Nombres correctos de columnas en el dataset
    df_agg = df.groupby(['inst_nombre_institucion', 'estu_snies_prgmacademico']).agg(
        **{col: (col, 'mean') for col in columnas_existentes},
        n_presentaciones=('estu_consecutivo', 'nunique')
    ).reset_index()
    
    # Renombrar columnas para compatibilidad
    df_agg = df_agg.rename(columns={
        'inst_nombre_institucion': 'nombre_ies',
        'estu_snies_prgmacademico': 'programa_academico'
    })
    
    # Filtrar programas con al menos 30 presentaciones (para estabilidad)
    df_agg = df_agg[df_agg['n_presentaciones'] >= 30].copy()
    
    logger.info(f"Programas después de filtrar (>= 30 presentaciones): {len(df_agg)}")
    
    return df_agg, columnas_existentes


def aplicar_pca(df: pd.DataFrame, columnas_competencias: list, n_components: int = None):
    """
    Aplica PCA a las competencias
    """
    logger.info("Aplicando PCA...")
    
    # Extraer features
    X = df[columnas_competencias].values
    
    # Estandarizar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Determinar número de componentes
    if n_components is None:
        # Usar criterio de varianza acumulada > 80%
        n_components = min(len(columnas_competencias), 5)
    
    # Aplicar PCA
    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    
    # Varianza explicada
    varianza_explicada = pca.explained_variance_ratio_
    varianza_acumulada = np.cumsum(varianza_explicada)
    
    logger.info(f"PCA aplicado: {n_components} componentes")
    logger.info(f"Varianza explicada por componente: {varianza_explicada}")
    logger.info(f"Varianza acumulada (PC1+PC2): {varianza_acumulada[1]:.2%}")
    
    return pca, scaler, X_pca, X_scaled, varianza_explicada, varianza_acumulada


def visualizar_varianza_explicada(varianza_explicada, varianza_acumulada, guardar=True):
    """
    Genera gráfico de varianza explicada (gráfico de codo)
    """
    logger.info("Generando gráfico de varianza explicada...")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Barplot de varianza por componente
    axes[0].bar(range(1, len(varianza_explicada)+1), varianza_explicada, 
                color='steelblue', edgecolor='black')
    axes[0].set_xlabel('Componente Principal', fontsize=12)
    axes[0].set_ylabel('Varianza Explicada', fontsize=12)
    axes[0].set_title('Varianza Explicada por Componente', fontsize=13, fontweight='bold')
    axes[0].set_xticks(range(1, len(varianza_explicada)+1))
    axes[0].grid(axis='y', alpha=0.3)
    
    # Varianza acumulada
    axes[1].plot(range(1, len(varianza_acumulada)+1), varianza_acumulada, 
                 'o-', color='darkgreen', linewidth=2, markersize=8)
    axes[1].axhline(y=0.8, color='r', linestyle='--', label='80% varianza')
    axes[1].set_xlabel('Número de Componentes', fontsize=12)
    axes[1].set_ylabel('Varianza Acumulada', fontsize=12)
    axes[1].set_title('Varianza Acumulada', fontsize=13, fontweight='bold')
    axes[1].set_xticks(range(1, len(varianza_acumulada)+1))
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    
    if guardar:
        ruta = VISUALIZACIONES_DIR / f'pca_varianza_explicada_{datetime.now().strftime("%Y%m%d")}.png'
        plt.savefig(ruta, dpi=150, bbox_inches='tight')
        logger.info(f"Gráfico guardado: {ruta}")
    
    plt.show()
    return ruta if guardar else None


def visualizar_scatter_pca(X_pca, df, varianza_explicada, componente_x=0, componente_y=1, guardar=True):
    """
    Genera scatter plot 2D de los componentes principales
    """
    logger.info("Generando scatter plot PCA 2D...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Scatter por defecto (todos del mismo color)
    scatter = ax.scatter(X_pca[:, componente_x], X_pca[:, componente_y], 
                         alpha=0.6, s=50, c='steelblue', edgecolors='white')
    
    pc1_var = varianza_explicada[componente_x]*100 if componente_x < len(varianza_explicada) else 0
    pc2_var = varianza_explicada[componente_y]*100 if componente_y < len(varianza_explicada) else 0
    
    ax.set_xlabel(f'PC1 ({pc1_var:.1f}% varianza)', fontsize=12)
    ax.set_ylabel(f'PC2 ({pc2_var:.1f}% varianza)', fontsize=12)
    ax.set_title('Scatter Plot PCA: Programas Académicos en Espacio 2D', fontsize=14, fontweight='bold')
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    
    if guardar:
        ruta = VISUALIZACIONES_DIR / f'pca_scatter_2d_{datetime.now().strftime("%Y%m%d")}.png'
        plt.savefig(ruta, dpi=150, bbox_inches='tight')
        logger.info(f"Gráfico guardado: {ruta}")
    
    plt.show()
    return ruta if guardar else None


def visualizar_scatter_pca_por_area(X_pca, df, varianza_explicada, columna_color='area_conocimiento', guardar=True):
    """
    Scatter plot coloreado por área de conocimiento o tipo de IES
    """
    logger.info(f"Generando scatter plot PCA coloreado por {columna_color}...")
    
    # Verificar si la columna existe
    if columna_color not in df.columns:
        logger.warning(f"Columna '{columna_color}' no encontrada. Usando scatter simple.")
        return visualizar_scatter_pca(X_pca, df, guardar=guardar)
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Obtener valores únicos de la columna de color
    colores = df[columna_color].unique()
    
    # Mapear colores
    cmap = plt.cm.get_cmap('tab20', len(colores))
    
    for i, valor in enumerate(sorted(colores)):
        mask = df[columna_color] == valor
        if mask.sum() > 0:
            ax.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                      alpha=0.6, s=50, c=[cmap(i)], 
                      label=str(valor), edgecolors='white', linewidth=0.5)
    
    ax.set_xlabel(f'PC1 ({varianza_explicada[0]*100:.1f}% varianza)', fontsize=12)
    ax.set_ylabel(f'PC2 ({varianza_explicada[1]*100:.1f}% varianza)', fontsize=12)
    ax.set_title(f'PCA por {columna_color.replace("_", " ").title()}', fontsize=14, fontweight='bold')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    
    if guardar:
        ruta = VISUALIZACIONES_DIR / f'pca_scatter_por_{columna_color}_{datetime.now().strftime("%Y%m%d")}.png'
        plt.savefig(ruta, dpi=150, bbox_inches='tight')
        logger.info(f"Gráfico guardado: {ruta}")
    
    plt.show()
    return ruta if guardar else None


def ejecutar_pca_completo():
    """
    Función principal que ejecuta todo el pipeline de PCA
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISIS PCA DE COMPETENCIAS SABER PRO")
    logger.info("=" * 60)
    
    # 1. Cargar datos
    df = cargar_datos_saber_pro()
    
    # 2. Preparar datos
    df_agg, columnas_competencias = preparar_datos_pca(df)
    
    # 3. Aplicar PCA
    pca, scaler, X_pca, X_scaled, varianza_explicada, varianza_acumulada = aplicar_pca(
        df_agg, columnas_competencias, n_components=min(5, len(columnas_competencias))
    )
    
    # 4. Visualizar varianza explicada
    ruta_varianza = visualizar_varianza_explicada(varianza_explicada, varianza_acumulada)
    
    # 5. Visualizar scatter 2D
    ruta_scatter = visualizar_scatter_pca(X_pca, df_agg, varianza_explicada, guardar=True)
    
    # 6. Visualizar scatter por área (si existe la columna)
    if 'area_conocimiento' in df_agg.columns:
        ruta_scatter_area = visualizar_scatter_pca_por_area(
            X_pca, df_agg, varianza_explicada, 'area_conocimiento'
        )
    
    # 7. Guardar modelo
    metadata = create_experiment_metadata(
        experiment_name="PCA Competencias Saber Pro",
        model_type="PCA",
        description="Análisis de Componentes Principales para competencias genéricas de Saber Pro",
        author="Jhonatan",
        issue="Sprint 7.1",
        hyperparameters={
            "n_components": pca.n_components_,
            "random_state": 42
        },
        metrics={
            "varianza_explicada_pc1": float(varianza_explicada[0]),
            "varianza_explicada_pc2": float(varianza_explicada[1]),
            "varianza_acumulada_pc1_pc2": float(varianza_acumulada[1]),
            "varianza_total_explicada": float(varianza_acumulada[-1])
        },
        data_info={
            "n_programas": len(df_agg),
            "n_competencias": len(columnas_competencias),
            "competencias": columnas_competencias,
            "filtro_min_presentaciones": 30,
            "periodo": "2015-2024"
        }
    )
    
    saved_files = save_pca_model(pca, scaler, columnas_competencias, metadata)
    
    # 8. Guardar métricas adicionales
    metrics_file = save_metrics(metadata['metricas'], 'metricas_pca')
    
    logger.info("=" * 60)
    logger.info("PCA COMPLETADO EXITOSAMENTE")
    logger.info("=" * 60)
    
    print("\n" + "=" * 60)
    print("RESUMEN DEL ANÁLISIS PCA")
    print("=" * 60)
    print(f"\nProgramas analizados: {len(df_agg)}")
    print(f"Competencias: {len(columnas_competencias)}")
    print(f"Varianza PC1: {varianza_explicada[0]*100:.1f}%")
    print(f"Varianza PC2: {varianza_explicada[1]*100:.1f}%")
    print(f"Varianza acumulada PC1+PC2: {varianza_acumulada[1]*100:.1f}%")
    print(f"\nArchivos guardados:")
    for key, path in saved_files.items():
        print(f"  {key}: {path}")
    
    return df_agg, pca, scaler, X_pca, varianza_explicada


if __name__ == "__main__":
    df_agg, pca, scaler, X_pca, varianza_explicada = ejecutar_pca_completo()