import pandas as pd

ruta_csv = r'C:\Users\jhona\Desktop\UNIVERSIDAD SANTO TOMAS\CONSULTORIA PROYECTO\BASES DE DATOS\BASES_LIMPIEZA_GENERAL.csv'
ruta_parquet = r'C:\Users\jhona\Desktop\UNIVERSIDAD SANTO TOMAS\CONSULTORIA PROYECTO\BASES DE DATOS\BASES_FINALES_OPTIMIZADAS.parquet'

def optimizar_almacenamiento():
    print("--- OPTIMIZANDO ARCHIVO PARA CONSULTORÍA ---")
    # Importante: leer con el separador '|' que generó la limpieza
    df = pd.read_csv(ruta_csv, sep='|', encoding='latin1', low_memory=False)
    
    print(f"Comprimiendo {len(df)} registros y 151 columnas...")
    
    # Guardar usando pyarrow
    try:
        df.to_parquet(ruta_parquet, engine='pyarrow', index=False)
        print(f"✅ ¡Éxito! Archivo optimizado en: {ruta_parquet}")
        
        # Comparación de tamaño (opcional)
        size_csv = os.path.getsize(ruta_csv) / (1024 * 1024)
        size_pq = os.path.getsize(ruta_parquet) / (1024 * 1024)
        print(f"Reducción: de {size_csv:.2f} MB a {size_pq:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error al optimizar: {e}")

if __name__ == "__main__":
    import os
    optimizar_almacenamiento()