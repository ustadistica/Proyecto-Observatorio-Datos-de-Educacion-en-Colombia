"""
Script para analizar los valores de departamentos en las bases de datos del Saber Pro
"""
import pandas as pd
import glob

# Cargar todos los archivos parquet individuales
archivos = glob.glob('datos_procesados/saber_pro_*.parquet')
archivos_individuales = [f for f in archivos if 'consolidado' not in f]

print("=" * 60)
print("ANÁLISIS DE DEPARTAMENTOS - SABER PRO")
print("=" * 60)

# Cargar y analizar
for archivo in sorted(archivos_individuales):
    df = pd.read_parquet(archivo)
    if 'estu_depto_presentacion' in df.columns:
        unicos = df['estu_depto_presentacion'].dropna().unique()
        print(f"\n{archivo}:")
        print(f"  Total únicos: {len(unicos)}")
        print(f"  Valores: {sorted([str(v) for v in unicos])}")

# Análisis consolidado
print("\n" + "=" * 60)
print("ANÁLISIS CONSOLIDADO")
print("=" * 60)

consolidado = pd.concat([pd.read_parquet(f) for f in archivos_individuales])
deptos = consolidado['estu_depto_presentacion'].dropna().unique()
print(f"\nTotal departamentos únicos: {len(deptos)}")
print("\nLista completa:")
for depto in sorted([str(d) for d in deptos]):
    count = len(consolidado[consolidado['estu_depto_presentacion'] == depto])
    print(f"  {depto}: {count:,} registros")