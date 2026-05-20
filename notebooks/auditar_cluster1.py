#!/usr/bin/env python3
"""
Script para auditar datos del Cluster 1 - Detectar problemas de calidad
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path

print("="*80)
print("AUDITORIA DE DATOS - CLUSTER 1")
print("="*80)

# Cargar modelo
with open('artifacts/modelos/clasificacion_ies_cluster_20260517.pkl', 'rb') as f:
    modelo_clustering = pickle.load(f)

# Cargar dataset original
print("\nCargando datos...")
df_saberpro = pd.read_parquet('datos/processed/saber_pro/saber_pro_consolidado.parquet')
print(f"Dataset: {len(df_saberpro):,} registros x {len(df_saberpro.columns)} columnas")

# Crear features por IES
print("\nCreando features por IES...")
features_ies = df_saberpro.groupby('nombre_ies').agg({
    'puntaje_global': 'mean',
    'punt_razona_cuantitativa': 'mean',
    'punt_lectura_critica': 'mean',
    'punt_ingles': 'mean',
    'estu_consecutivo': 'count'
}).rename(columns={'estu_consecutivo': 'n_presentaciones'})

# Calcular prop_p75_plus
p75_global = df_saberpro['puntaje_global'].quantile(0.75)
df_temp = df_saberpro[['nombre_ies', 'puntaje_global']].copy()
df_temp['es_p75_plus'] = (df_temp['puntaje_global'] >= p75_global).astype(int)
prop_p75 = df_temp.groupby('nombre_ies')['es_p75_plus'].mean().rename('prop_p75_plus')
features_ies = features_ies.join(prop_p75)

# Filtrar IES con >= 100 presentaciones
features_ies = features_ies[features_ies['n_presentaciones'] >= 100].copy()

print(f"IES analizadas: {len(features_ies)}")

# Agregar labels de clustering
features_ies['cluster'] = modelo_clustering['labels']

# Analizar Cluster 1
print("\n" + "="*80)
print("CLUSTER 1: ANÁLISIS DETALLADO")
print("="*80)

cluster1 = features_ies[features_ies['cluster'] == 1].copy()
print(f"\nNúmero de IES en Cluster 1: {len(cluster1)}")

print("\n--- ESTADÍSTICAS DESCRIPTIVAS ---")
print(cluster1.describe())

print("\n--- IES DEL CLUSTER 1 ---")
cluster1_sorted = cluster1.sort_values('puntaje_global')
print(cluster1_sorted[['puntaje_global', 'punt_razona_cuantitativa', 
                        'punt_lectura_critica', 'punt_ingles', 'n_presentaciones']])

# Analizar valores extremadamente bajos
print("\n" + "="*80)
print("DIAGNÓSTICO: ¿SON ERRORES DE DATOS?")
print("="*80)

puntajes_muy_bajos = cluster1[cluster1['puntaje_global'] < 50]
print(f"\nIES con puntaje < 50: {len(puntajes_muy_bajos)} de {len(cluster1)}")
print(f"Porcentaje: {len(puntajes_muy_bajos)/len(cluster1)*100:.1f}%")

if len(puntajes_muy_bajos) > 0:
    print("\nIES con puntajes anómalamente bajos:")
    print(puntajes_muy_bajos[['puntaje_global', 'n_presentaciones']])
    
    # Verificar si son ceros
    ceros = cluster1[cluster1['puntaje_global'] < 1]
    print(f"\nIES con puntaje ~0: {len(ceros)}")
    if len(ceros) > 0:
        print("NOMBRES DE IES CON PUNTAJE ~0:")
        print(ceros.index.tolist())

# Verificar datos originales de una IES del Cluster 1
print("\n" + "="*80)
print("VERIFICACIÓN EN DATOS ORIGINALES")
print("="*80)

ies_ejemplo = cluster1.index[0]
print(f"\nIES de ejemplo: {ies_ejemplo}")
datos_ies = df_saberpro[df_saberpro['nombre_ies'] == ies_ejemplo]
print(f"Registros: {len(datos_ies)}")
print(f"\nEstadísticas del puntaje_global:")
print(datos_ies['puntaje_global'].describe())
print(f"\nValores únicos de puntaje_global:")
valores_unicos = datos_ies['puntaje_global'].value_counts().head(10)
print(valores_unicos)

# Contar NAs originales
print(f"\nNAs en puntaje_global: {datos_ies['puntaje_global'].isna().sum()}")
print(f"Zeros en puntaje_global: {(datos_ies['puntaje_global'] == 0).sum()}")
print(f"Valores < 50: {(datos_ies['puntaje_global'] < 50).sum()}")

# RECOMENDACIÓN
print("\n" + "="*80)
print("RECOMENDACIÓN")
print("="*80)

if len(puntajes_muy_bajos) > 30:  # Si más del 50% tiene puntajes bajos
    print("\n⚠️ PROBLEMA CRÍTICO DETECTADO:")
    print(f"  - {len(puntajes_muy_bajos)} IES ({len(puntajes_muy_bajos)/len(cluster1)*100:.1f}%) tienen puntajes < 50")
    print("  - Esto es anormalmente bajo en escala 0-300")
    print("\n📋 POSIBLES CAUSAS:")
    print("  1. Valores NA codificados como 0 en dataset original")
    print("  2. IES con muy pocos datos válidos")
    print("  3. Error en proceso de consolidación")
    print("\n🔴 ACCIÓN REQUERIDA:")
    print("  1. Revisar dataset raw de Saber Pro")
    print("  2. Validar proceso de limpieza de datos")
    print("  3. Verificar con estadísticas oficiales ICFES")
    print("  4. Considerar excluir IES con < 500 presentaciones")
else:
    print("\n✅ Cluster 1 parece tener datos válidos pero bajo desempeño real")
    print("   Requiere intervención educativa")

print("\n" + "="*80)
