import pandas as pd
import os

# 1. Configuración de la carpeta
ruta_base = r'C:\Users\jhona\Desktop\UNIVERSIDAD SANTO TOMAS\CONSULTORIA PROYECTO\BASES DE DATOS'
lista_dataframes = []

print("--- INICIANDO PROCESO DE CARGA ---")

# 2. Bucle para cargar cada año
for anio in range(2015, 2025):
    nombre_archivo = f"Examen_Saber_Pro_Genericas_{anio}.txt"
    ruta_completa = os.path.join(ruta_base, nombre_archivo)
    
    if os.path.exists(ruta_completa):
        print(f"Cargando año {anio}...")
        try:
            # Quitamos low_memory para que no de error
            df_temp = pd.read_csv(ruta_completa, sep=None, engine='python', encoding='latin1')
            df_temp['anio_proceso'] = anio
            lista_dataframes.append(df_temp)
            print(f"   ✅ ¡Listo! {len(df_temp)} registros cargados.")
        except Exception as e:
            print(f"   ❌ Error en {anio}: {e}")
    else:
        print(f"   ⚠️ No se encontró el archivo del año {anio}")

# 3. Unir todo y GUARDAR
if lista_dataframes:
    print("\nConcatenando todos los datos... esto puede tardar un poco por el volumen.")
    df_final = pd.concat(lista_dataframes, ignore_index=True)
    
    ruta_salida = r'C:\Users\jhona\Desktop\UNIVERSIDAD SANTO TOMAS\CONSULTORIA PROYECTO\BASES DE DATOS\BASES_CONSOLIDADO_INGESTA.csv'
    
    print("Guardando el archivo final en tu computadora...")
    df_final.to_csv(ruta_salida, index=False, sep=';', encoding='latin1')
    
    print("-" * 30)
    print(f"¡ÉXITO TOTAL! Se procesaron {len(df_final)} registros.")
    print(f"El archivo consolidado está en: {ruta_salida}")
    print("-" * 30)
else:
    print("\nNo se cargó nada. Verifica los nombres de los archivos.")