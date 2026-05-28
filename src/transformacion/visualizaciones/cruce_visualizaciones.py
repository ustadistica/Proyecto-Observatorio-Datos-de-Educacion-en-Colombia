"""
Módulo de visualizaciones para el cruce Saber Pro - Graduados SNIES
Issues 6.1 y 6.2
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

# Configuración
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Estilo para matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("viridis")


def scatter_plot_puntaje_vs_graduados(cruce_ies: pd.DataFrame, anio: int = None, 
                                       guardar: bool = True, ruta_salida: str = "artifacts/visualizaciones"):
    """
    Issue 6.1: Gráfico de dispersión de puntaje promedio vs volumen de graduados
    
    Args:
        cruce_ies: DataFrame con cruce por IES
        anio: Año específico para filtrar (None = todos los años)
        guardar: Si True, guarda la figura
        ruta_salida: Ruta para guardar las visualizaciones
    """
    logger.info("Generando scatter plot de puntaje vs graduados...")
    
    # Filtrar por año si se especifica
    df = cruce_ies.copy()
    if anio:
        df = df[df['anio'] == anio]
        titulo = f'Puntaje Promedio vs Graduados ({anio})'
    else:
        titulo = 'Puntaje Promedio vs Graduados (Todos los años)'
    
    # Filtrar datos válidos
    df_valido = df.dropna(subset=['promedio_puntaje', 'total_graduados'])
    df_valido = df_valido[df_valido['total_graduados'] > 0]
    
    # Crear figura con Plotly para interactividad
    fig = px.scatter(
        df_valido,
        x='total_graduados',
        y='promedio_puntaje',
        hover_data=['nombre_ies', 'anio'],
        title=titulo,
        labels={
            'total_graduados': 'Número de Graduados',
            'promedio_puntaje': 'Puntaje Promedio Saber Pro'
        },
        opacity=0.6,
        size_max=10
    )
    
    fig.update_traces(marker=dict(color='royalblue', line=dict(width=1, color='DarkSlateBlue')))
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        template='plotly_white'
    )
    
    if guardar:
        ruta = Path(ruta_salida)
        ruta.mkdir(parents=True, exist_ok=True)
        nombre_archivo = f"scatter_puntaje_graduados_{anio if anio else 'todos'}.html"
        fig.write_html(ruta / nombre_archivo)
        logger.info(f"Gráfico guardado: {ruta / nombre_archivo}")
    
    return fig


def heatmap_correlaciones(cruce_ies: pd.DataFrame, anio: int = None,
                          guardar: bool = True, ruta_salida: str = "artifacts/visualizaciones"):
    """
    Issue 6.1: Mapa de calor de correlaciones entre variables
    """
    logger.info("Generando heatmap de correlaciones...")
    
    df = cruce_ies.copy()
    if anio:
        df = df[df['anio'] == anio]
    
    # Seleccionar variables numéricas
    variables = ['promedio_puntaje', 'total_graduados', 'total_presentados', 'tasa_presentacion', 'mediana_puntaje']
    df_corr = df[variables].dropna()
    
    # Calcular matriz de correlación
    corr_matrix = df_corr.corr()
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        corr_matrix,
        annot=True,
        cmap='coolwarm',
        center=0,
        fmt='.3f',
        linewidths=0.5,
        ax=ax,
        square=True,
        cbar_kws={"shrink": 0.8}
    )
    
    ax.set_title('Matriz de Correlación - Variables del Cruce', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    if guardar:
        ruta = Path(ruta_salida)
        ruta.mkdir(parents=True, exist_ok=True)
        nombre_archivo = f"heatmap_correlaciones_{anio if anio else 'todos'}.png"
        fig.savefig(ruta / nombre_archivo, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Heatmap guardado: {ruta / nombre_archivo}")
    
    return fig


def top_programas_barras(top_programas: pd.DataFrame, 
                         guardar: bool = True, ruta_salida: str = "artifacts/visualizaciones"):
    """
    Issue 6.2: Gráfico de barras del top 10 programas con mayor desfase
    """
    logger.info("Generando gráfico de barras de top programas...")
    
    # Preparar datos
    df = top_programas.copy()
    df['brecha_abs_total'] = df['brecha_total'].abs()
    
    # Ordenar
    df = df.sort_values('brecha_abs_total', ascending=True)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Barras horizontales
    bars = ax.barh(
        range(len(df)),
        df['brecha_abs_total'],
        color=plt.cm.viridis(np.linspace(0.2, 0.8, len(df)))
    )
    
    # Etiquetas
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df['programa_academico'], fontsize=9)
    ax.set_xlabel('Magnitud del Desfase (valor absoluto)', fontsize=12)
    ax.set_title('Top 10 Programas con Mayor Desfase entre Graduados y Presentados', fontsize=14, fontweight='bold')
    
    # Agregar valores en las barras
    for i, (bar, value) in enumerate(zip(bars, df['brecha_abs_total'])):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
                f'{value:,.0f}', va='center', fontsize=9)
    
    plt.tight_layout()
    
    if guardar:
        ruta = Path(ruta_salida)
        ruta.mkdir(parents=True, exist_ok=True)
        nombre_archivo = "top_programas_mayor_desfase.png"
        fig.savefig(ruta / nombre_archivo, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Gráfico guardado: {ruta / nombre_archivo}")
    
    return fig


def distribucion_tasa_presentacion(cruce_ies: pd.DataFrame, 
                                   guardar: bool = True, ruta_salida: str = "artifacts/visualizaciones"):
    """
    Issue 6.1/6.2: Distribución de la tasa de presentación
    """
    logger.info("Generando distribución de tasa de presentación...")
    
    df = cruce_ies.copy()
    df_valido = df.dropna(subset=['tasa_presentacion'])
    df_valido = df_valido[df_valido['total_graduados'] > 0]
    
    # Crear figura con subplot
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Histograma
    axes[0].hist(df_valido['tasa_presentacion'], bins=30, edgecolor='black', alpha=0.7, color='skyblue')
    axes[0].axvline(df_valido['tasa_presentacion'].mean(), color='red', linestyle='--', 
                    label=f'Media: {df_valido["tasa_presentacion"].mean():.2f}')
    axes[0].axvline(df_valido['tasa_presentacion'].median(), color='green', linestyle='--',
                    label=f'Mediana: {df_valido["tasa_presentacion"].median():.2f}')
    axes[0].set_xlabel('Tasa de Presentación (Presentados/Graduados)')
    axes[0].set_ylabel('Frecuencia')
    axes[0].set_title('Distribución de Tasa de Presentación')
    axes[0].legend()
    
    # Boxplot por año
    if 'anio' in df_valido.columns:
        años_muestra = sorted(df_valido['anio'].unique())[-5:]  # Últimos 5 años
        df_ultimos = df_valido[df_valido['anio'].isin(años_muestra)]
        df_ultimos.boxplot(column='tasa_presentacion', by='anio', ax=axes[1])
        axes[1].set_title('Tasa de Presentación por Año')
        axes[1].set_xlabel('Año')
        axes[1].set_ylabel('Tasa de Presentación')
        plt.suptitle('')  # Eliminar título automático
    
    plt.tight_layout()
    
    if guardar:
        ruta = Path(ruta_salida)
        ruta.mkdir(parents=True, exist_ok=True)
        nombre_archivo = "distribucion_tasa_presentacion.png"
        fig.savefig(ruta / nombre_archivo, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Gráfico guardado: {ruta / nombre_archivo}")
    
    return fig


def evolucion_temporal(cruce_ies: pd.DataFrame, 
                       guardar: bool = True, ruta_salida: str = "artifacts/visualizaciones"):
    """
    Issue 6.1: Evolución temporal de promedios y graduados
    """
    logger.info("Generando evolución temporal...")
    
    df = cruce_ies.copy()
    
    # Agrupar por año
    df_anual = df.groupby('anio').agg(
        promedio_puntaje=('promedio_puntaje', 'mean'),
        total_graduados=('total_graduados', 'sum'),
        total_presentados=('total_presentados', 'sum'),
        tasa_presentacion=('tasa_presentacion', 'mean')
    ).reset_index()
    
    # Crear figura con doble eje
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Eje 1: Puntaje promedio
    color = 'tab:blue'
    ax1.set_xlabel('Año')
    ax1.set_ylabel('Puntaje Promedio', color=color)
    line1 = ax1.plot(df_anual['anio'], df_anual['promedio_puntaje'], 
                     color=color, marker='o', linewidth=2, label='Puntaje Promedio')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)
    
    # Eje 2: Graduados
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Número de Graduados', color=color)
    line2 = ax2.bar(df_anual['anio'], df_anual['total_graduados'], 
                    alpha=0.3, color=color, label='Graduados')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Título
    plt.title('Evolución Temporal: Puntajes Saber Pro vs Graduados', fontsize=14, fontweight='bold')
    
    # Leyendas combinadas
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    
    if guardar:
        ruta = Path(ruta_salida)
        ruta.mkdir(parents=True, exist_ok=True)
        nombre_archivo = "evolucion_temporal_puntajes_graduados.png"
        fig.savefig(ruta / nombre_archivo, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Gráfico guardado: {ruta / nombre_archivo}")
    
    return fig


def generar_todas_las_visualizaciones():
    """
    Función principal para generar todas las visualizaciones
    """
    logger.info("=" * 60)
    logger.info("GENERANDO VISUALIZACIONES DEL CRUCE")
    logger.info("=" * 60)
    
    # Cargar datos
    logger.info("Cargando datos procesados...")
    ruta_base = Path("datos/processed")
    
    cruce_ies = pd.read_parquet(ruta_base / "cruce_saber_pro_graduados_ies.parquet")
    cruce_prog = pd.read_parquet(ruta_base / "cruce_saber_pro_graduados_programa.parquet")
    top_programas = pd.read_parquet(ruta_base / "top_programas_mayor_desfase.parquet")
    
    logger.info(f"Datos cargados: {cruce_ies.shape[0]} registros IES, {cruce_prog.shape[0]} registros programa")
    
    # Generar visualizaciones
    logger.info("Generando visualizaciones...")
    
    # 1. Scatter plot
    scatter_plot_puntaje_vs_graduados(cruce_ies, anio=None, guardar=True)
    
    # 2. Heatmap de correlaciones
    heatmap_correlaciones(cruce_ies, anio=None, guardar=True)
    
    # 3. Top programas
    top_programas_barras(top_programas, guardar=True)
    
    # 4. Distribución de tasa de presentación
    distribucion_tasa_presentacion(cruce_ies, guardar=True)
    
    # 5. Evolución temporal
    evolucion_temporal(cruce_ies, guardar=True)
    
    logger.info("=" * 60)
    logger.info("VISUALIZACIONES GENERADAS EXITOSAMENTE")
    logger.info("=" * 60)


if __name__ == "__main__":
    generar_todas_las_visualizaciones()