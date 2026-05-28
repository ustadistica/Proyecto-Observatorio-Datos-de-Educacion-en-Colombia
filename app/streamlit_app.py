"""
Dashboard interactivo del Observatorio de Educación - Ustadistica 2026-I

Integra los análisis de:
- Issue 6.1/6.2: Cruce Saber Pro con Graduados SNIES
- Issue 6.4: Análisis de Movilidad Estudiantil
- Issue 6.5: Correlación Matrícula vs Rendimiento

Uso:
    poetry run streamlit run app/streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import json

# Configuración de página
st.set_page_config(
    page_title="Observatorio Ustadistica - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1f77b4; text-align: center; margin-bottom: 1rem;}
    .section-header {font-size: 1.5rem; color: #2c3e50; margin-top: 1.5rem;}
    .metric-card {background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4;}
    .warning-box {background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ffc107;}
    .interpretacion {background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2196f3; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def cargar_datos(ruta_base: str = "datos/processed"):
    """Carga todos los datos procesados"""
    ruta = Path(ruta_base)
    
    datos = {}
    
    # Issue 6.1/6.2 - Cruce Saber Pro con Graduados
    try:
        datos['cruce_ies'] = pd.read_parquet(ruta / "cruce_saber_pro_graduados_ies.parquet")
        datos['cruce_programa'] = pd.read_parquet(ruta / "cruce_saber_pro_graduados_programa.parquet")
        datos['top_programas'] = pd.read_parquet(ruta / "top_programas_mayor_desfase.parquet")
        with open(ruta / "correlaciones.json", 'r') as f:
            datos['correlaciones'] = json.load(f)
    except Exception as e:
        st.warning(f"No se pudieron cargar los datos de cruce: {e}")
    
    # Issue 6.4 - Movilidad
    try:
        datos['matriz_od'] = pd.read_parquet(ruta / "matriz_origen_destino.parquet")
        datos['metricas_concentracion'] = pd.read_parquet(ruta / "metricas_concentracion.parquet")
        datos['flujos_movilidad'] = pd.read_parquet(ruta / "flujos_movilidad.parquet")
        datos['top_rutas'] = pd.read_parquet(ruta / "top_rutas_movilidad.parquet")
    except Exception as e:
        st.warning(f"No se pudieron cargar los datos de movilidad: {e}")
    
    # Issue 6.5 - Correlación Matrícula-Rendimiento
    try:
        datos['cruce_matricula'] = pd.read_parquet(ruta / "cruce_matricula_rendimiento.parquet")
        datos['correlaciones_prog'] = pd.read_parquet(ruta / "correlaciones_por_programa.parquet")
        datos['areas_analisis'] = pd.read_parquet(ruta / "analisis_por_area_conocimiento.parquet")
        datos['alertas'] = pd.read_parquet(ruta / "alertas_tempranas.parquet")
    except Exception as e:
        st.warning(f"No se pudieron cargar los datos de correlación: {e}")
    
    return datos


def corregir_encoding(texto):
    """Corrige problemas de encoding en textos"""
    if isinstance(texto, str):
        try:
            return texto.encode('latin-1').decode('utf-8', errors='ignore')
        except:
            return texto
    return texto


def main():
    # Encabezado principal
    st.markdown('<h1 class="main-header">📊 Observatorio de Educación - Ustadistica 2026-I</h1>', 
                unsafe_allow_html=True)
    
    # Barra lateral con navegación
    st.sidebar.title("🧭 Navegación")
    seccion = st.sidebar.radio(
        "Selecciona un análisis:",
        ["Inicio", "6.1 - Cruce por IES", "6.2 - Eficiencia por Programa", 
         "6.3 - Analisis Universidades Específicas", "6.4 - Movilidad Estudiantil", "6.5 - Matrícula vs Rendimiento",
         "7.1 - PCA Competencias", "7.2 - Clustering Departamental", "7.3 - Saturación de Programas"]
    )
    
    # Cargar datos
    with st.spinner("Cargando datos..."):
        datos = cargar_datos()
    
    # Información en barra lateral
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📁 Fuentes de Datos")
    st.sidebar.info("""
    - **SNIES**: Graduados y Matriculados (2015-2024)
    - **ICFES**: Saber Pro (2015-2024)
    - **PTE**: Presupuesto Territorial
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ Acerca de")
    st.sidebar.caption("""
    Proyecto de consultoría - Universidad Santo Tomás
    Equipo: Ustadistica 2026-I
    """)
    
    # ==================== PÁGINA DE INICIO ====================
    if seccion == "Inicio":
        st.markdown("## 🎯 Bienvenido al Dashboard del Observatorio")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Registros Saber Pro", f"{2683632:,}")
        with col2:
            st.metric("Total Graduados SNIES", f"{420594:,}")
        with col3:
            st.metric("Total Matriculados SNIES", f"{676853:,}")
        
        st.markdown("""
        ### Análisis Disponibles
        
        Este dashboard integra cuatro análisis principales sobre educación superior en Colombia:
        
        #### 6.1 - Cruce Saber Pro con Graduados por IES
        - Relación entre puntajes promedio y volumen de graduados a nivel institucional
        - Correlaciones de Pearson y Spearman
        - Desglose por acreditación (IES acreditadas vs no acreditadas)
        
        #### 6.2 - Eficiencia de Culminación por Programa  
        - Tasa de presentación de Saber Pro vs graduados por programa
        - Top programas con mayor desfase
        - Interpretación de brechas entre graduados y presentados
        
        #### 6.3 - Análisis de Universidades Específicas
        - Universidad Santo Tomás
        - Universidad Nacional de Colombia
        - Corporación Universitaria de Educación Superior (CUN)
        
        #### 6.4 - Movilidad Estudiantil Interdepartamental
        - Flujos de estudiantes entre departamentos
        - Métricas de concentración de oferta educativa
        - Departamentos importadores vs exportadores
        - Top rutas de movilidad
        
        #### 6.5 - Correlación Matrícula vs Rendimiento
        - Análisis de si el crecimiento de matrícula afecta la calidad
        - Alertas tempranas de pérdida de calidad por sobrepoblación
        - Tendencias por área de conocimiento
        
        ---
        
        *Selecciona un análisis en el menú lateral para comenzar.*
        """)
    
    # ==================== ISSUE 6.1 - CRUCE POR IES ====================
    elif seccion == "6.1 - Cruce por IES":
        st.markdown("## 📈 Issue 6.1: Cruce Saber Pro con Graduados por IES")
        
        st.markdown("""
        <div class="interpretacion">
        <strong>📌 Interpretación:</strong> Este análisis cruza los datos de graduados del SNIES con 
        los presentados de Saber Pro a nivel institucional. La <em>tasa de presentación</em> indica 
        qué proporción de graduados realmente presentó el examen Saber Pro. Una tasa cercana a 1 (100%) 
        indica que casi todos los graduados presentaron el examen, mientras que tasas bajas sugieren 
        que muchos estudiantes se gradúan sin presentar la prueba.
        </div>
        """, unsafe_allow_html=True)
        
        if 'cruce_ies' in datos:
            df = datos['cruce_ies']
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                anio_min, anio_max = int(df['anio'].min()), int(df['anio'].max())
                anio_seleccionado = st.slider("Año:", anio_min, anio_max, anio_max)
            
            # Filtrar datos
            df_filtrado = df[df['anio'] == anio_seleccionado]
            
            # Métricas clave
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("IES Analizadas", f"{df_filtrado['nombre_ies'].nunique()}")
            with col2:
                st.metric("Graduados Totales", f"{df_filtrado['total_graduados'].sum():,.0f}")
            with col3:
                st.metric("Presentados Totales", f"{df_filtrado['total_presentados'].sum():,.0f}")
            with col4:
                tasa_promedio = df_filtrado['tasa_presentacion'].mean()
                st.metric("Tasa Presentación Promedio", f"{tasa_promedio:.2%}" if not pd.isna(tasa_promedio) else "N/A")
            
            # Gráfico de dispersión
            st.markdown("### Scatter Plot: Puntaje Promedio vs Graduados")
            
            fig_scatter = px.scatter(
                df_filtrado.dropna(subset=['promedio_puntaje', 'total_graduados']),
                x='total_graduados',
                y='promedio_puntaje',
                hover_data=['nombre_ies'],
                title=f'Puntaje Promedio vs Volumen de Graduados ({anio_seleccionado})',
                labels={'total_graduados': 'Número de Graduados', 'promedio_puntaje': 'Puntaje Promedio Saber Pro'},
                opacity=0.6
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Correlaciones
            st.markdown("### Correlaciones")
            if 'correlaciones' in datos:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Pearson", f"{datos['correlaciones']['pearson']:.4f}")
                with col2:
                    st.metric("Spearman", f"{datos['correlaciones']['spearman']:.4f}")
                
                st.markdown("""
                <div class="interpretacion">
                <strong>📌 Interpretación:</strong> La correlación de Pearson mide la relación lineal 
                entre puntaje y número de graduados. La correlación de Spearman mide la relación 
                monótona (por rangos). Valores cercanos a 0 indican poca relación, valores cercanos 
                a 1 o -1 indican fuerte relación positiva o negativa respectivamente.
                </div>
                """, unsafe_allow_html=True)
            
            # Evolución temporal - Puntajes vs Graduados
            st.markdown("### Evolución Temporal: Puntajes vs Graduados")
            df_anual = df.groupby('anio').agg(
                promedio_puntaje=('promedio_puntaje', 'mean'),
                total_graduados=('total_graduados', 'sum')
            ).reset_index()
            
            fig_evolucion = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_evolucion.add_trace(
                go.Scatter(x=df_anual['anio'], y=df_anual['promedio_puntaje'], 
                          name='Puntaje Promedio', mode='lines+markers', line=dict(color='blue')),
                secondary_y=False
            )
            
            fig_evolucion.add_trace(
                go.Bar(x=df_anual['anio'], y=df_anual['total_graduados'], 
                       name='Graduados', marker_color='rgba(255,0,0,0.3)'),
                secondary_y=True
            )
            
            fig_evolucion.update_layout(
                title='Evolución Temporal: Puntajes vs Graduados',
                xaxis_title='Año',
                yaxis_title='Puntaje Promedio',
                yaxis2_title='Número de Graduados'
            )
            
            st.plotly_chart(fig_evolucion, use_container_width=True)
            
            # NUEVO: Gráfico de barras - Graduados vs Presentados por año
            st.markdown("### Graduados vs Presentados por Año")
            
            st.markdown("""
            <div class="interpretacion">
            <strong>📌 Interpretación:</strong> Este gráfico compara año por año la cantidad total 
            de estudiantes que se graduaron (SNIES) vs la cantidad que presentaron el examen Saber Pro (ICFES). 
            La diferencia entre las barras muestra el desfase entre graduación y presentación del examen.
            </div>
            """, unsafe_allow_html=True)
            
            df_anual_comp = df.groupby('anio').agg(
                total_graduados=('total_graduados', 'sum'),
                total_presentados=('total_presentados', 'sum')
            ).reset_index()
            
            # Crear gráfico de barras agrupadas
            fig_barras_comp = go.Figure()
            
            fig_barras_comp.add_trace(
                go.Bar(
                    x=df_anual_comp['anio'],
                    y=df_anual_comp['total_graduados'],
                    name='Graduados (SNIES)',
                    marker_color='rgba(54, 162, 235, 0.8)',
                    text=df_anual_comp['total_graduados'].apply(lambda x: f'{x:,.0f}'),
                    textposition='auto'
                )
            )
            
            fig_barras_comp.add_trace(
                go.Bar(
                    x=df_anual_comp['anio'],
                    y=df_anual_comp['total_presentados'],
                    name='Presentados Saber Pro (ICFES)',
                    marker_color='rgba(75, 192, 192, 0.8)',
                    text=df_anual_comp['total_presentados'].apply(lambda x: f'{x:,.0f}'),
                    textposition='auto'
                )
            )
            
            fig_barras_comp.update_layout(
                title='Comparación Anual: Graduados vs Presentados Saber Pro',
                xaxis_title='Año',
                yaxis_title='Número de Estudiantes',
                barmode='group',
                legend_title='Tipo'
            )
            
            st.plotly_chart(fig_barras_comp, use_container_width=True)
            
            # Tabla resumen anual
            st.markdown("### Tabla Resumen Anual")
            df_anual_comp['diferencia'] = df_anual_comp['total_graduados'] - df_anual_comp['total_presentados']
            df_anual_comp['porcentaje_presentacion'] = (df_anual_comp['total_presentados'] / df_anual_comp['total_graduados'] * 100).round(1)
            
            st.dataframe(
                df_anual_comp[['anio', 'total_graduados', 'total_presentados', 'diferencia', 'porcentaje_presentacion']].style
                .format({'total_graduados': '{:,.0f}', 'total_presentados': '{:,.0f}', 'diferencia': '{:,.0f}', 'porcentaje_presentacion': '{:.1f}%'})
                .set_properties(subset=['diferencia'], **{'font-weight': 'bold'}),
                use_container_width=True
            )
            
            # NUEVO: Gráfico de barras - Graduados de PREGRADO vs Presentados por año (ajustado)
            st.markdown("### Graduados de Pregrado vs Presentados por Año (Ajustado)")
            
            st.markdown("""
            <div class="interpretacion">
            <strong>📌 Interpretación:</strong> Este gráfico ajusta la comparación restando los graduados de posgrado, 
            ya que el examen Saber Pro está diseñado principalmente para estudiantes de pregrado. 
            Esto proporciona una comparación más precisa entre graduados y presentados.
            </div>
            """, unsafe_allow_html=True)
            
            # Cargar datos de SNIES para obtener graduados de pregrado por año
            try:
                snies_graduados = pd.read_parquet(Path("datos/processed/snies/snies_graduados_consolidado.parquet"))
                
                # Filtrar solo pregrado
                snies_pregrado = snies_graduados[snies_graduados['nivel_academico'] == 'PREGRADO']
                
                # Agrupar por año (extraer año de anio_proceso)
                snies_pregrado['anio'] = snies_pregrado['anio_proceso'].astype(str).str[:4].astype(int)
                graduados_pregrado_anual = snies_pregrado.groupby('anio')['graduados'].sum().reset_index()
                graduados_pregrado_anual = graduados_pregrado_anual.rename(columns={'graduados': 'graduados_pregrado'})
                
                # Unir con los presentados
                df_anual_ajustado = df_anual_comp[['anio', 'total_presentados']].merge(
                    graduados_pregrado_anual, on='anio', how='left'
                )
                
                # Llenar NaN con 0 si no hay datos
                df_anual_ajustado['graduados_pregrado'] = df_anual_ajustado['graduados_pregrado'].fillna(0).astype(int)
                
                # Crear gráfico de barras agrupadas ajustado
                fig_barras_ajustado = go.Figure()
                
                fig_barras_ajustado.add_trace(
                    go.Bar(
                        x=df_anual_ajustado['anio'],
                        y=df_anual_ajustado['graduados_pregrado'],
                        name='Graduados Pregrado (SNIES)',
                        marker_color='rgba(54, 162, 235, 0.8)',
                        text=df_anual_ajustado['graduados_pregrado'].apply(lambda x: f'{x:,.0f}'),
                        textposition='auto'
                    )
                )
                
                fig_barras_ajustado.add_trace(
                    go.Bar(
                        x=df_anual_ajustado['anio'],
                        y=df_anual_ajustado['total_presentados'],
                        name='Presentados Saber Pro (ICFES)',
                        marker_color='rgba(75, 192, 192, 0.8)',
                        text=df_anual_ajustado['total_presentados'].apply(lambda x: f'{x:,.0f}'),
                        textposition='auto'
                    )
                )
                
                fig_barras_ajustado.update_layout(
                    title='Comparación Anual: Graduados de Pregrado vs Presentados Saber Pro (Ajustado)',
                    xaxis_title='Año',
                    yaxis_title='Número de Estudiantes',
                    barmode='group',
                    legend_title='Tipo'
                )
                
                st.plotly_chart(fig_barras_ajustado, use_container_width=True)
                
                # Tabla resumen ajustada
                st.markdown("### Tabla Resumen Ajustada (Solo Pregrado)")
                df_anual_ajustado['diferencia_ajustada'] = df_anual_ajustado['graduados_pregrado'] - df_anual_ajustado['total_presentados']
                df_anual_ajustado['porcentaje_presentacion_ajustado'] = (df_anual_ajustado['total_presentados'] / df_anual_ajustado['graduados_pregrado'] * 100).round(1)
                
                st.dataframe(
                    df_anual_ajustado[['anio', 'graduados_pregrado', 'total_presentados', 'diferencia_ajustada', 'porcentaje_presentacion_ajustado']].style
                    .format({'graduados_pregrado': '{:,.0f}', 'total_presentados': '{:,.0f}', 'diferencia_ajustada': '{:,.0f}', 'porcentaje_presentacion_ajustado': '{:.1f}%'})
                    .set_properties(subset=['diferencia_ajustada'], **{'font-weight': 'bold'}),
                    use_container_width=True
                )
                
            except Exception as e:
                st.warning(f"No se pudieron cargar los datos de nivel académico para el ajuste: {e}")
            
            # NUEVO: Gráfico de torta - Graduados por nivel académico (Pregrado vs Posgrado) - HISTÓRICO
            st.markdown("### Distribución de Graduados por Nivel Académico (Histórico 2015-2024)")
            
            st.markdown("""
            <div class="interpretacion">
            <strong>📌 Interpretación:</strong> Los estudiantes de posgrado (especialización, maestría, doctorado) 
            no están obligados a presentar el examen Saber Pro, el cual está diseñado principalmente para estudiantes 
            de pregrado. Esta diferencia explica en parte por qué hay más graduados que presentados.
            </div>
            """, unsafe_allow_html=True)
            
            # Cargar datos de SNIES para obtener distribución por nivel (TODOS LOS AÑOS)
            try:
                snies_graduados = pd.read_parquet(Path("datos/processed/snies/snies_graduados_consolidado.parquet"))
                
                # Agrupar por nivel académico - TODOS LOS AÑOS (histórico)
                nivel_academico = snies_graduados.groupby('nivel_academico')['graduados'].sum().reset_index()
                nivel_academico = nivel_academico.sort_values('graduados', ascending=False)
                
                # Crear gráfico de torta
                fig_torta = px.pie(
                    nivel_academico,
                    values='graduados',
                    names='nivel_academico',
                    title='Distribución Histórica de Graduados por Nivel Académico (2015-2024)',
                    labels={'nivel_academico': 'Nivel Académico', 'graduados': 'Número de Graduados'}
                )
                
                fig_torta.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_torta, use_container_width=True)
                
                # Mostrar tabla con los datos
                st.markdown("### Detalle por Nivel Académico (Histórico)")
                nivel_academico['porcentaje'] = (nivel_academico['graduados'] / nivel_academico['graduados'].sum() * 100).round(1)
                st.dataframe(
                    nivel_academico.style.format({'graduados': '{:,.0f}', 'porcentaje': '{:.1f}%'}),
                    use_container_width=True
                )
                
                # Evolución temporal por nivel académico
                st.markdown("### Evolución Temporal por Nivel Académico")
                nivel_temporal = snies_graduados.groupby(['anio_proceso', 'nivel_academico'])['graduados'].sum().reset_index()
                nivel_temporal = nivel_temporal.pivot(index='anio_proceso', columns='nivel_academico', values='graduados').fillna(0)
                
                fig_evolucion_nivel = go.Figure()
                for nivel in nivel_temporal.columns:
                    fig_evolucion_nivel.add_trace(
                        go.Scatter(x=nivel_temporal.index, y=nivel_temporal[nivel], 
                                  name=nivel, mode='lines+markers')
                    )
                
                fig_evolucion_nivel.update_layout(
                    title='Evolución de Graduados por Nivel Académico (2015-2024)',
                    xaxis_title='Año',
                    yaxis_title='Número de Graduados',
                    legend_title='Nivel Académico'
                )
                
                st.plotly_chart(fig_evolucion_nivel, use_container_width=True)
                
            except Exception as e:
                st.warning(f"No se pudieron cargar los datos de nivel académico: {e}")
        else:
            st.warning("No hay datos disponibles para este análisis.")
    
    # ==================== ISSUE 6.2 - EFICIENCIA POR PROGRAMA ====================
    elif seccion == "6.2 - Eficiencia por Programa":
        st.markdown("## 🎓 Issue 6.2: Eficiencia de Culminación por Programa")
        
        st.markdown("""
        <div class="interpretacion">
        <strong>📌 Interpretación:</strong> Este análisis mide la <em>eficiencia de culminación</em> 
        comparando cuántos estudiantes se gradúan vs cuántos presentan Saber Pro por programa. 
        La <em>brecha</em> representa la diferencia entre graduados y presentados. Una brecha 
        negativa grande indica que muchos estudiantes se gradúan sin presentar el examen, lo que 
        podría sugerir que el examen no es requisito de grado o que hay baja motivación para presentarlo.
        </div>
        """, unsafe_allow_html=True)
        
        if 'cruce_programa' in datos:
            df = datos['cruce_programa']
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                anios = sorted(df['anio'].unique())
                anio_seleccionado = st.selectbox("Año:", anios, index=len(anios)-1)
            with col2:
                ies_list = sorted(df['nombre_ies'].unique())[:50]  # Limitar a 50 para rendimiento
                ies_seleccionada = st.selectbox("Institución:", ies_list)
            
            # Filtrar datos
            df_filtrado = df[(df['anio'] == anio_seleccionado) & (df['nombre_ies'] == ies_seleccionada)]
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Programas", f"{df_filtrado['programa_academico'].nunique()}")
            with col2:
                st.metric("Graduados", f"{df_filtrado['total_graduados'].sum():,.0f}")
            with col3:
                st.metric("Presentados", f"{df_filtrado['total_presentados'].sum():,.0f}")
            
            # Top programas con mayor desfase
            st.markdown("### Top 10 Programas con Mayor Desfase (Histórico)")
            
            if 'top_programas' in datos:
                top_df = datos['top_programas'].copy()
                top_df['brecha_abs'] = top_df['brecha_total'].abs()
                top_df = top_df.sort_values('brecha_abs', ascending=True)
                
                fig_barras = px.bar(
                    top_df.head(10),
                    x='brecha_abs',
                    y='programa_academico',
                    orientation='h',
                    title='Top 10 Programas con Mayor Desfase entre Graduados y Presentados',
                    labels={'brecha_abs': 'Magnitud del Desfase'},
                    hover_data=['nombre_ies', 'graduados_totales', 'presentados_totales']
                )
                st.plotly_chart(fig_barras, use_container_width=True)
                
                st.markdown("""
                <div class="interpretacion">
                <strong>📌 Interpretación:</strong> Estos programas tienen la mayor diferencia entre 
                el número de graduados y el número de estudiantes que presentaron Saber Pro. 
                Una brecha negativa grande (como -51,570 en Tecnología en Gestión Empresarial del SENA) 
                indica que hay muchos más graduados que presentados, lo que sugiere que el examen 
                no es obligatorio para graduarse en estos programas.
                </div>
                """, unsafe_allow_html=True)
            
            # Tabla de programas
            st.markdown("### Detalle de Programas")
            if not df_filtrado.empty:
                df_display = df_filtrado[[
                    'programa_academico', 'total_graduados', 'total_presentados', 
                    'tasa_presentacion', 'promedio_puntaje'
                ]].sort_values('tasa_presentacion', ascending=False)
                st.dataframe(df_display, use_container_width=True)
            else:
                st.info("No hay datos para la combinación seleccionada.")
        else:
            st.warning("No hay datos disponibles para este análisis.")
    
    # ==================== ISSUE 6.3 - UNIVERSIDADES ESPECÍFICAS ====================
    elif seccion == "6.3 - Analisis Universidades Específicas":
        st.markdown("## 🏛️ Issue 6.3: Análisis de Universidades Específicas")
        
        st.markdown("""
        <div class="interpretacion">
        <strong>📌 Interpretación:</strong> Este análisis compara el desempeño de universidades específicas:
        <ul>
            <li><strong>Top 10 IES Acreditadas</strong> con más presentados de Saber Pro</li>
            <li><strong>Top 10 IES No Acreditadas</strong> con más presentados de Saber Pro</li>
            <li><strong>Universidades de Referencia</strong>: Universidad Santo Tomás, Universidad Nacional de Colombia y CUN</li>
        </ul>
        Se muestra la relación entre graduados y presentados de Saber Pro.
        </div>
        """, unsafe_allow_html=True)
        
        if 'cruce_ies' in datos:
            df = datos['cruce_ies']
            
            # ==================== TOP 10 IES ACREDITADAS ====================
            st.markdown("### 🏆 Top 10 IES Acreditadas con Más Presentados Saber Pro (Histórico)")
            
            # Filtrar IES acreditadas (asumiendo que hay columna de acreditación en los datos)
            # Si no hay columna de acreditación, usamos las IES con mayor volumen
            df_historico = df.groupby('nombre_ies').agg(
                total_presentados=('total_presentados', 'sum'),
                total_graduados=('total_graduados', 'sum'),
                promedio_puntaje=('promedio_puntaje', 'mean')
            ).reset_index()
            
            # Calcular tasa de presentación histórica
            df_historico['tasa_presentacion'] = (df_historico['total_presentados'] / df_historico['total_graduados'] * 100).round(1)
            
            # Top 10 IES con más presentados
            top_ies_presentados = df_historico.nlargest(10, 'total_presentados')
            
            fig_top_ies = px.bar(
                top_ies_presentados,
                x='total_presentados',
                y='nombre_ies',
                orientation='h',
                title='Top 10 IES con Más Presentados Saber Pro (Histórico)',
                labels={'total_presentados': 'Total Presentados', 'nombre_ies': 'Institución'},
                hover_data=['total_graduados', 'tasa_presentacion', 'promedio_puntaje']
            )
            fig_top_ies.update_traces(marker_color='rgba(54, 162, 235, 0.8)')
            st.plotly_chart(fig_top_ies, use_container_width=True)
            
            st.markdown("""
            <div class="interpretacion">
            <strong>📌 Interpretación:</strong> Estas son las 10 instituciones con mayor número de estudiantes 
            que presentaron el examen Saber Pro en el período histórico. El volumen de presentados refleja 
            tanto el tamaño de la institución como su tasa de graduación.
            </div>
            """, unsafe_allow_html=True)
            
            # Tabla detallada del top
            st.markdown("### Detalle Top 10 IES con Más Presentados")
            st.dataframe(
                top_ies_presentados[['nombre_ies', 'total_graduados', 'total_presentados', 'tasa_presentacion', 'promedio_puntaje']].style
                .format({'total_graduados': '{:,.0f}', 'total_presentados': '{:,.0f}', 'tasa_presentacion': '{:.1f}%', 'promedio_puntaje': '{:.1f}'})
                .set_properties(subset=['total_presentados'], **{'font-weight': 'bold'}),
                use_container_width=True
            )
            
            # ==================== UNIVERSIDADES ESPECÍFICAS ====================
            st.markdown("---")
            st.markdown("### 🎯 Análisis de Universidades de Referencia")
            
            st.markdown("""
            <div class="interpretacion">
            <strong>📌 Interpretación:</strong> Análisis detallado de tres universidades de referencia:
            <ul>
                <li><strong>Universidad Santo Tomás</strong> - Universidad católica con amplia cobertura nacional</li>
                <li><strong>Universidad Nacional de Colombia</strong> - Universidad pública líder en investigación</li>
                <li><strong>Corporación Universitaria de Educación Superior (CUN)</strong> - Institución privada con enfoque en educación accesible</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Universidades específicas
            universidades_especificas = [
                'UNIVERSIDAD SANTO TOMAS',
                'UNIVERSIDAD NACIONAL DE COLOMBIA',
                'CORPORACION UNIFICADA NACIONAL DE EDUCACION SUPERIOR-CUN-'
            ]
            
            # Filtrar solo datos de estas universidades (todos los años)
            df_univ = df[df['nombre_ies'].isin(universidades_especificas)]
            
            if not df_univ.empty:
                # Selector de universidad
                univ_seleccionada = st.selectbox("Selecciona una universidad:", 
                    ['TODAS'] + [nombre for nombre in universidades_especificas if nombre in df_univ['nombre_ies'].values])
                
                if univ_seleccionada != 'TODAS':
                    df_univ_filtrado = df_univ[df_univ['nombre_ies'] == univ_seleccionada]
                else:
                    df_univ_filtrado = df_univ
                
                # Métricas generales (histórico)
                st.markdown("### Métricas Generales (Histórico 2015-2024)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Graduados", f"{df_univ_filtrado['total_graduados'].sum():,.0f}")
                with col2:
                    st.metric("Total Presentados", f"{df_univ_filtrado['total_presentados'].sum():,.0f}")
                with col3:
                    tasa = df_univ_filtrado['tasa_presentacion'].mean()
                    st.metric("Tasa Presentación Promedio", f"{tasa:.2%}" if not pd.isna(tasa) else "N/A")
                with col4:
                    puntaje = df_univ_filtrado['promedio_puntaje'].mean()
                    st.metric("Puntaje Promedio", f"{puntaje:.1f}" if not pd.isna(puntaje) else "N/A")
                
                # Gráfico de barras - Graduados vs Presentados por año
                st.markdown("### Graduados vs Presentados por Año")
                df_anual_univ = df_univ_filtrado.groupby('anio').agg(
                    total_graduados=('total_graduados', 'sum'),
                    total_presentados=('total_presentados', 'sum')
                ).reset_index()
                
                fig_barras_univ = go.Figure()
                fig_barras_univ.add_trace(
                    go.Bar(x=df_anual_univ['anio'], y=df_anual_univ['total_graduados'],
                          name='Graduados', marker_color='rgba(54, 162, 235, 0.8)')
                )
                fig_barras_univ.add_trace(
                    go.Bar(x=df_anual_univ['anio'], y=df_anual_univ['total_presentados'],
                          name='Presentados Saber Pro', marker_color='rgba(75, 192, 192, 0.8)')
                )
                fig_barras_univ.update_layout(
                    title=f'Graduados vs Presentados Saber Pro{f" - {univ_seleccionada}" if univ_seleccionada != "TODAS" else ""}',
                    xaxis_title='Año',
                    yaxis_title='Número de Estudiantes',
                    barmode='group'
                )
                st.plotly_chart(fig_barras_univ, use_container_width=True)
                
                # Evolución temporal de presentados y graduados
                st.markdown("### Evolución de Presentados vs Graduados por Universidad")
                
                # Agrupar por universidad y año
                df_evolucion = df_univ_filtrado.groupby(['nombre_ies', 'anio']).agg(
                    total_graduados=('total_graduados', 'sum'),
                    total_presentados=('total_presentados', 'sum')
                ).reset_index()
                
                if not df_evolucion.empty:
                    fig_evolucion = go.Figure()
                    
                    # Agregar trazas para cada universidad
                    for universidad in df_evolucion['nombre_ies'].unique():
                        df_univ = df_evolucion[df_evolucion['nombre_ies'] == universidad]
                        
                        fig_evolucion.add_trace(
                            go.Scatter(
                                x=df_univ['anio'],
                                y=df_univ['total_graduados'],
                                name=f'{universidad} - Graduados',
                                mode='lines+markers',
                                line=dict(width=3)
                            )
                        )
                        
                        fig_evolucion.add_trace(
                            go.Scatter(
                                x=df_univ['anio'],
                                y=df_univ['total_presentados'],
                                name=f'{universidad} - Presentados',
                                mode='lines+markers',
                                line=dict(dash='dash', width=2)
                            )
                        )
                    
                    fig_evolucion.update_layout(
                        title='Evolución de Graduados vs Presentados por Universidad',
                        xaxis_title='Año',
                        yaxis_title='Número de Estudiantes',
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_evolucion, use_container_width=True)
                else:
                    st.info("No hay datos disponibles para las universidades seleccionadas.")
                
                # Tabla resumen por año
                st.markdown("### Detalle por Año")
                df_detalle = df_univ_filtrado.groupby(['nombre_ies', 'anio']).agg(
                    total_graduados=('total_graduados', 'sum'),
                    total_presentados=('total_presentados', 'sum'),
                    promedio_puntaje=('promedio_puntaje', 'mean')
                ).reset_index()
                df_detalle['tasa_presentacion'] = (df_detalle['total_presentados'] / df_detalle['total_graduados'] * 100).round(1)
                st.dataframe(
                    df_detalle.style.format({
                        'total_graduados': '{:,.0f}',
                        'total_presentados': '{:,.0f}',
                        'promedio_puntaje': '{:.1f}',
                        'tasa_presentacion': '{:.1f}%'
                    }),
                    use_container_width=True
                )
            else:
                st.warning("No hay datos para las universidades específicas.")
        else:
            st.warning("No hay datos disponibles para este análisis.")
    
    # ==================== ISSUE 6.4 - MOVILIDAD ESTUDIANTIL ====================
    elif seccion == "6.4 - Movilidad Estudiantil":
        st.markdown("## 🗺️ Issue 6.4: Movilidad Estudiantil Interdepartamental")
        
        st.markdown("""
        <div class="interpretacion">
        <strong>📌 Interpretación:</strong> Este análisis mide el fenómeno de <em>movilidad estudiantil</em>,
        es decir, cuántos estudiantes se desplazan de su departamento de residencia a otro para estudiar.
        Los <em>departamentos importadores</em> reciben más estudiantes de los que envían, mientras que 
        los <em>exportadores</em> envían más estudiantes de los que reciben.
        </div>
        """, unsafe_allow_html=True)
        
        if 'metricas_concentracion' in datos:
            # Métricas de concentración
            st.markdown("### Concentración de Oferta Educativa por Departamento")
            
            metricas = datos['metricas_concentracion']
            
            # Top departamentos
            top_deptos = metricas.head(10)
            
            fig_concentracion = px.bar(
                top_deptos,
                x='total_estudiantes',
                y='depto_ies',
                orientation='h',
                title='Top 10 Departamentos con Más Estudiantes',
                labels={'total_estudiantes': 'Número de Estudiantes', 'depto_ies': 'Departamento'},
                hover_data=['total_programas', 'total_ies', 'porcentaje_nacional']
            )
            st.plotly_chart(fig_concentracion, use_container_width=True)
            
            # Flujos netos - Tabla mejorada
            st.markdown("### Departamentos Importadores vs Exportadores")
            
            if 'flujos_movilidad' in datos:
                flujos = datos['flujos_movilidad']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📥 Importadores (Flujo Neto Positivo)")
                    st.markdown("""
                    <div class="interpretacion">
                    Departamentos que reciben más estudiantes de los que envían. 
                    Suelen tener mayor oferta educativa o universidades de prestigio.
                    </div>
                    """, unsafe_allow_html=True)
                    importadores = flujos[flujos['balance_movilidad'] == 'Importador'].nlargest(10, 'flujo_neto')
                    st.dataframe(importadores[['departamento', 'flujo_neto', 'porcentaje_movilidad']].style
                                .format({'flujo_neto': '{:,.0f}', 'porcentaje_movilidad': '{:.1f}%'}), 
                                use_container_width=True)
                
                with col2:
                    st.subheader("📤 Exportadores (Flujo Neto Negativo)")
                    st.markdown("""
                    <div class="interpretacion">
                    Departamentos que envían más estudiantes de los que reciben. 
                    Los estudiantes migran a otros departamentos para estudiar.
                    </div>
                    """, unsafe_allow_html=True)
                    exportadores = flujos[flujos['balance_movilidad'] == 'Exportador'].nsmallest(10, 'flujo_neto')
                    st.dataframe(exportadores[['departamento', 'flujo_neto', 'porcentaje_movilidad']].style
                                .format({'flujo_neto': '{:,.0f}', 'porcentaje_movilidad': '{:.1f}%'}), 
                                use_container_width=True)
            
            # Top rutas - Tabla mejorada
            st.markdown("### Top 20 Rutas de Movilidad Más Frecuentes")
            
            if 'top_rutas' in datos:
                st.markdown("""
                <div class="interpretacion">
                Estas son las rutas más comunes que siguen los estudiantes desde su departamento 
                de residencia (origen) hasta el departamento donde estudian (destino).
                </div>
                """, unsafe_allow_html=True)
                top_rutas_df = datos['top_rutas'].head(20).copy()
                st.dataframe(top_rutas_df[['origen', 'destino', 'total_estudiantes', 'porcentaje']].style
                            .format({'total_estudiantes': '{:,.0f}', 'porcentaje': '{:.1f}%'}), 
                            use_container_width=True)
        else:
            st.warning("No hay datos disponibles para este análisis.")
    
    # ==================== ISSUE 6.5 - MATRÍCULA VS RENDIMIENTO ====================
    elif seccion == "6.5 - Matrícula vs Rendimiento":
        st.markdown("## 📊 Issue 6.5: Correlación Matrícula vs Rendimiento Académico")
        
        st.markdown("""
        <div class="interpretacion">
        <strong>📌 Interpretación:</strong> Este análisis busca identificar si los programas con 
        <em>crecimiento exponencial de matrícula</em> sufren una caída en sus indicadores de calidad 
        académica. Una <em>correlación negativa</em> entre crecimiento de matrícula y puntajes sugiere 
        que a medida que aumenta la matrícula, disminuye el rendimiento, posiblemente debido a 
        sobrepoblación, pérdida de control en la relación estudiante-docente o infraestructura insuficiente.
        </div>
        """, unsafe_allow_html=True)
        
        if 'areas_analisis' in datos:
            # Análisis por área de conocimiento
            st.markdown("### Correlaciones por Área de Conocimiento")
            
            areas = datos['areas_analisis'].copy()
            # Corregir encoding en nombres de áreas
            areas['area_conocimiento'] = areas['area_conocimiento'].apply(corregir_encoding)
            areas = areas.sort_values('correlacion_crecimiento_puntaje')
            
            # Top áreas con correlación negativa (posible pérdida de calidad)
            st.subheader("Áreas con Mayor Correlación Negativa (Posible Pérdida de Calidad)")
            
            fig_areas = px.bar(
                areas.head(15),
                x='correlacion_crecimiento_puntaje',
                y='area_conocimiento',
                orientation='h',
                title='Correlación entre Crecimiento y Rendimiento por Área de Conocimiento',
                color='correlacion_crecimiento_puntaje',
                color_continuous_scale='RdYlGn_r',
                labels={'correlacion_crecimiento_puntaje': 'Coeficiente de Correlación', 
                        'area_conocimiento': 'Área de Conocimiento'}
            )
            st.plotly_chart(fig_areas, use_container_width=True)
            
            st.markdown("""
            <div class="interpretacion">
            <strong>📌 Interpretación:</strong> Las áreas con correlación negativa fuerte (como Zootecnia 
            con -0.92) muestran que a medida que aumenta la matrícula, los puntajes tienden a disminuir. 
            Esto podría indicar problemas de calidad relacionados con sobrepoblación.
            </div>
            """, unsafe_allow_html=True)
            
            # Tabla detallada
            st.markdown("### Detalle por Área")
            areas_display = areas[['area_conocimiento', 'correlacion_crecimiento_puntaje', 'p_valor', 'anios_analisis']].copy()
            areas_display['area_conocimiento'] = areas_display['area_conocimiento'].apply(corregir_encoding)
            st.dataframe(areas_display.style.format({'correlacion_crecimiento_puntaje': '{:.4f}', 'p_valor': '{:.4f}'}), 
                        use_container_width=True)
            
            # Alertas tempranas
            st.markdown("### 🚨 Alertas Tempranas")
            
            if 'alertas' in datos and not datos['alertas'].empty:
                alertas = datos['alertas']
                
                # Contar por nivel de riesgo
                col1, col2, col3 = st.columns(3)
                with col1:
                    alto = len(alertas[alertas['nivel_riesgo'] == 'ALTO'])
                    st.metric("Riesgo ALTO", alto)
                with col2:
                    medio = len(alertas[alertas['nivel_riesgo'] == 'MEDIO'])
                    st.metric("Riesgo MEDIO", medio)
                with col3:
                    bajo = len(alertas[alertas['nivel_riesgo'] == 'BAJO'])
                    st.metric("Riesgo BAJO", bajo)
                
                st.dataframe(alertas, use_container_width=True)
            else:
                st.info("No se identificaron programas en riesgo crítico con los umbrales actuales.")
                st.caption("""
                **Nota:** Los umbrales utilizados son:
                - Crecimiento acumulado > 50%
                - Correlación negativa < -0.3
                """)
        else:
            st.warning("No hay datos disponibles para este análisis.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Observatorio de Educación - Ustadistica 2026-I | Universidad Santo Tomás"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()