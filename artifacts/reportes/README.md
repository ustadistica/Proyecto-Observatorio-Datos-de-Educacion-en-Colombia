# Reportes Técnicos - Sprint 7 Machine Learning

Este directorio contiene los informes técnicos generados durante el Sprint 7 del Observatorio de Datos de Educación en Colombia.

## Contenido

### 📊 Informe Principal
- **`informe_sprint_7_ml.html`** - Informe técnico completo
  - Justificación metodológica de clustering
  - Análisis de viabilidad (K óptimo, PCA, Silhouette)
  - Documentación del modelo de regresión Random Forest
  - Métricas de evaluación e interpretación
  - Aplicaciones y próximos pasos

## Issues Documentados

### ✅ Issue 7.1: Predicción de Puntajes Saber Pro
**Estado:** COMPLETO

**Descripción:** Modelo de regresión Random Forest para predecir puntaje global Saber Pro.

**Artefactos Generados:**
- Modelo: `artifacts/modelos/regresion_puntaje_saberpro_YYYYMMDD.pkl`
- Métricas: `artifacts/metricas/metricas_regresion_YYYYMMDD.json`
- Feature Importance: `artifacts/metricas/feature_importance_YYYYMMDD.csv`
- Visualizaciones:
  - `importancia_features_YYYYMMDD.png`
  - `distribucion_errores_YYYYMMDD.png`

**Métricas Esperadas:**
- R² ≥ 0.70 (varianza explicada)
- RMSE < 15 puntos
- MAE < 10 puntos
- MAPE < 8%

**Features Utilizadas:**
- Numéricas: puntajes de módulos Saber Pro
- Categóricas: género, estrato, área residencia, IES, departamento

---

### ✅ Issue 7.2: Clustering de IES por Desempeño
**Estado:** COMPLETO

**Descripción:** Clustering K-means de instituciones educativas superiores según desempeño en Saber Pro.

**Artefactos Generados:**
- Modelo: `artifacts/modelos/clasificacion_ies_cluster_YYYYMMDD.pkl`
- Métricas: `artifacts/metricas/metricas_clustering_YYYYMMDD.json`
- Perfiles: `artifacts/metricas/perfiles_clusters_YYYYMMDD.csv`
- Visualizaciones:
  - `correlacion_features_ies.png`
  - `analisis_k_optimo.png`
  - `pca_varianza_explicada.png`
  - `clusters_ies_2d_YYYYMMDD.png`
  - `perfiles_clusters_barplot.png`

**Análisis Realizado:**
1. **Determinación de K óptimo:**
   - Método del codo (elbow method)
   - Silhouette Score (maximizar)
   - Davies-Bouldin Index (minimizar)

2. **Análisis de Componentes Principales (PCA):**
   - Reducción dimensional para visualización
   - Interpretación de varianza explicada
   - Proyección 2D de clusters

3. **Viabilidad del Clustering:**
   - Criterios: Silhouette ≥ 0.40, DB ≤ 1.5
   - Validación por estabilidad (n_init=20)
   - Interpretabilidad de perfiles

**Features por IES:**
- Puntaje global promedio
- Puntajes promedio por módulo (razonamiento, lectura, inglés)
- Número de presentaciones
- Proporción en percentil 75+ (prop_p75_plus)

---

## Notebook Interactivo

El análisis completo ejecutable está disponible en:
```
notebooks/sprint_7_machine_learning.ipynb
```

**Contenido del Notebook:**
1. Carga y exploración de datos
2. Análisis completo de clustering
   - Determinación de K óptimo
   - PCA y visualización
   - Entrenamiento y evaluación
   - Perfiles de clusters
3. Modelo de regresión
   - Preparación de datos
   - Entrenamiento Random Forest
   - Feature importance
   - Validación cruzada
4. Conclusiones e interpretación

## Cómo Usar Este Informe

### Visualizar en Navegador
```bash
# Abrir informe HTML
start artifacts/reportes/informe_sprint_7_ml.html
```

### Cargar Modelos en Python
```python
import pickle
from pathlib import Path

ARTIFACTS = Path("artifacts")

# Cargar modelo de clustering
with open(ARTIFACTS / "modelos" / "clasificacion_ies_cluster_20260517.pkl", "rb") as f:
    modelo_cluster = pickle.load(f)

# Cargar modelo de regresión
with open(ARTIFACTS / "modelos" / "regresion_puntaje_saberpro_20260517.pkl", "rb") as f:
    modelo_regresion = pickle.load(f)

# Usar modelos
kmeans = modelo_cluster['modelo']
scaler = modelo_cluster['scaler']
rf = modelo_regresion['modelo']
```

### Cargar Métricas
```python
import json

with open(ARTIFACTS / "metricas" / "metricas_clustering_20260517.json") as f:
    metricas_cluster = json.load(f)

with open(ARTIFACTS / "metricas" / "metricas_regresion_20260517.json") as f:
    metricas_regresion = json.load(f)

print(f"Silhouette Score: {metricas_cluster['metricas_clustering']['silhouette_score']}")
print(f"R² Test: {metricas_regresion['metricas_test']['r2_score']}")
```

## Interpretación de Resultados

### Clustering de IES
Los clusters representan grupos homogéneos de instituciones con características similares:

- **Cluster Alto Desempeño:** IES con puntajes superiores al P75, alta concentración de estudiantes destacados
- **Cluster Medio-Alto:** IES con desempeño cercano o ligeramente superior al promedio nacional
- **Cluster Medio-Bajo:** IES con oportunidades de mejora, potencial de intervención
- **Cluster Masivo** (si K=4): IES grandes con alta variabilidad interna

**Aplicaciones:**
- Benchmarking entre instituciones del mismo grupo
- Identificación de mejores prácticas
- Focalización de políticas educativas
- Asignación diferenciada de recursos

### Modelo de Regresión
El modelo identifica factores clave que influyen en el desempeño:

**Importancia Esperada de Features:**
1. Puntajes de módulos (alta correlación con global)
2. Institución educativa (efecto IES)
3. Estrato socioeconómico
4. Departamento (diferencias regionales)

**Aplicaciones:**
- Predicción de puntajes esperados
- Análisis de brechas (real vs esperado)
- Identificación de IES con valor agregado
- Evaluación de impacto de programas

## Próximos Pasos

### Validación y Extensión
1. ✅ Validar resultados con expertos del dominio educativo
2. ✅ Comparar con acreditación institucional SNIES
3. ✅ Explorar modelos alternativos (XGBoost, LightGBM)
4. ✅ Incorporar features adicionales:
   - Acreditación institucional
   - Recursos y profesores por estudiante
   - Tasas de graduación por cohorte

### Análisis Temporal
1. ✅ Estudiar evolución de clusters año a año
2. ✅ Identificar IES que mejoran/empeoran
3. ✅ Analizar impacto de políticas educativas

### Interpretabilidad Avanzada
1. ✅ Aplicar SHAP values para explicación de predicciones
2. ✅ Análisis de contribución individual de features
3. ✅ Casos de estudio de IES específicas

## Limitaciones y Consideraciones

### Limitaciones Conocidas
1. **K-means asume clusters esféricos:** Puede no capturar formas complejas
2. **Datos agregados por IES:** Se pierde variabilidad interna
3. **Filtro de 100 presentaciones:** Excluye IES pequeñas
4. **Multicolinealidad en regresión:** Puntajes de módulos correlacionados con target

### Consideraciones Metodológicas
- Los modelos son descriptivos/predictivos, no causales
- La interpretación debe considerar contexto educativo
- Las métricas de validación son indicativas, no definitivas
- Se requiere validación con expertos del dominio

## Referencias

- MacQueen, J. (1967). "Some methods for classification and analysis of multivariate observations"
- Rousseeuw, P. J. (1987). "Silhouettes: A graphical aid to the interpretation and validation of cluster analysis"
- Breiman, L. (2001). "Random Forests". Machine Learning, 45(1), 5-32
- Jolliffe, I. T. (2002). "Principal Component Analysis" (2nd ed.)

## Contacto

**Proyecto:** Observatorio de Datos de Educación en Colombia  
**Autor:** German Chamorro  
**Fecha:** Mayo 17, 2026  
**Repositorio:** https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia

---

**Última actualización:** 2026-05-17
