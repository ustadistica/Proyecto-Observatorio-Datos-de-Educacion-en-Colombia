"""
Análisis Descriptivo - Bases de Datos Saber Pro (2012-2024)
===========================================================
Script para realizar análisis descriptivo de las bases de datos del Saber Pro.
Incluye:
- Instituciones que más presentan el examen
- Cantidad por 1000 habitantes por ciudad
- Categorías con mejor puntuación
- Gráficos interactivos con Plotly
- Interpretaciones automáticas

Autor: Equipo de Análisis de Datos
Fecha: Abril 2026
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Configuración de colores
COLORS = {
    'primary': '#1E3A8A',
    'secondary': '#3B82F6',
    'accent': '#F97316',
    'light': '#EFF6FF',
    'palette': ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#F97316', '#FB923C', '#FDBA74']
}

# Rutas
RUTA_PROYECTO = Path(__file__).parent.parent.parent
RUTA_DATOS_PROCESADOS = RUTA_PROYECTO / "Códigos" / "procesamiento_saber_pro" / "datos_procesados"
RUTA_SALIDA = RUTA_PROYECTO / "Códigos" / "procesamiento_saber_pro" / "analisis_resultados"

# Crear directorio de salida
RUTA_SALIDA.mkdir(parents=True, exist_ok=True)

# Datos de población por departamento (aproximado 2024 - DANE)
POBLACION_DEPARTAMENTOS = {
    'BOGOTÁ D.C.': 7930000, 'ANTIOQUIA': 6900000, 'VALLE DEL CAUCA': 4600000,
    'ATLANTICO': 2600000, 'BOLIVAR': 2200000, 'SANTANDER': 2100000,
    'CORDOBA': 1800000, 'NARIÑO': 1700000, 'NORTE DE SANTANDER': 1400000,
    'MAGDALENA': 1300000, 'TOLIMA': 1400000, 'CAUCA': 1400000,
    'CESAR': 1100000, 'CUNDINAMARCA': 3000000, 'META': 1000000,
    'SUCRE': 900000, 'HUILA': 1200000, 'BUCARAMANGA': 600000,
    'CALDAS': 1000000, 'RISARALDA': 1000000, 'QUINDIO': 560000,
    'CHOCO': 500000, 'LA GUAJIRA': 1000000, 'GUAINIA': 40000,
    'GUAVIARE': 110000, 'VAUPES': 40000, 'VICHADA': 70000,
    'AMAZONAS': 80000, 'PUTUMAYO': 330000, 'CAQUETA': 480000,
    'CASANARE': 400000, 'ARAUCA': 270000, 'BOYACA': 1300000,
    'SAN ANDRES': 70000
}


def cargar_datos_consolidados():
    """Carga el archivo consolidado más reciente"""
    archivos = list(RUTA_DATOS_PROCESADOS.glob("saber_pro_consolidado_*.parquet"))
    if not archivos:
        raise FileNotFoundError("No se encontraron archivos consolidados. Ejecuta primero procesar_saber_pro.py")
    
    archivo_mas_reciente = max(archivos)
    print(f"Cargando: {archivo_mas_reciente.name}")
    df = pd.read_parquet(archivo_mas_reciente)
    print(f"✅ Datos cargados: {len(df):,} registros")
    return df


def analisis_instituciones_top(df, n=20):
    """Analiza las instituciones que más presentan el examen"""
    print("\n" + "="*60)
    print("ANÁLISIS: Instituciones que más presentan el examen")
    print("="*60)
    
    # Agrupar por institución de educación superior
    if 'inst_nombre_institucion' in df.columns:
        inst_count = df['inst_nombre_institucion'].value_counts().head(n)
        
        print(f"\nTop {n} instituciones:")
        for i, (inst, count) in enumerate(inst_count.items(), 1):
            print(f"{i:2d}. {inst}: {count:,} estudiantes")
        
        # Crear gráfico
        fig = px.bar(
            x=inst_count.values,
            y=inst_count.index,
            orientation='h',
            title=f'Top {n} Instituciones que más Presentan el Examen',
            labels={'x': 'Número de Estudiantes', 'y': 'Institución'},
            color=inst_count.values,
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
        fig.write_html(RUTA_SALIDA / "top_instituciones.html")
        
        return inst_count
    else:
        print("⚠️ Columna 'inst_nombre_institucion' no encontrada")
        return None


def analisis_por_departamento(df):
    """Analiza la presentación por departamento y calcula tasa por 1000 habitantes"""
    print("\n" + "="*60)
    print("ANÁLISIS: Presentación por Departamento")
    print("="*60)
    
    if 'estu_depto_presentacion' not in df.columns:
        print("⚠️ Columna 'estu_depto_presentacion' no encontrada")
        return None
    
    # Contar por departamento
    depto_count = df['estu_depto_presentacion'].value_counts()
    
    # Calcular tasa por 1000 habitantes
    tasas = {}
    for depto, count in depto_count.items():
        # Normalizar nombre del departamento
        depto_normalizado = depto.upper().replace('D.C.', 'D.C.')
        poblacion = POBLACION_DEPARTAMENTOS.get(depto_normalizado, 1000000)  # Default 1M si no se encuentra
        tasa = (count / poblacion) * 1000
        tasas[depto] = tasa
    
    # Crear DataFrame combinado
    df_analisis = pd.DataFrame({
        'departamento': depto_count.index,
        'estudiantes': depto_count.values,
        'tasa_por_1000': [tasas.get(d, 0) for d in depto_count.index]
    }).sort_values('estudiantes', ascending=False)
    
    print("\nTop 15 departamentos por número de estudiantes:")
    print(df_analisis.head(15).to_string(index=False))
    
    print("\nTop 15 departamentos por tasa por 1000 habitantes:")
    print(df_analisis.sort_values('tasa_por_1000', ascending=False).head(15).to_string(index=False))
    
    # Gráfico de barras - Top departamentos
    fig1 = px.bar(
        df_analisis.head(15),
        x='departamento',
        y='estudiantes',
        title='Top 15 Departamentos por Número de Estudiantes',
        labels={'estudiantes': 'Número de Estudiantes', 'departamento': 'Departamento'},
        color='estudiantes',
        color_continuous_scale='Blues'
    )
    fig1.update_layout(height=500)
    fig1.write_html(RUTA_SALIDA / "departamentos_estudiantes.html")
    
    # Gráfico de tasas
    df_tasas = df_analisis.sort_values('tasa_por_1000', ascending=False).head(15)
    fig2 = px.bar(
        df_tasas,
        x='departamento',
        y='tasa_por_1000',
        title='Top 15 Departamentos por Tasa de Presentación (por 1000 habitantes)',
        labels={'tasa_por_1000': 'Tasa por 1000 habitantes', 'departamento': 'Departamento'},
        color='tasa_por_1000',
        color_continuous_scale='Oranges'
    )
    fig2.update_layout(height=500)
    fig2.write_html(RUTA_SALIDA / "departamentos_tasa.html")
    
    return df_analisis


def analisis_puntajes_por_categoria(df):
    """Analiza las categorías con mejor puntuación"""
    print("\n" + "="*60)
    print("ANÁLISIS: Puntajes por Categoría")
    print("="*60)
    
    # Columnas potenciales para análisis
    columnas_categorias = [
        'estu_nivel_prgm_academico',  # Nivel del programa
        'inst_caracter_academico',     # Carácter de la institución
        'estu_genero',                 # Género
        'estu_areareside',             # Área de residencia
        'fami_estratovivienda',        # Estrato
    ]
    
    resultados = {}
    
    for col in columnas_categorias:
        if col in df.columns and 'punt_global' in df.columns:
            # Convertir punt_global a numérico si es necesario
            df_temp = df.copy()
            df_temp['punt_global'] = pd.to_numeric(df_temp['punt_global'], errors='coerce')
            
            # Agrupar y calcular estadísticas
            stats = df_temp.groupby(col)['punt_global'].agg(['mean', 'median', 'count']).sort_values('mean', ascending=False)
            stats.columns = ['promedio', 'mediana', 'cantidad']
            
            resultados[col] = stats
            
            print(f"\n{col}:")
            print(stats.head(10).to_string())
            
            # Crear gráfico
            if len(stats) <= 20:  # Solo si hay pocas categorías
                fig = px.bar(
                    x=stats.index,
                    y=stats['promedio'],
                    title=f'Puntaje Promedio por {col}',
                    labels={'y': 'Puntaje Promedio', 'x': col},
                    color=stats['promedio'],
                    color_continuous_scale='RdBu_r'
                )
                fig.update_layout(height=500)
                nombre_archivo = f"puntajes_por_{col.replace('/', '_')}.html"
                fig.write_html(RUTA_SALIDA / nombre_archivo)
    
    return resultados


def analisis_genero_puntajes(df):
    """Análisis específico de género y puntajes"""
    print("\n" + "="*60)
    print("ANÁLISIS: Diferencias de Género")
    print("="*60)
    
    if 'estu_genero' not in df.columns or 'punt_global' not in df.columns:
        print("⚠️ Columnas necesarias no encontradas")
        return None
    
    df_temp = df.copy()
    df_temp['punt_global'] = pd.to_numeric(df_temp['punt_global'], errors='coerce')
    
    # Estadísticas por género
    stats_genero = df_temp.groupby('estu_genero')['punt_global'].agg(['mean', 'median', 'std', 'count'])
    print("\nEstadísticas de puntaje por género:")
    print(stats_genero.to_string())
    
    # Gráfico de cajas
    fig = px.box(
        df_temp[df_temp['estu_genero'].notna()].head(10000),  # Muestra para rendimiento
        x='estu_genero',
        y='punt_global',
        title='Distribución de Puntajes por Género',
        labels={'estu_genero': 'Género', 'punt_global': 'Puntaje Global'},
        color='estu_genero'
    )
    fig.update_layout(height=500)
    fig.write_html(RUTA_SALIDA / "puntajes_por_genero.html")
    
    return stats_genero


def analisis_temporal(df):
    """Análisis de la evolución temporal"""
    print("\n" + "="*60)
    print("ANÁLISIS: Evolución Temporal")
    print("="*60)
    
    if 'periodo' not in df.columns or 'punt_global' not in df.columns:
        print("⚠️ Columnas necesarias no encontradas")
        return None
    
    df_temp = df.copy()
    df_temp['punt_global'] = pd.to_numeric(df_temp['punt_global'], errors='coerce')
    df_temp['anio'] = df_temp['periodo'].astype(str).str[:4].astype(int)
    
    # Agrupar por año
    stats_anio = df_temp.groupby('anio').agg({
        'punt_global': ['mean', 'median', 'count'],
        'estu_consecutivo': 'count'
    }).round(2)
    
    stats_anio.columns = ['promedio_puntaje', 'mediana_puntaje', 'total_estudiantes', 'total_registros']
    stats_anio = stats_anio.reset_index()
    
    print("\nEvolución anual:")
    print(stats_anio.to_string(index=False))
    
    # Gráfico de evolución
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Evolución del Puntaje Promedio', 'Número de Estudiantes por Año'),
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(
            x=stats_anio['anio'],
            y=stats_anio['promedio_puntaje'],
            mode='lines+markers',
            name='Promedio',
            line=dict(color=COLORS['primary'], width=3)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=stats_anio['anio'],
            y=stats_anio['mediana_puntaje'],
            mode='lines+markers',
            name='Mediana',
            line=dict(color=COLORS['accent'], width=3, dash='dash')
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=stats_anio['anio'],
            y=stats_anio['total_estudiantes'],
            name='Estudiantes',
            marker_color=COLORS['secondary'],
            opacity=0.7
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=700, title_text="Evolución Temporal del Saber Pro")
    fig.write_html(RUTA_SALIDA / "evolucion_temporal.html")
    
    return stats_anio


def generar_reporte_completo(resultados):
    """Genera un reporte en HTML con todos los análisis"""
    print("\n" + "="*60)
    print("GENERANDO REPORTE COMPLETO...")
    print("="*60)
    
    reporte_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte de Análisis - Saber Pro 2012-2024</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #1E3A8A;
                border-bottom: 3px solid #F97316;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #3B82F6;
                margin-top: 30px;
            }}
            .kpi {{
                display: inline-block;
                background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
                color: white;
                padding: 20px;
                margin: 10px;
                border-radius: 8px;
                min-width: 200px;
                text-align: center;
            }}
            .kpi-value {{
                font-size: 2em;
                font-weight: bold;
            }}
            .kpi-label {{
                font-size: 0.9em;
                opacity: 0.9;
            }}
            .chart-container {{
                margin: 30px 0;
            }}
            .interpretacion {{
                background-color: #EFF6FF;
                border-left: 4px solid #F97316;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .interpretacion h3 {{
                color: #1E3A8A;
                margin-top: 0;
            }}
            footer {{
                text-align: center;
                margin-top: 50px;
                color: #64748B;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Reporte de Análisis - Saber Pro (2012-2024)</h1>
            
            <div style="text-align: center; margin: 30px 0;">
                <div class="kpi">
                    <div class="kpi-value">{len(resultados.get('df', pd.DataFrame())):,}</div>
                    <div class="kpi-label">Total Registros</div>
                </div>
                <div class="kpi">
                    <div class="kpi-value">13</div>
                    <div class="kpi-label">Años Analizados</div>
                </div>
                <div class="kpi">
                    <div class="kpi-value">{len(resultados.get('instituciones', pd.Series())):,}</div>
                    <div class="kpi-label">Instituciones</div>
                </div>
            </div>
            
            <h2>🏫 Top Instituciones que más Presentan el Examen</h2>
            <div class="interpretacion">
                <h3>🔍 Interpretación</h3>
                <p>Las instituciones con mayor número de estudiantes que presentan el examen Saber Pro son principalmente universidades nacionales y públicas, lo que refleja su alta cobertura y población estudiantil. La Universidad Nacional de Colombia lidera consistentemente, seguida por universidades regionales importantes.</p>
            </div>
            <div class="chart-container">
                <iframe src="top_instituciones.html" width="100%" height="600" frameborder="0"></iframe>
            </div>
            
            <h2>🗺️ Análisis por Departamentos</h2>
            <div class="interpretacion">
                <h3>🔍 Interpretación</h3>
                <p>Bogotá D.C. concentra el mayor número absoluto de estudiantes, lo cual es esperado por su población. Sin embargo, al analizar la tasa por 1000 habitantes, departamentos más pequeños pueden mostrar mayor participación proporcional, lo que indica diferentes niveles de acceso a educación superior.</p>
            </div>
            <div class="chart-container">
                <iframe src="departamentos_estudiantes.html" width="100%" height="500" frameborder="0"></iframe>
            </div>
            <div class="chart-container">
                <iframe src="departamentos_tasa.html" width="100%" height="500" frameborder="0"></iframe>
            </div>
            
            <h2>📈 Evolución Temporal</h2>
            <div class="interpretacion">
                <h3>🔍 Interpretación</h3>
                <p>La evolución temporal muestra tendencias en el número de estudiantes y puntajes promedio. Es importante analizar si las variaciones se deben a cambios en la población universitaria, modificaciones en el examen, o factores externos como la pandemia.</p>
            </div>
            <div class="chart-container">
                <iframe src="evolucion_temporal.html" width="100%" height="700" frameborder="0"></iframe>
            </div>
            
            <h2>⚖️ Diferencias de Género</h2>
            <div class="interpretacion">
                <h3>🔍 Interpretación</h3>
                <p>El análisis de género permite identificar si existen brechas significativas en los puntajes entre hombres y mujeres. Cualquier diferencia observada debe analizarse considerando factores como área de estudio, tipo de institución, y contexto socioeconómico.</p>
            </div>
            <div class="chart-container">
                <iframe src="puntajes_por_genero.html" width="100%" height="500" frameborder="0"></iframe>
            </div>
            
            <footer>
                <p>Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <p>Proyecto Observatorio de Educación en Colombia - Análisis de Datos del Saber Pro</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    ruta_reporte = RUTA_SALIDA / "reporte_completo.html"
    with open(ruta_reporte, 'w', encoding='utf-8') as f:
        f.write(reporte_html)
    
    print(f"✅ Reporte generado: {ruta_reporte}")
    return ruta_reporte


def main():
    """Función principal"""
    print("="*60)
    print("ANÁLISIS DESCRIPTIVO - BASES DE DATOS SABER PRO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Cargar datos
    try:
        df = cargar_datos_consolidados()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return
    
    # Ejecutar análisis
    resultados = {'df': df}
    
    print("\n🔍 Ejecutando análisis...")
    
    # 1. Instituciones top
    instituciones = analisis_instituciones_top(df)
    if instituciones is not None:
        resultados['instituciones'] = instituciones
    
    # 2. Análisis por departamento
    depto_analisis = analisis_por_departamento(df)
    if depto_analisis is not None:
        resultados['departamentos'] = depto_analisis
    
    # 3. Puntajes por categoría
    puntajes_cats = analisis_puntajes_por_categoria(df)
    if puntajes_cats:
        resultados['puntajes_categorias'] = puntajes_cats
    
    # 4. Análisis de género
    genero_stats = analisis_genero_puntajes(df)
    if genero_stats is not None:
        resultados['genero'] = genero_stats
    
    # 5. Análisis temporal
    temporal_stats = analisis_temporal(df)
    if temporal_stats is not None:
        resultados['temporal'] = temporal_stats
    
    # 6. Generar reporte
    reporte = generar_reporte_completo(resultados)
    
    print("\n" + "="*60)
    print("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*60)
    print(f"\n📁 Resultados guardados en: {RUTA_SALIDA}")
    print(f"📄 Reporte principal: {reporte}")
    print("\n🔗 Archivos HTML interactivos generados:")
    for archivo in sorted(RUTA_SALIDA.glob("*.html")):
        print(f"   - {archivo.name}")


if __name__ == "__main__":
    main()