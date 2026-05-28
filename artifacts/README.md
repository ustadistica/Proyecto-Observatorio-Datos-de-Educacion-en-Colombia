# Artifacts - Modelos y Métricas de Machine Learning

Este directorio almacena los artefactos generados por los modelos de machine learning del proyecto (Sprint 7).

## Estructura

```
artifacts/
├── modelos/              # Modelos entrenados serializados (.pkl)
├── metricas/             # Métricas de evaluación (.json, .csv)
├── visualizaciones/      # Gráficos y plots (.png, .pdf)
└── reportes/             # Informes técnicos de modelos (.md, .html)
```

## Convenciones de Nombres

### Modelos (`modelos/`)
- `clasificacion_ies_cluster_YYYYMMDD.pkl` - Modelo de clustering K-means/DBSCAN para IES
- `regresion_puntaje_saberpro_YYYYMMDD.pkl` - Modelo de regresión (Random Forest/XGBoost)
- `scaler_features_YYYYMMDD.pkl` - Escalador para normalización de features
- `encoder_categoricas_YYYYMMDD.pkl` - Encoder para variables categóricas

### Métricas (`metricas/`)
- `metricas_clasificacion_YYYYMMDD.json` - Precision, Recall, F1, AUC
- `metricas_regresion_YYYYMMDD.json` - R², RMSE, MAE, MAPE
- `metricas_clustering_YYYYMMDD.json` - Silhouette, Davies-Bouldin, Calinski-Harabasz
- `feature_importance_YYYYMMDD.csv` - Importancia de variables
- `validacion_cruzada_YYYYMMDD.csv` - Resultados de CV

### Visualizaciones (`visualizaciones/`)
- `clusters_ies_2d_YYYYMMDD.png` - Proyección 2D de clusters (PCA/t-SNE)
- `importancia_features_YYYYMMDD.png` - Gráfico de importancia
- `distribucion_errores_YYYYMMDD.png` - Histograma de residuos
- `matriz_confusion_YYYYMMDD.png` - Matriz de confusión
- `curvas_aprendizaje_YYYYMMDD.png` - Learning curves

### Reportes (`reportes/`)
- `informe_modelo_clustering_YYYYMMDD.md` - Documentación técnica clustering
- `informe_modelo_regresion_YYYYMMDD.md` - Documentación técnica regresión
- `benchmarks_modelos_YYYYMMDD.csv` - Comparación de modelos

## Issues Asociados (Sprint 7)

- **Issue 7.1:** Predicción de puntajes Saber Pro → `regresion_puntaje_saberpro`
- **Issue 7.2:** Clustering IES por desempeño → `clasificacion_ies_cluster`
- **Issue 7.3:** Predicción tasa de graduación → `regresion_graduacion` (si se implementa)

## Métricas de Evaluación

### Clasificación / Clustering
```json
{
  "modelo": "kmeans_ies",
  "fecha": "2026-05-17",
  "silhouette_score": 0.XX,
  "davies_bouldin_index": X.XX,
  "calinski_harabasz_score": XXX.XX,
  "n_clusters": X,
  "samples_per_cluster": [XX, XX, XX]
}
```

### Regresión
```json
{
  "modelo": "random_forest_saberpro",
  "fecha": "2026-05-17",
  "r2_score": 0.XX,
  "rmse": XX.XX,
  "mae": XX.XX,
  "mape": XX.XX,
  "cv_mean_r2": 0.XX,
  "cv_std_r2": 0.XX
}
```

## Uso

Los modelos se cargan con:

```python
import pickle
from pathlib import Path

ARTIFACTS = Path("artifacts")

# Cargar modelo
with open(ARTIFACTS / "modelos" / "regresion_puntaje_saberpro_20260517.pkl", "rb") as f:
    modelo = pickle.load(f)

# Cargar métricas
import json
with open(ARTIFACTS / "metricas" / "metricas_regresion_20260517.json", "r") as f:
    metricas = json.load(f)
```

## Versionado

- Usar fecha en formato `YYYYMMDD` para versionar artefactos
- Mantener máximo 3 versiones por tipo de modelo
- Documentar cambios significativos en el reporte asociado

## Referencias

- Scikit-learn: https://scikit-learn.org/
- XGBoost: https://xgboost.readthedocs.io/
- Clustering validation: https://scikit-learn.org/stable/modules/clustering.html#clustering-evaluation
