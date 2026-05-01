import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configurar el estilo de graficos
plt.style.use('ggplot')
sns.set_theme(style="whitegrid")

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / 'datos' / 'processed' / 'eficiencia_universidades.csv'

def main():
    if not CSV_PATH.exists():
        print(f"Error: No se encontro el archivo {CSV_PATH}")
        return

    # Leer el dataset
    df = pd.read_csv(CSV_PATH)
    
    print("=== RESUMEN DE DATOS CRUZADOS ===")
    print(f"Total registros: {len(df)}")
    print(f"Años con cruce exitoso: {sorted(df['anio_proceso'].unique())}")
    print(f"Total universidades cruzadas: {df['institucion'].nunique()}\n")
    
    # 1. Top 10 Instituciones mas eficientes (Menor costo por graduado)
    # Promediar el costo_por_graduado_millones a lo largo de los años disponibles
    eficiencia_promedio = df.groupby('institucion', as_index=False).agg(
        costo_promedio=('costo_por_graduado_millones', 'mean'),
        total_graduados=('total_graduados', 'sum'),
        total_pagos=('pagos_millones', 'sum')
    )
    
    # Filtrar solo universidades con una cantidad representativa de graduados (> 1000 historicos)
    eficiencia_robusta = eficiencia_promedio[eficiencia_promedio['total_graduados'] > 1000].copy()
    
    # Ordenar por costo promedio (de menor a mayor)
    top_10 = eficiencia_robusta.sort_values('costo_promedio').head(10)
    
    print("=== TOP 10 UNIVERSIDADES MAS EFICIENTES (Menor costo promedio por graduado) ===")
    print("*(Filtro: Mas de 1,000 graduados historicos en la muestra)*\n")
    print(f"{'INSTITUCION':<50} | {'GRADUADOS':<10} | {'COSTO PROMEDIO (Millones)'}")
    print("-" * 85)
    for _, row in top_10.iterrows():
        print(f"{row['institucion'][:48]:<50} | {int(row['total_graduados']):<10,d} | ${row['costo_promedio']:,.1f}")
        
    print("\n")
    
    # 2. Top 10 Instituciones que mas dinero recibieron vs Graduados (Mayor costo)
    bottom_10 = eficiencia_robusta.sort_values('costo_promedio', ascending=False).head(10)
    print("=== TOP 10 UNIVERSIDADES CON MAYOR INVERSION POR GRADUADO ===")
    print(f"{'INSTITUCION':<50} | {'GRADUADOS':<10} | {'COSTO PROMEDIO (Millones)'}")
    print("-" * 85)
    for _, row in bottom_10.iterrows():
        print(f"{row['institucion'][:48]:<50} | {int(row['total_graduados']):<10,d} | ${row['costo_promedio']:,.1f}")

    # 3. Graficar: Top 10 mas eficientes
    plt.figure(figsize=(12, 6))
    sns.barplot(
        data=top_10, 
        x='costo_promedio', 
        y='institucion', 
        palette='viridis'
    )
    plt.title('Top 10 Universidades más "Eficientes" (Menor Inversión por Graduado)', fontsize=14, pad=15)
    plt.xlabel('Millones de Pesos por Graduado (Promedio)', fontsize=12)
    plt.ylabel('Institución', fontsize=12)
    plt.tight_layout()
    
    # Guardar grafica
    out_img1 = BASE_DIR / 'Imagenes' / 'Top_Eficiencia_Universidades.png'
    out_img1.parent.mkdir(exist_ok=True)
    plt.savefig(out_img1, dpi=300)
    print(f"\nGrafico de barras guardado en: {out_img1}")

    # 4. Evolucion en el tiempo de la inversion vs graduados (Para el sistema cruzado total)
    evolucion = df.groupby('anio_proceso', as_index=False).agg(
        pagos_totales=('pagos_millones', 'sum'),
        graduados_totales=('total_graduados', 'sum')
    )
    evolucion['costo_global'] = evolucion['pagos_totales'] / evolucion['graduados_totales']
    
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=evolucion, x='anio_proceso', y='costo_global', marker='o', color='#e74c3c', linewidth=2.5, markersize=8)
    plt.title('Evolución Histórica: Inversión Promedio por Graduado', fontsize=14, pad=15)
    plt.xlabel('Año de Proceso', fontsize=12)
    plt.ylabel('Millones de Pesos / Graduado', fontsize=12)
    plt.xticks(evolucion['anio_proceso'])
    plt.tight_layout()
    
    out_img2 = BASE_DIR / 'Imagenes' / 'Evolucion_Eficiencia_Global.png'
    plt.savefig(out_img2, dpi=300)
    print(f"Grafico de evolucion guardado en: {out_img2}")

if __name__ == '__main__':
    main()
