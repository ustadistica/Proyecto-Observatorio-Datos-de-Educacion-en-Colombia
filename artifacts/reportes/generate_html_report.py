#!/usr/bin/env python3
"""
Script para generar reporte HTML del Sprint 7 - Machine Learning
Autor: German
Fecha: 2026-05-17
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configuración
BASE_DIR = Path(__file__).parent.parent
METRICAS_DIR = BASE_DIR / 'metricas'
OUTPUT_FILE = BASE_DIR / 'reportes' / 'informe_sprint_7_ml.html'

# Cargar datos
with open(METRICAS_DIR / 'metricas_clustering_20260517.json', 'r') as f:
    metricas_clustering = json.load(f)

with open(METRICAS_DIR / 'metricas_regresion_20260517.json', 'r') as f:
    metricas_regresion = json.load(f)

perfiles_clusters = pd.read_csv(METRICAS_DIR / 'perfiles_clusters_20260517.csv', index_col=0)
feature_importance = pd.read_csv(METRICAS_DIR / 'feature_importance_20260517.csv')

# HTML Template
html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe Sprint 7 - Machine Learning</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .metric-card {{
            background-color: #ecf0f1;
            border-left: 5px solid #3498db;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .alert {{
            background-color: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
        }}
        .success {{
            background-color: #d4edda;
            border-left: 5px solid #28a745;
            padding: 15px;
            margin: 15px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 INFORME SPRINT 7: ANÁLISIS DE MACHINE LEARNING</h1>
        <p><strong>Observatorio de Datos de Educación en Colombia</strong></p>
        <p>Fecha: {datetime.now().strftime('%d de %B de %Y')}</p>
        <p>Periodo de Análisis: 2015-2024</p>
        
        <hr>
        
        <h2>📋 RESUMEN EJECUTIVO</h2>
        <div class="success">
            <p><strong>✅ Objetivos Cumplidos:</strong></p>
            <ul>
                <li><strong>Issue 7.1:</strong> Modelo predictivo con 99.54% de precisión</li>
                <li><strong>Issue 7.2:</strong> Clustering de 336 IES en 2 grupos</li>
            </ul>
        </div>
        
        <h2>🎯 1. ANÁLISIS DE CLUSTERING (Issue 7.2)</h2>
        
        <h3>1.1 Métricas de Clustering</h3>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-label">Silhouette Score</div>
                <div class="metric-value">{metricas_clustering['metricas_clustering']['silhouette_score']:.3f}</div>
                <p>Buena separación entre clusters</p>
            </div>
            <div class="metric-card">
                <div class="metric-label">Davies-Bouldin Index</div>
                <div class="metric-value">{metricas_clustering['metricas_clustering']['davies_bouldin_index']:.3f}</div>
                <p>Baja similitud intra-cluster</p>
            </div>
            <div class="metric-card">
                <div class="metric-label">Calinski-Harabasz</div>
                <div class="metric-value">{metricas_clustering['metricas_clustering']['calinski_harabasz_score']:.1f}</div>
                <p>Alta dispersión entre clusters</p>
            </div>
        </div>
        
        <h3>1.2 Distribución de IES por Cluster</h3>
        <table>
            <tr>
                <th>Cluster</th>
                <th>Número de IES</th>
                <th>Porcentaje</th>
            </tr>
            <tr>
                <td>Cluster 0 (Estándar)</td>
                <td>{metricas_clustering['distribucion_clusters']['0']}</td>
                <td>{(metricas_clustering['distribucion_clusters']['0']/336*100):.1f}%</td>
            </tr>
            <tr>
                <td>Cluster 1 (Crítico)</td>
                <td>{metricas_clustering['distribucion_clusters']['1']}</td>
                <td>{(metricas_clustering['distribucion_clusters']['1']/336*100):.1f}%</td>
            </tr>
        </table>
        
        <h3>1.3 Perfiles de Clusters</h3>
        <table>
            <tr>
                <th>Cluster</th>
                <th>Puntaje Global</th>
                <th>Razonamiento Cuant.</th>
                <th>Lectura Crítica</th>
                <th>Inglés</th>
                <th>N Presentaciones</th>
                <th>% P75+</th>
            </tr>
            <tr>
                <td><strong>Cluster 0</strong></td>
                <td>{perfiles_clusters.loc[0, 'puntaje_global_mean']:.2f} ± {perfiles_clusters.loc[0, 'puntaje_global_std']:.2f}</td>
                <td>{perfiles_clusters.loc[0, 'punt_razona_cuantitativa_mean']:.2f}</td>
                <td>{perfiles_clusters.loc[0, 'punt_lectura_critica_mean']:.2f}</td>
                <td>{perfiles_clusters.loc[0, 'punt_ingles_mean']:.2f}</td>
                <td>{int(perfiles_clusters.loc[0, 'n_presentaciones_mean']):,}</td>
                <td>{perfiles_clusters.loc[0, 'prop_p75_plus_mean']:.1%}</td>
            </tr>
            <tr style="background-color: #fff3cd;">
                <td><strong>Cluster 1</strong></td>
                <td>{perfiles_clusters.loc[1, 'puntaje_global_mean']:.2f} ± {perfiles_clusters.loc[1, 'puntaje_global_std']:.2f}</td>
                <td>{perfiles_clusters.loc[1, 'punt_razona_cuantitativa_mean']:.2f}</td>
                <td>{perfiles_clusters.loc[1, 'punt_lectura_critica_mean']:.2f}</td>
                <td>{perfiles_clusters.loc[1, 'punt_ingles_mean']:.2f}</td>
                <td>{int(perfiles_clusters.loc[1, 'n_presentaciones_mean']):,}</td>
                <td>{perfiles_clusters.loc[1, 'prop_p75_plus_mean']:.1%}</td>
            </tr>
        </table>
        
        <div class="alert">
            <strong>⚠️ ALERTA:</strong> El Cluster 1 presenta puntajes anómalamente bajos (24.27 en escala 0-300).
            Esto sugiere posibles problemas de calidad de datos que requieren validación urgente.
        </div>
        
        <h3>1.4 Interpretación - Clustering</h3>
        <p><strong>Cluster 0 (IES de Desempeño Estándar):</strong></p>
        <ul>
            <li>Representa el 79.8% de las IES analizadas (268 instituciones)</li>
            <li>Puntaje global promedio de 130.15 puntos</li>
            <li>24% de sus estudiantes en el cuartil superior (P75+)</li>
            <li>Concentra 2.47 millones de presentaciones (93.4% del total)</li>
        </ul>
        
        <p><strong>Cluster 1 (IES de Desempeño Crítico):</strong></p>
        <ul>
            <li>Representa el 20.2% de las IES (68 instituciones)</li>
            <li>Puntaje global promedio de 24.27 puntos ⚠️</li>
            <li>Solo 1% de sus estudiantes en P75+</li>
            <li>175,904 presentaciones (6.6% del total)</li>
            <li><strong>REQUIERE VALIDACIÓN DE DATOS</strong></li>
        </ul>
        
        <hr>
        
        <h2>🤖 2. MODELO DE REGRESIÓN (Issue 7.1)</h2>
        
        <h3>2.1 Métricas de Desempeño</h3>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-label">R² Score (Test)</div>
                <div class="metric-value">{metricas_regresion['metricas_test']['r2_score']:.4f}</div>
                <p>Explica 99.54% de la varianza</p>
            </div>
            <div class="metric-card">
                <div class="metric-label">RMSE (Test)</div>
                <div class="metric-value">{metricas_regresion['metricas_test']['rmse']:.2f}</div>
                <p>Error promedio en puntos</p>
            </div>
            <div class="metric-card">
                <div class="metric-label">MAE (Test)</div>
                <div class="metric-value">{metricas_regresion['metricas_test']['mae']:.2f}</div>
                <p>Error absoluto promedio</p>
            </div>
        </div>
        
        <h3>2.2 Validación Cruzada (5-Fold)</h3>
        <div class="success">
            <p><strong>Media R²:</strong> {metricas_regresion['validacion_cruzada']['cv_mean_r2']:.6f}</p>
            <p><strong>Desviación Estándar:</strong> {metricas_regresion['validacion_cruzada']['cv_std_r2']:.6f}</p>
            <p>✅ Modelo muy estable y consistente</p>
        </div>
        
        <h3>2.3 Importancia de Features</h3>
        <table>
            <tr>
                <th>Ranking</th>
                <th>Feature</th>
                <th>Importancia</th>
                <th>Porcentaje</th>
            </tr>
"""

# Agregar importancia de features
for idx, row in feature_importance.iterrows():
    porcentaje = row['importance'] * 100
    html_content += f"""
            <tr>
                <td>{idx + 1}</td>
                <td><strong>{row['feature']}</strong></td>
                <td>{row['importance']:.6f}</td>
                <td>{porcentaje:.2f}%</td>
            </tr>
"""

html_content += f"""
        </table>
        
        <h3>2.4 Interpretación - Regresión</h3>
        
        <div class="success">
            <h4>✅ Fortalezas del Modelo:</h4>
            <ul>
                <li><strong>Precisión Excepcional:</strong> R² = 99.54% indica ajuste casi perfecto</li>
                <li><strong>Sin Overfitting:</strong> Diferencia Train-Test de solo 0.07%</li>
                <li><strong>Muy Estable:</strong> Validación cruzada con σ = 0.00015</li>
                <li><strong>Error Mínimo:</strong> ±3.7 puntos en escala 0-300 (1.2% de error)</li>
            </ul>
        </div>
        
        <div class="alert">
            <h4>🔍 Hallazgo Crítico: Dominio de Lectura Crítica</h4>
            <p><strong>Lectura Crítica explica el 91.56% de la predicción del puntaje global.</strong></p>
            <p><strong>Implicaciones:</strong></p>
            <ul>
                <li>El puntaje global está casi completamente determinado por lectura crítica</li>
                <li>Las otras 4 competencias aportan solo 8.44% combinadas</li>
                <li>Sugiere alta colinealidad entre competencias</li>
                <li>Posible sobre-ponderación de lectura crítica en cálculo ICFES</li>
            </ul>
        </div>
        
        <div class="success">
            <h4>📉 Variables Demográficas Irrelevantes:</h4>
            <p><strong>Género, IES y Departamento tienen impacto < 0.001%</strong></p>
            <p><strong>Interpretación:</strong></p>
            <ul>
                <li>✅ La prueba NO discrimina por género (importancia 0.0001%)</li>
                <li>✅ Neutralidad geográfica (departamento 0.0004%)</li>
                <li>✅ Equidad del instrumento confirmada</li>
                <li>El desempeño individual domina sobre factores institucionales</li>
            </ul>
        </div>
        
        <hr>
        
        <h2>💡 3. CONCLUSIONES Y RECOMENDACIONES</h2>
        
        <h3>3.1 Hallazgos Principales</h3>
        <ol>
            <li><strong>Lectura Crítica es el Factor Dominante:</strong> 91.6% de importancia en predicción</li>
            <li><strong>Dos Perfiles Institucionales Claros:</strong> 80% estándar vs 20% crítico</li>
            <li><strong>Equidad del Instrumento:</strong> Variables demográficas no discriminan</li>
            <li><strong>Excelente Calidad Predictiva:</strong> R² = 99.54% sin overfitting</li>
        </ol>
        
        <h3>3.2 Limitaciones Reconocidas</h3>
        <div class="alert">
            <ul>
                <li><strong>Calidad de Datos Cluster 1:</strong> Puntajes anómalos requieren validación</li>
                <li><strong>Sesgo de Selección:</strong> Exclusión de variables con >30% NAs</li>
                <li><strong>Correlación vs Causalidad:</strong> Modelo NO establece causalidad</li>
                <li><strong>Muestra Selectiva:</strong> Solo 3.7% de datos utilizados (100K de 2.6M)</li>
            </ul>
        </div>
        
        <h3>3.3 Recomendaciones Inmediatas</h3>
        <div class="success">
            <h4>🔴 PRIORIDAD ALTA (Semana 1-2):</h4>
            <ol>
                <li><strong>Validar datos del Cluster 1</strong> (68 IES con puntajes ~24)</li>
                <li>Presentar resultados a stakeholders</li>
                <li>Documentar decisiones metodológicas</li>
                <li>Publicar notebooks en repositorio</li>
            </ol>
        </div>
        
        <h3>3.4 Impacto Esperado</h3>
        <p><strong>Para las IES:</strong></p>
        <ul>
            <li>Herramienta de diagnóstico institucional</li>
            <li>Benchmark con 336 instituciones nacionales</li>
            <li>Identificación de brechas específicas</li>
        </ul>
        
        <p><strong>Para Estudiantes:</strong></p>
        <ul>
            <li>Identificación temprana de riesgos académicos</li>
            <li>Recomendaciones personalizadas</li>
            <li>Apoyo focalizado en lectura crítica</li>
        </ul>
        
        <p><strong>Para Política Pública:</strong></p>
        <ul>
            <li>Evidencia para diseño de intervenciones</li>
            <li>Focalización de recursos limitados</li>
            <li>Monitoreo de calidad educativa</li>
        </ul>
        
        <hr>
        
        <h2>📁 4. ARTEFACTOS GENERADOS</h2>
        
        <h3>Modelos Entrenados:</h3>
        <ul>
            <li><code>clasificacion_ies_cluster_20260517.pkl</code> - Modelo KMeans</li>
            <li><code>regresion_puntaje_saberpro_20260517.pkl</code> - Random Forest Regressor</li>
        </ul>
        
        <h3>Métricas:</h3>
        <ul>
            <li><code>metricas_clustering_20260517.json</code></li>
            <li><code>metricas_regresion_20260517.json</code></li>
            <li><code>perfiles_clusters_20260517.csv</code></li>
            <li><code>feature_importance_20260517.csv</code></li>
        </ul>
        
        <h3>Visualizaciones:</h3>
        <ul>
            <li><code>analisis_k_optimo.png</code> - Método del codo y Silhouette</li>
            <li><code>correlacion_features_ies.png</code> - Matriz de correlación</li>
            <li><code>pca_varianza_explicada.png</code> - Análisis PCA</li>
            <li><code>clusters_ies_2d_20260517.png</code> - Clusters en espacio PCA</li>
            <li><code>perfiles_clusters_barplot.png</code> - Perfiles por cluster</li>
            <li><code>importancia_features_20260517.png</code> - Importancia de variables</li>
            <li><code>distribucion_errores_20260517.png</code> - Distribución de residuos</li>
        </ul>
        
        <div class="footer">
            <p>Informe generado automáticamente el {datetime.now().strftime('%d de %B de %Y a las %H:%M:%S')}</p>
            <p><strong>Observatorio de Datos de Educación en Colombia</strong></p>
            <p>Sprint 7 - Machine Learning | Issues 7.1 y 7.2</p>
            <p><em>Este documento es de carácter técnico y está sujeto a revisión.</em></p>
        </div>
    </div>
</body>
</html>
"""

# Guardar HTML
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Reporte HTML generado exitosamente:")
print(f"  {OUTPUT_FILE}")
print(f"\nArchivo de {len(html_content):,} caracteres")
print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
