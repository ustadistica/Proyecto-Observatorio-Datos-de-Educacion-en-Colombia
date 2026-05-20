#!/usr/bin/env python3
"""
regresion_saberpro.py - Issue 7.1: Predicción de Puntajes Saber Pro
===================================================================
Modelo de regresión para predecir puntaje global Saber Pro usando:
  - Características del estudiante (género, estrato, área residencia)
  - Institución y departamento de presentación
  - Puntajes de módulos individuales

Salidas:
  - Modelo: artifacts/modelos/regresion_puntaje_saberpro_YYYYMMDD.pkl
  - Métricas: artifacts/metricas/metricas_regresion_YYYYMMDD.json
  - Visualizaciones: artifacts/visualizaciones/

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

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SABER_PRO_PATH = PROJECT_ROOT / "datos" / "processed" / "saber_pro" / "saber_pro_consolidado.parquet"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODELOS_DIR = ARTIFACTS_DIR / "modelos"
METRICAS_DIR = ARTIFACTS_DIR / "metricas"
VIZ_DIR = ARTIFACTS_DIR / "visualizaciones"

FECHA = datetime.now().strftime("%Y%m%d")

# Parámetros del modelo
TEST_SIZE = 0.2
RANDOM_STATE = 42
N_ESTIMATORS = 100
MAX_DEPTH = 10

# Features a utilizar
FEATURES_NUMERICAS = [
    'punt_razona_cuantitativa',
    'punt_lectura_critica',
    'punt_ingles',
    'punt_comuni_escrita',
    'punt_comp_ciudadanas'
]

FEATURES_CATEGORICAS = [
    'estu_genero',
    'fami_estratovivienda',
    'estu_area_residencia',
    'inst_nombre_institucion',
    'estu_depto_presentacion'
]

TARGET = 'puntaje_global'

# ============================================================================
# FUNCIONES
# ============================================================================

def cargar_y_preparar_datos():
    """
    Carga Saber Pro y prepara dataset para modelado.
    
    Returns:
        tuple: (X, y, feature_names, encoders)
    """
    print("📥 Cargando datos de Saber Pro...")
    
    df = pd.read_parquet(SABER_PRO_PATH)
    print(f"   Total registros: {len(df):,}")
    
    # Filtrar registros con target válido
    df = df[df[TARGET].notna()].copy()
    print(f"   Registros con puntaje global: {len(df):,}")
    
    # Seleccionar features disponibles
    features_disponibles = []
    for feat in FEATURES_NUMERICAS + FEATURES_CATEGORICAS:
        if feat in df.columns:
            features_disponibles.append(feat)
        else:
            print(f"   ⚠️ Feature no disponible: {feat}")
    
    # Preparar dataset
    df_model = df[features_disponibles + [TARGET]].dropna()
    print(f"   Registros después de dropna: {len(df_model):,}")
    
    return df_model, features_disponibles


def codificar_categoricas(df, features_categoricas):
    """
    Codifica variables categóricas usando LabelEncoder.
    
    Args:
        df: DataFrame con datos
        features_categoricas: Lista de columnas categóricas
    
    Returns:
        tuple: (df_encoded, encoders_dict)
    """
    print("\n🔧 Codificando variables categóricas...")
    
    df_encoded = df.copy()
    encoders = {}
    
    for col in features_categoricas:
        if col in df.columns:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
            print(f"   {col}: {len(le.classes_)} categorías únicas")
    
    return df_encoded, encoders


def entrenar_modelo(X_train, X_test, y_train, y_test):
    """
    Entrena Random Forest Regressor y evalúa.
    
    Args:
        X_train, X_test, y_train, y_test: Splits de train/test
    
    Returns:
        tuple: (modelo, metricas)
    """
    print(f"\n🤖 Entrenando Random Forest Regressor...")
    print(f"   Train: {len(X_train):,} | Test: {len(X_test):,}")
    
    # Modelo
    rf = RandomForestRegressor(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1
    )
    
    rf.fit(X_train, y_train)
    
    # Predicciones
    y_train_pred = rf.predict(X_train)
    y_test_pred = rf.predict(X_test)
    
    # Métricas Train
    r2_train = r2_score(y_train, y_train_pred)
    rmse_train = np.sqrt(mean_squared_error(y_train, y_train_pred))
    mae_train = mean_absolute_error(y_train, y_train_pred)
    mape_train = np.mean(np.abs((y_train - y_train_pred) / y_train)) * 100
    
    # Métricas Test
    r2_test = r2_score(y_test, y_test_pred)
    rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
    mae_test = mean_absolute_error(y_test, y_test_pred)
    mape_test = np.mean(np.abs((y_test - y_test_pred) / y_test)) * 100
    
    print(f"\n📊 Métricas de Evaluación:")
    print(f"   TRAIN - R²: {r2_train:.4f} | RMSE: {rmse_train:.2f} | MAE: {mae_train:.2f} | MAPE: {mape_train:.2f}%")
    print(f"   TEST  - R²: {r2_test:.4f} | RMSE: {rmse_test:.2f} | MAE: {mae_test:.2f} | MAPE: {mape_test:.2f}%")
    
    metricas = {
        "train": {
            "r2_score": float(r2_train),
            "rmse": float(rmse_train),
            "mae": float(mae_train),
            "mape": float(mape_train)
        },
        "test": {
            "r2_score": float(r2_test),
            "rmse": float(rmse_test),
            "mae": float(mae_test),
            "mape": float(mape_test)
        }
    }
    
    return rf, metricas, y_test_pred


def validacion_cruzada(modelo, X, y):
    """
    Realiza validación cruzada k-fold.
    
    Args:
        modelo: Modelo entrenado
        X, y: Features y target
    
    Returns:
        dict: Resultados de CV
    """
    print("\n🔄 Validación cruzada (5-fold)...")
    
    cv_scores = cross_val_score(modelo, X, y, cv=5, scoring='r2', n_jobs=-1)
    
    print(f"   Scores: {cv_scores}")
    print(f"   Media: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    return {
        "cv_folds": 5,
        "cv_mean_r2": float(cv_scores.mean()),
        "cv_std_r2": float(cv_scores.std()),
        "cv_scores": cv_scores.tolist()
    }


def analizar_feature_importance(modelo, feature_names):
    """
    Analiza y visualiza importancia de features.
    
    Args:
        modelo: Random Forest entrenado
        feature_names: Nombres de features
    
    Returns:
        pd.DataFrame: Feature importance
    """
    print("\n📈 Analizando importancia de features...")
    
    importances = pd.DataFrame({
        'feature': feature_names,
        'importance': modelo.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n   Top 10 features más importantes:")
    print(importances.head(10).to_string(index=False))
    
    # Visualización
    fig, ax = plt.subplots(figsize=(10, 6))
    top_15 = importances.head(15)
    ax.barh(range(len(top_15)), top_15['importance'], color='steelblue')
    ax.set_yticks(range(len(top_15)))
    ax.set_yticklabels(top_15['feature'])
    ax.set_xlabel('Importancia', fontsize=12)
    ax.set_title('Top 15 Features - Importancia en el Modelo', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    plt.tight_layout()
    
    viz_path = VIZ_DIR / f"importancia_features_{FECHA}.png"
    fig.savefig(viz_path, dpi=150, bbox_inches='tight')
    print(f"   Gráfico guardado: {viz_path}")
    plt.close(fig)
    
    return importances


def visualizar_predicciones(y_test, y_pred):
    """
    Visualiza predicciones vs valores reales.
    
    Args:
        y_test: Valores reales
        y_pred: Valores predichos
    """
    print("\n📊 Generando visualización de predicciones...")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Scatter plot: Real vs Predicho
    axes[0].scatter(y_test, y_pred, alpha=0.3, s=10, color='steelblue')
    axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 
                 'r--', lw=2, label='Predicción perfecta')
    axes[0].set_xlabel('Puntaje Real', fontsize=12)
    axes[0].set_ylabel('Puntaje Predicho', fontsize=12)
    axes[0].set_title('Puntaje Real vs Predicho', fontsize=13, fontweight='bold')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    # Histograma de errores
    errores = y_test - y_pred
    axes[1].hist(errores, bins=50, color='coral', edgecolor='black', alpha=0.7)
    axes[1].axvline(0, color='red', linestyle='--', linewidth=2, label='Error = 0')
    axes[1].set_xlabel('Error (Real - Predicho)', fontsize=12)
    axes[1].set_ylabel('Frecuencia', fontsize=12)
    axes[1].set_title('Distribución de Errores', fontsize=13, fontweight='bold')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    
    viz_path = VIZ_DIR / f"distribucion_errores_{FECHA}.png"
    fig.savefig(viz_path, dpi=150, bbox_inches='tight')
    print(f"   Gráfico guardado: {viz_path}")
    plt.close(fig)


def guardar_resultados(modelo, encoders, metricas, cv_results, feature_importance, feature_names):
    """
    Guarda modelo y métricas en artifacts/.
    
    Args:
        modelo: Random Forest entrenado
        encoders: Diccionario de encoders
        metricas: Métricas de evaluación
        cv_results: Resultados de validación cruzada
        feature_importance: DataFrame de importancias
        feature_names: Nombres de features
    """
    print("\n💾 Guardando resultados...")
    
    # Guardar modelo y encoders
    modelo_path = MODELOS_DIR / f"regresion_puntaje_saberpro_{FECHA}.pkl"
    with open(modelo_path, 'wb') as f:
        pickle.dump({'modelo': modelo, 'encoders': encoders}, f)
    print(f"   Modelo guardado: {modelo_path}")
    
    # Guardar métricas completas
    metricas_completas = {
        "metadata": {
            "modelo": "random_forest_puntaje_saberpro",
            "fecha_entrenamiento": datetime.now().isoformat(),
            "autor": "German",
            "issue": "Sprint 7.1 - Predicción puntajes Saber Pro",
            "descripcion": "Modelo de regresión para predecir puntaje global Saber Pro"
        },
        "datos": {
            "target_variable": TARGET,
            "periodo": "2015-2024"
        },
        "hiperparametros": {
            "algoritmo": "RandomForestRegressor",
            "n_estimators": N_ESTIMATORS,
            "max_depth": MAX_DEPTH,
            "random_state": RANDOM_STATE
        },
        "metricas_train": metricas["train"],
        "metricas_test": metricas["test"],
        "validacion_cruzada": cv_results,
        "feature_importance_top10": feature_importance.head(10).set_index('feature')['importance'].to_dict(),
        "features_utilizadas": feature_names
    }
    
    metricas_path = METRICAS_DIR / f"metricas_regresion_{FECHA}.json"
    with open(metricas_path, 'w') as f:
        json.dump(metricas_completas, f, indent=2)
    print(f"   Métricas guardadas: {metricas_path}")
    
    # Guardar feature importance como CSV
    importance_csv = METRICAS_DIR / f"feature_importance_{FECHA}.csv"
    feature_importance.to_csv(importance_csv, index=False)
    print(f"   Feature importance guardado: {importance_csv}")


def main():
    """Función principal del pipeline de regresión."""
    print("="*70)
    print("PREDICCIÓN DE PUNTAJES SABER PRO - Sprint 7.1")
    print("="*70)
    
    # 1. Cargar datos
    df_model, features_disponibles = cargar_y_preparar_datos()
    
    # 2. Separar categóricas y numéricas
    features_cat = [f for f in FEATURES_CATEGORICAS if f in features_disponibles]
    features_num = [f for f in FEATURES_NUMERICAS if f in features_disponibles]
    
    # 3. Codificar categóricas
    df_encoded, encoders = codificar_categoricas(df_model, features_cat)
    
    # 4. Preparar X, y
    all_features = features_num + features_cat
    X = df_encoded[all_features].values
    y = df_encoded[TARGET].values
    
    # 5. Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    
    # 6. Entrenar modelo
    modelo, metricas, y_pred = entrenar_modelo(X_train, X_test, y_train, y_test)
    
    # 7. Validación cruzada
    cv_results = validacion_cruzada(modelo, X, y)
    
    # 8. Feature importance
    feature_importance = analizar_feature_importance(modelo, all_features)
    
    # 9. Visualizaciones
    visualizar_predicciones(y_test, y_pred)
    
    # 10. Guardar resultados
    guardar_resultados(modelo, encoders, metricas, cv_results, feature_importance, all_features)
    
    print("\n✅ Pipeline completado exitosamente!")
    print(f"   Revisa artifacts/ para ver los resultados.")


if __name__ == "__main__":
    main()
