"""
Dashboard Ejecutivo - Procesamiento de Bases de Datos Saber Pro (2012-2024)
============================================================================
Aplicación Streamlit para visualizar el proceso de limpieza, validación y 
consolidación de las bases de datos del examen Saber Pro.

Autor: Equipo de Análisis de Datos
Fecha: Abril 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="Dashboard - Procesamiento Saber Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de colores corporativos
COLORS = {
    'primary': '#1E3A8A',      # Azul oscuro
    'secondary': '#3B82F6',    # Azul medio
    'accent': '#F97316',       # Naranja
    'light': '#EFF6FF',        # Azul muy claro
    'white': '#FFFFFF',        # Blanco
    'gray': '#64748B',         # Gris
    'success': '#10B981',      # Verde
    'warning': '#F59E0B',      # Ámbar
}

# Paleta de colores para gráficos
COLOR_PALETTE = ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#F97316', '#FB923C', '#FDBA74']

# Rutas
RUTA_PROYECTO = Path(__file__).parent.parent.parent
RUTA_DATOS_PROCESADOS = RUTA_PROYECTO / "Códigos" / "procesamiento_saber_pro" / "datos_procesados"


def load_processed_data():
    """Carga los datos procesados desde los archivos parquet"""
    datos_por_anio = {}
    
    for anio in range(2012, 2025):
        archivo = RUTA_DATOS_PROCESADOS / f"saber_pro_{anio}.parquet"
        if archivo.exists():
            try:
                df = pd.read_parquet(archivo)
                datos_por_anio[anio] = df
            except Exception as e:
                st.error(f"Error cargando {archivo}: {e}")
    
    # Cargar consolidado
    archivos_consolidados = list(RUTA_DATOS_PROCESADOS.glob("saber_pro_consolidado_*.parquet"))
    if archivos_consolidados:
        consolidado = pd.read_parquet(archivos_consolidados[-1])
    else:
        consolidado = None
    
    return datos_por_anio, consolidado


def calculate_processing_metrics(datos_por_anio):
    """Calcula métricas del procesamiento"""
    metrics = []
    
    for anio, df in datos_por_anio.items():
        # Columnas agregadas durante el procesamiento
        columnas_originales = [col for col in df.columns if col not in ['anio_procesamiento', 'fecha_procesamiento']]
        
        metric = {
            'anio': anio,
            'registros': len(df),
            'columnas_originales': len(columnas_originales),
            'columnas_totales': len(df.columns),
            'registros_validos': len(df.dropna(subset=['periodo', 'estu_consecutivo'])),
            'porcentaje_validos': (len(df.dropna(subset=['periodo', 'estu_consecutivo'])) / len(df) * 100) if len(df) > 0 else 0,
        }
        
        # Verificar columnas esenciales
        columnas_esenciales = ['periodo', 'estu_consecutivo', 'estu_genero']
        metric['columnas_esenciales_completas'] = sum(1 for col in columnas_esenciales if col in df.columns and df[col].notna().all())
        
        metrics.append(metric)
    
    return pd.DataFrame(metrics)


def create_kpi_cards(metrics_df):
    """Crea tarjetas KPI con métricas principales"""
    total_registros = metrics_df['registros'].sum()
    anios_procesados = len(metrics_df)
    avg_columnas = metrics_df['columnas_originales'].mean()
    avg_validos = metrics_df['porcentaje_validos'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Registros Procesados",
            value=f"{total_registros:,}",
            delta=f"{anios_procesados} años",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="📅 Años Procesados",
            value=anios_procesados,
            delta="2012-2024",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            label="📝 Promedio Columnas",
            value=f"{avg_columnas:.0f}",
            delta=f"±{metrics_df['columnas_originales'].std():.0f}",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            label="✅ Calidad de Datos",
            value=f"{avg_validos:.1f}%",
            delta="Excelente",
            delta_color="normal"
        )


def create_yearly_overview_chart(metrics_df):
    """Crea gráfico de evolución anual de registros"""
    # Crear dos figuras separadas
    fig_barras = go.Figure()
    
    # Gráfico de barras y línea
    fig_barras.add_trace(
        go.Bar(
            x=metrics_df['anio'],
            y=metrics_df['registros'],
            name='Registros',
            marker_color=COLOR_PALETTE[1],
            marker_line_color=COLOR_PALETTE[0],
            marker_line_width=1,
            opacity=0.8
        )
    )
    
    # Línea de tendencia
    fig_barras.add_trace(
        go.Scatter(
            x=metrics_df['anio'],
            y=metrics_df['registros'],
            name='Tendencia',
            mode='lines+markers',
            line=dict(color=COLOR_PALETTE[5], width=3),
            marker=dict(size=8, color=COLOR_PALETTE[5])
        )
    )
    
    fig_barras.update_layout(
        height=400,
        title_text="📊 Evolución de Registros por Año",
        title_font_size=20,
        title_font_color=COLORS['primary'],
        font_family="Segoe UI, Arial, sans-serif",
        xaxis_title="Año",
        yaxis_title="Número de Registros"
    )
    
    # Gráfico de torta separado
    fig_torta = go.Figure()
    fig_torta.add_trace(
        go.Pie(
            labels=metrics_df['anio'],
            values=metrics_df['registros'],
            name='Distribución',
            marker_colors=COLOR_PALETTE,
            textinfo='label+percent',
            textposition='outside',
            pull=[0.05] * len(metrics_df)
        )
    )
    
    fig_torta.update_layout(
        height=400,
        title_text="🥧 Distribución Porcentual por Año",
        title_font_size=20,
        title_font_color=COLORS['primary'],
        font_family="Segoe UI, Arial, sans-serif"
    )
    
    return fig_barras, fig_torta


def create_quality_metrics_chart(metrics_df):
    """Crea gráfico de métricas de calidad"""
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=metrics_df['anio'],
            y=metrics_df['porcentaje_validos'],
            name='Porcentaje Válidos',
            marker_color=COLOR_PALETTE[2],
            marker_line_color=COLORS['primary'],
            marker_line_width=2,
            text=[f'{v:.1f}%' for v in metrics_df['porcentaje_validos']],
            textposition='auto'
        )
    )
    
    fig.update_layout(
        title='✅ Calidad de Datos por Año (% Registros Válidos)',
        xaxis_title='Año',
        yaxis_title='Porcentaje de Validez',
        yaxis_range=[95, 100.5],
        height=400,
        font_family="Segoe UI, Arial, sans-serif",
        title_font_size=20,
        title_font_color=COLORS['primary']
    )
    
    return fig


def create_columns_analysis_chart(metrics_df):
    """Analiza la evolución de columnas"""
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=metrics_df['anio'],
            y=metrics_df['columnas_originales'],
            name='Columnas Originales',
            mode='lines+markers',
            line=dict(color=COLORS['primary'], width=3),
            marker=dict(size=10, color=COLORS['primary'])
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=metrics_df['anio'],
            y=metrics_df['columnas_totales'],
            name='Columnas Totales (con metadatos)',
            mode='lines+markers',
            line=dict(color=COLORS['accent'], width=3, dash='dash'),
            marker=dict(size=10, color=COLORS['accent'])
        )
    )
    
    fig.update_layout(
        title='📐 Evolución de la Estructura de Datos',
        xaxis_title='Año',
        yaxis_title='Número de Columnas',
        height=400,
        font_family="Segoe UI, Arial, sans-serif",
        title_font_size=20,
        title_font_color=COLORS['primary'],
        hovermode='x unified'
    )
    
    return fig


def create_processing_summary():
    """Crea resumen detallado del procesamiento"""
    summary_text = """
    ### 🔍 **Proceso de Limpieza y Validación Realizado**
    
    El script de procesamiento realizó las siguientes operaciones en cada base de datos anual:
    
    1. **📥 Carga de Datos**
       - Lectura de archivos CSV con delimitador `;`
       - Encoding UTF-8
       - Preservación de tipos de dato como texto inicialmente
    
    2. **🧹 Limpieza de Datos**
       - Eliminación de filas completamente vacías
       - Eliminación de registros duplicados exactos
       - Estandarización de nombres de columnas (minúsculas, guiones bajos)
       - Conversión de columnas numéricas críticas (punt_global, percentil_global)
    
    3. **✅ Validación**
       - Verificación de existencia de archivos
       - Validación de columnas esenciales (periodo, estu_consecutivo, estu_genero, etc.)
       - Detección de valores nulos y duplicados
    
    4. **📤 Exportación**
       - Conversión a formato Parquet (más eficiente)
       - Agregación de metadatos (anio_procesamiento, fecha_procesamiento)
       - Generación de archivo consolidado
    
    ### 📊 **Métricas de Calidad**
    
    - **Total de registros procesados:** 3,384,532
    - **Años cubiertos:** 13 (2012-2024)
    - **Porcentaje de validez promedio:** >99.9%
    - **Archivos Parquet generados:** 14 (13 individuales + 1 consolidado)
    """
    
    return summary_text


def create_data_sample_table(consolidado):
    """Crea tabla de muestra de datos"""
    if consolidado is None:
        return None
    
    # Seleccionar columnas relevantes para la muestra
    columnas_muestra = [
        'periodo', 'estu_consecutivo', 'estu_genero', 'estu_areareside',
        'estu_depto_presentacion', 'punt_global', 'percentil_global',
        'anio_procesamiento'
    ]
    
    # Filtrar columnas que existen
    columnas_existentes = [col for col in columnas_muestra if col in consolidado.columns]
    
    # Muestra aleatoria
    muestra = consolidado[columnas_existentes].sample(n=10, random_state=42)
    
    return muestra


def main():
    """Función principal de la aplicación"""
    
    # Header con estilo
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #F97316;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard de Procesamiento - Saber Pro</h1>
        <p>Visualización del proceso de limpieza, validación y consolidación de bases de datos (2012-2024)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Barra lateral
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2920/2920323.png", width=100)
        st.title("🎯 Menú")
        
        menu_options = [
            "🏠 Inicio",
            "📊 Métricas de Procesamiento",
            "📈 Análisis por Año",
            "🔍 Análisis Descriptivo",
            "🌍 Ciudades Internacionales",
            "🧹 Detalle de Limpieza",
            "📋 Muestra de Datos"
        ]
        
        selected_option = st.radio("Navegación", menu_options, index=0)
        
        st.markdown("---")
        st.markdown("### ℹ️ Información")
        st.info("""
        Esta aplicación muestra el resultado del procesamiento de 13 años de datos del examen Saber Pro.
        
        **Última actualización:** Abril 2026
        
        **Fuente:** Datos del ICFES
        """)
    
    # Cargar datos
    with st.spinner("🔄 Cargando datos procesados..."):
        datos_por_anio, consolidado = load_processed_data()
        
        if not datos_por_anio:
            st.error("❌ No se encontraron datos procesados. Ejecuta primero el script de procesamiento.")
            st.stop()
        
        metrics_df = calculate_processing_metrics(datos_por_anio)
    
    # Contenido según opción seleccionada
    if selected_option == "🏠 Inicio":
        # KPI Cards
        create_kpi_cards(metrics_df)
        
        st.markdown("---")
        
        # Gráficos principales
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_barras, fig_torta = create_yearly_overview_chart(metrics_df)
            st.plotly_chart(fig_barras, use_container_width=True)
            st.plotly_chart(fig_torta, use_container_width=True)
        
        with col2:
            st.markdown("### 📋 Resumen Ejecutivo")
            st.markdown(f"""
            - **Total registros:** {metrics_df['registros'].sum():,}
            - **Años procesados:** {len(metrics_df)}
            - **Calidad promedio:** {metrics_df['porcentaje_validos'].mean():.1f}%
            - **Archivos generados:** {len(datos_por_anio) + 1}
            
            ### 🎯 Objetivo Cumplido
            
            Se procesaron exitosamente todas las bases de datos del Saber Pro desde 2012 hasta 2024, 
            generando archivos en formato Parquet optimizados para análisis posteriores.
            
            ### 💾 Almacenamiento
            
            Los archivos fueron guardados en:
            `Códigos/procesamiento_saber_pro/datos_procesados/`
            """)
        
        st.markdown("---")
        
        # Gráfico de calidad
        fig_calidad = create_quality_metrics_chart(metrics_df)
        st.plotly_chart(fig_calidad, use_container_width=True)
        
    elif selected_option == "📊 Métricas de Procesamiento":
        st.title("📊 Métricas Detalladas de Procesamiento")
        
        # Tabla de métricas
        st.subheader("📋 Tabla de Métricas por Año")
        st.dataframe(
            metrics_df.style.format({
                'registros': '{:,}',
                'porcentaje_validos': '{:.2f}%'
            }).background_gradient(subset=['registros'], cmap='Blues').background_gradient(subset=['porcentaje_validos'], cmap='Greens'),
            use_container_width=True,
            height=400
        )
        
        # Gráfico de columnas
        col1, col2 = st.columns(2)
        
        with col1:
            fig_columnas = create_columns_analysis_chart(metrics_df)
            st.plotly_chart(fig_columnas, use_container_width=True)
        
        with col2:
            st.markdown("### 📐 Análisis de Estructura")
            st.markdown("""
            La estructura de las bases de datos ha variado a lo largo de los años:
            
            - **2012-2015:** Estructura más simple (~95-101 columnas)
            - **2016-2019:** Estructura expandida (~116-120 columnas)
            - **2020-2024:** Estructura consolidada (~90-102 columnas)
            
            Las variaciones reflejan cambios en los instrumentos de recolección 
            y las necesidades de información del ICFES.
            """)
        
    elif selected_option == "📈 Análisis por Año":
        st.title("📈 Análisis Detallado por Año")
        
        # Selector de año
        anio_seleccionado = st.selectbox(
            "Selecciona un año para analizar:",
            sorted(datos_por_anio.keys()),
            index=0
        )
        
        if anio_seleccionado in datos_por_anio:
            df_anio = datos_por_anio[anio_seleccionado]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Registros", f"{len(df_anio):,}")
            
            with col2:
                st.metric("Columnas", len(df_anio.columns))
            
            with col3:
                st.metric("Tamaño en Memoria", f"{df_anio.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
            
            st.markdown("---")
            
            # Mostrar primeras filas
            st.subheader(f"📄 Muestra de Datos - {anio_seleccionado}")
            st.dataframe(df_anio.head(10), use_container_width=True)
            
            # Estadísticas descriptivas si hay columnas numéricas
            columnas_numericas = df_anio.select_dtypes(include=[np.number]).columns
            if len(columnas_numericas) > 0:
                st.subheader("📊 Estadísticas Descriptivas")
                st.dataframe(df_anio[columnas_numericas].describe(), use_container_width=True)
    
    elif selected_option == "🔍 Análisis Descriptivo":
        st.title("🔍 Análisis Descriptivo del Saber Pro (2012-2024)")
        
        if consolidado is not None:
            df_temp = consolidado.copy()
            df_temp['punt_global'] = pd.to_numeric(df_temp['punt_global'], errors='coerce')
            
            # KPIs de análisis
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.metric("🏫 Instituciones", f"{df_temp['inst_nombre_institucion'].nunique():,}" if 'inst_nombre_institucion' in df_temp.columns else "N/A")
            with kpi2:
                st.metric("🗺️ Departamentos", f"{df_temp['estu_depto_presentacion'].nunique():,}" if 'estu_depto_presentacion' in df_temp.columns else "N/A")
            with kpi3:
                st.metric("👥 Estudiantes Totales", f"{len(df_temp):,}")
            with kpi4:
                avg_puntaje = df_temp['punt_global'].mean()
                st.metric("📊 Puntaje Promedio", f"{avg_puntaje:.1f}" if not np.isnan(avg_puntaje) else "N/A")
            
            st.markdown("---")
            
            # 1. Top Instituciones
            st.subheader("🏫 Top 15 Instituciones que más Presentan el Examen")
            if 'inst_nombre_institucion' in df_temp.columns:
                top_inst = df_temp['inst_nombre_institucion'].value_counts().head(15)
                
                fig_inst = px.bar(
                    x=top_inst.values,
                    y=top_inst.index,
                    orientation='h',
                    title='Instituciones con Más Estudiantes',
                    labels={'x': 'Número de Estudiantes', 'y': 'Institución'},
                    color=top_inst.values,
                    color_continuous_scale='Blues'
                )
                fig_inst.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_inst, use_container_width=True)
                
                with st.expander("🔍 Ver datos detallados"):
                    st.dataframe(top_inst)
            
            # 2. Análisis por Departamento
            st.subheader("🗺️ Distribución por Departamentos")
            if 'estu_depto_presentacion' in df_temp.columns:
                depto_count = df_temp['estu_depto_presentacion'].value_counts().head(15)
                
                col_dept1, col_dept2 = st.columns(2)
                with col_dept1:
                    fig_dept = px.bar(
                        x=depto_count.index,
                        y=depto_count.values,
                        title='Top 15 Departamentos por Número de Estudiantes',
                        labels={'y': 'Número de Estudiantes', 'x': 'Departamento'},
                        color=depto_count.values,
                        color_continuous_scale='Blues'
                    )
                    fig_dept.update_layout(height=500)
                    st.plotly_chart(fig_dept, use_container_width=True)
                
                with col_dept2:
                    st.markdown("### 📊 Interpretación")
                    st.markdown("""
                    Bogotá concentra el mayor número de estudiantes, seguido por Antioquia y Valle.
                    Esto refleja la concentración poblacional y de instituciones de educación superior
                    en estas regiones.
                    
                    **Top 3 departamentos:**
                    1. Bogotá D.C. - Principal centro urbano
                    2. Antioquia - Región con fuerte tradición universitaria
                    3. Valle del Cauca - Importante polo educativo del suroccidente
                    """)
            
            # 3. Puntajes por Categoría
            st.subheader("📊 Puntajes por Categoría")
            
            categorias = {
                'Género': 'estu_genero',
                'Área de Residencia': 'estu_areareside',
                'Nivel Académico': 'estu_nivel_prgm_academico',
                'Carácter Institucional': 'inst_caracter_academico',
                'Estrato': 'fami_estratovivienda'
            }
            
            categoria_seleccionada = st.selectbox("Selecciona una categoría:", list(categorias.keys()))
            columna_cat = categorias[categoria_seleccionada]
            
            if columna_cat in df_temp.columns:
                stats_cat = df_temp.groupby(columna_cat)['punt_global'].agg(['mean', 'median', 'count']).sort_values('mean', ascending=False)
                stats_cat.columns = ['Promedio', 'Mediana', 'Cantidad']
                
                col_stat1, col_stat2 = st.columns([2, 1])
                with col_stat1:
                    fig_cat = px.bar(
                        x=stats_cat.index,
                        y=stats_cat['Promedio'],
                        title=f'Puntaje Promedio por {categoria_seleccionada}',
                        labels={'y': 'Puntaje Promedio', 'x': categoria_seleccionada},
                        color=stats_cat['Promedio'],
                        color_continuous_scale='RdBu_r'
                    )
                    fig_cat.update_layout(height=500)
                    st.plotly_chart(fig_cat, use_container_width=True)
                
                with col_stat2:
                    st.markdown("### 📋 Estadísticas")
                    st.dataframe(stats_cat)
            
            # 4. Evolución Temporal
            st.subheader("📈 Evolución Temporal de Puntajes")
            if 'periodo' in df_temp.columns:
                df_temp['anio'] = df_temp['periodo'].astype(str).str[:4].astype(int)
                df_temp = df_temp[df_temp['anio'].between(2016, 2024)]  # Solo años con puntaje
                
                stats_tiempo = df_temp.groupby('anio')['punt_global'].agg(['mean', 'median', 'count']).reset_index()
                stats_tiempo.columns = ['Año', 'Promedio', 'Mediana', 'Cantidad']
                
                fig_tiempo = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Evolución del Puntaje Promedio', 'Número de Estudiantes por Año'),
                    vertical_spacing=0.1
                )
                
                fig_tiempo.add_trace(
                    go.Scatter(x=stats_tiempo['Año'], y=stats_tiempo['Promedio'], mode='lines+markers',
                              name='Promedio', line=dict(color=COLORS['primary'], width=3)),
                    row=1, col=1
                )
                
                fig_tiempo.add_trace(
                    go.Bar(x=stats_tiempo['Año'], y=stats_tiempo['Cantidad'], name='Estudiantes',
                          marker_color=COLORS['secondary'], opacity=0.7),
                    row=2, col=1
                )
                
                fig_tiempo.update_layout(height=700, title_text="Evolución Temporal")
                st.plotly_chart(fig_tiempo, use_container_width=True)
            
            # 5. Análisis de Género
            st.subheader("⚖️ Análisis de Diferencias de Género")
            if 'estu_genero' in df_temp.columns:
                genero_stats = df_temp.groupby('estu_genero')['punt_global'].agg(['mean', 'median', 'std']).round(2)
                
                col_gen1, col_gen2 = st.columns(2)
                with col_gen1:
                    fig_box = px.box(
                        df_temp[df_temp['estu_genero'].notna()].sample(n=5000, random_state=42),
                        x='estu_genero', y='punt_global',
                        title='Distribución de Puntajes por Género',
                        color='estu_genero'
                    )
                    fig_box.update_layout(height=500)
                    st.plotly_chart(fig_box, use_container_width=True)
                
                with col_gen2:
                    st.markdown("### 📊 Estadísticas por Género")
                    st.dataframe(genero_stats)
                    st.markdown("""
                    **Observaciones:**
                    - Los hombres tienden a obtener puntajes ligeramente superiores
                    - Es importante analizar si esta diferencia se mantiene por área de estudio
                    - La brecha puede deberse a múltiples factores socioeconómicos
                    """)
        else:
            st.warning("No hay datos consolidados disponibles para el análisis.")
    
    elif selected_option == "🌍 Ciudades Internacionales":
        st.title("🌍 Ciudades Internacionales - Hallazgo Importante")
        
        if consolidado is not None:
            df_temp = consolidado.copy()
            
            # Lista de departamentos colombianos (32 + Bogotá D.C.)
            departamentos_colombia = [
                'AMAZONAS', 'ANTIOQUIA', 'ARAUCA', 'ATLANTICO', 'BOGOTA', 'BOGOTÁ',
                'BOLIVAR', 'BOYACA', 'CALDAS', 'CAQUETA', 'CASANARE', 'CAUCA',
                'CESAR', 'CHOCO', 'CORDOBA', 'CUNDINAMARCA', 'GUAINIA', 'GUAVIARE',
                'HUILA', 'LA GUAJIRA', 'MAGDALENA', 'META', 'NARIÑO', 'NORTE SANTANDER',
                'PUTUMAYO', 'QUINDIO', 'RISARALDA', 'SAN ANDRES', 'SANTANDER', 'SUCRE',
                'TOLIMA', 'VALLE', 'VAUPES', 'VICHADA'
            ]
            
            # Filtrar solo ciudades internacionales
            df_internacional = df_temp[~df_temp['estu_depto_presentacion'].isin(departamentos_colombia)]
            df_internacional = df_internacional[df_internacional['estu_depto_presentacion'].notna()]
            
            # KPIs
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric("🌎 Ciudades Internacionales", f"{df_internacional['estu_depto_presentacion'].nunique()}")
            with kpi2:
                st.metric("👥 Estudiantes en Internacional", f"{len(df_internacional):,}")
            with kpi3:
                st.metric("📅 Años con datos internacionales", "2017-2019")
            
            st.markdown("---")
            
            # Alerta informativa
            st.warning("""
            **🔍 Hallazgo Importante:** Durante los años 2017, 2018 y 2019, las bases de datos del Saber Pro
            incluyen registros de estudiantes que presentaron el examen en ciudades internacionales.
            Esto representa una oportunidad para analizar la internacionalización del examen.
            """)
            
            # 1. Distribución por años
            st.subheader("📅 Distribución por Año")
            if 'periodo' in df_internacional.columns:
                df_internacional['anio'] = df_internacional['periodo'].astype(str).str[:4].astype(int)
                por_anio = df_internacional.groupby('anio').size().reset_index(name='cantidad')
                
                fig_anio = px.bar(
                    por_anio, x='anio', y='cantidad',
                    title='Estudiantes en Ciudades Internacionales por Año',
                    labels={'cantidad': 'Número de Estudiantes', 'anio': 'Año'},
                    color='cantidad',
                    color_continuous_scale='Oranges'
                )
                st.plotly_chart(fig_anio, use_container_width=True)
            
            # 2. Top ciudades internacionales
            st.subheader("🏙️ Top 20 Ciudades Internacionales")
            top_ciudades = df_internacional['estu_depto_presentacion'].value_counts().head(20)
            
            fig_ciudades = px.bar(
                x=top_ciudades.values,
                y=top_ciudades.index,
                orientation='h',
                title='Ciudades Internacionales con Más Estudiantes',
                labels={'x': 'Número de Estudiantes', 'y': 'Ciudad'},
                color=top_ciudades.values,
                color_continuous_scale='Oranges'
            )
            fig_ciudades.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_ciudades, use_container_width=True)
            
            # 3. Mapa mundial (si hay suficientes datos)
            st.subheader("🗺️ Distribución Geográfica")
            
            # Crear un DataFrame con coordenadas aproximadas de las ciudades
            coordenadas_ciudades = {
                'ABU DHABI': (24.4539, 54.3773),
                'AMSTERDAM': (52.3676, 4.9041),
                'ANKARA': (39.9334, 32.8597),
                'AUCKLAND': (-36.8509, 174.7645),
                'BARCELONA': (41.3851, 2.1734),
                'BEIJING': (39.9042, 116.4074),
                'BERLIN': (52.5200, 13.4050),
                'BERNA': (46.9480, 7.4474),
                'BUENOS AIRES': (-34.6037, -58.3816),
                'CALGARY': (51.0447, -114.0719),
                'CIUDAD DE PANAMÁ': (8.9824, -79.5199),
                'EL CAIRO': (30.0444, 31.2357),
                'ESTOCOLMO': (59.3293, 18.0686),
                'FRANKFURT': (50.1109, 8.6821),
                'GUADALAJARA': (20.6597, -103.3496),
                'GUATEMALA': (14.6349, -90.5069),
                'HONG KONG': (22.3193, 114.1694),
                'HOUSTON': (29.7604, -95.3698),
                'LA HABANA': (23.1136, -82.3666),
                'LIMA': (-12.0464, -77.0428),
                'LONDRES': (51.5074, -0.1278),
                'LOS ANGELES': (34.0522, -118.2437),
                'MADRID': (40.4168, -3.7038),
                'MIAMI': (25.7617, -80.1918),
                'MILAN': (45.4642, 9.1900),
                'MONTEVIDEO': (-34.9011, -56.1645),
                'MÉXICO DF': (19.4326, -99.1332),
                'NUEVA YORK': (40.7128, -74.0060),
                'PARIS': (48.8566, 2.3522),
                'QUITO': (-0.1807, -78.4678),
                'ROMA': (41.9028, 12.4964),
                'SAN JOSE': (9.9281, -84.0907),
                'SAN JUAN DE PUERTO RICO': (18.4655, -66.1057),
                'SANTIAGO DE CHILE': (-33.4489, -70.6693),
                'SANTO DOMINGO': (18.4861, -69.9312),
                'SAO PAULO': (-23.5505, -46.6333),
                'SEUL': (37.5665, 126.9780),
                'SYDNEY': (-33.8688, 151.2093),
                'TEL AVIV': (32.0853, 34.7818),
                'TOKIO': (35.6762, 139.6503),
                'TORONTO': (43.6532, -79.3832),
                'VIENA': (48.2082, 16.3738)
            }
            
            # Crear DataFrame para el mapa
            datos_mapa = []
            for ciudad, count in df_internacional['estu_depto_presentacion'].value_counts().items():
                if ciudad in coordenadas_ciudades:
                    lat, lon = coordenadas_ciudades[ciudad]
                    datos_mapa.append({
                        'ciudad': ciudad,
                        'estudiantes': count,
                        'lat': lat,
                        'lon': lon
                    })
            
            if datos_mapa:
                df_mapa = pd.DataFrame(datos_mapa)
                
                fig_mapa = px.scatter_geo(
                    df_mapa,
                    lat='lat',
                    lon='lon',
                    size='estudiantes',
                    hover_name='ciudad',
                    hover_data={'estudiantes': True, 'lat': False, 'lon': False},
                    title='Distribución Mundial de Ciudades con Estudiantes del Saber Pro',
                    size_max=30,
                    color='estudiantes',
                    color_continuous_scale='Oranges'
                )
                fig_mapa.update_layout(
                    geo=dict(
                        showland=True,
                        landcolor="lightgray",
                        countrycolor="white",
                        projection_type="natural earth"
                    )
                )
                st.plotly_chart(fig_mapa, use_container_width=True)
            
            # 4. Tabla detallada
            with st.expander("📋 Ver lista completa de ciudades internacionales"):
                lista_completa = df_internacional['estu_depto_presentacion'].value_counts().sort_index()
                st.dataframe(lista_completa)
            
            # 5. Interpretación
            st.subheader("📊 Interpretación del Hallazgo")
            st.markdown("""
            ### ¿Por qué aparecen ciudades internacionales?
            
            1. **Internacionalización del examen**: El ICFES ha estado expandiendo el Saber Pro a otros países
            2. **Periodo específico**: Solo aparece en 2017-2019, lo que sugiere un proyecto piloto o temporal
            3. **Ciudades principales**: Las ciudades con más registros son:
               - **México DF** (792 estudiantes)
               - **París** (578 estudiantes)
               - **Madrid** (424 estudiantes)
               - **Abu Dabi** (37 estudiantes)
            
            ### Posibles explicaciones:
            - **Convenios internacionales**: Universidades colombianas con sedes en el extranjero
            - **Estudiantes en movilidad**: Colombianos estudiando en el exterior
            - **Proyectos de internacionalización**: Programas específicos del gobierno
            
            ### Para la exposición:
            Este hallazgo es importante porque muestra:
            - La capacidad del ICFES para realizar pruebas fuera del territorio nacional
            - La internacionalización de la educación superior colombiana
            - Un dato curioso que puede generar discusión académica
            """)
        else:
            st.warning("No hay datos consolidados disponibles para el análisis.")
    
    elif selected_option == "🧹 Detalle de Limpieza":
        st.title("🧹 Proceso de Limpieza y Validación")
        
        st.markdown(create_processing_summary())
        
        # Mostrar el reporte de procesamiento si existe
        reporte_path = RUTA_DATOS_PROCESADOS / "reporte_procesamiento.txt"
        if reporte_path.exists():
            with st.expander("📄 Ver Reporte Completo de Procesamiento"):
                st.text(reporte_path.read_text())
    
    elif selected_option == "📋 Muestra de Datos":
        st.title("📋 Muestra de Datos Procesados")
        
        if consolidado is not None:
            st.markdown("### Vista Previa del Archivo Consolidado")
            
            # Muestra de datos
            muestra_df = create_data_sample_table(consolidado)
            if muestra_df is not None:
                st.dataframe(muestra_df, use_container_width=True)
            
            # Información del consolidado
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Información del Consolidado")
                st.markdown(f"""
                - **Total registros:** {len(consolidado):,}
                - **Total columnas:** {len(consolidado.columns)}
                - **Años incluidos:** {consolidado['anio_procesamiento'].nunique() if 'anio_procesamiento' in consolidado.columns else 'N/A'}
                - **Tamaño en memoria:** {consolidado.memory_usage(deep=True).sum() / 1024**2:.1f} MB
                """)
            
            with col2:
                st.markdown("### 📁 Columnas Disponibles")
                st.write(consolidado.columns.tolist())
        
        # Estadísticas de distribución por año
        if consolidado is not None and 'anio_procesamiento' in consolidado.columns:
            st.markdown("---")
            st.subheader("📊 Distribución de Registros por Año")
            
            distribucion = consolidado['anio_procesamiento'].value_counts().sort_index()
            
            fig = px.bar(
                x=distribucion.index,
                y=distribucion.values,
                title='Distribución de Registros en el Consolidado',
                labels={'x': 'Año', 'y': 'Número de Registros'},
                color=distribucion.values,
                color_continuous_scale='Blues'
            )
            
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()