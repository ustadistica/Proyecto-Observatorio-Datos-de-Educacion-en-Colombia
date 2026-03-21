import pandas as pd
import numpy as np

# 1. Rutas de archivos
ruta_entrada = r'C:\Users\jhona\Desktop\UNIVERSIDAD SANTO TOMAS\CONSULTORIA PROYECTO\BASES DE DATOS\BASES_CONSOLIDADO_INGESTA.csv'
ruta_salida = r'C:\Users\jhona\Desktop\UNIVERSIDAD SANTO TOMAS\CONSULTORIA PROYECTO\BASES DE DATOS\BASES_LIMPIEZA_GENERAL.csv'

def limpieza_profesional():
    print("--- INICIANDO LIMPIEZA GENERAL DE LA BASE DE DATOS ---")
    
    # Cargar el consolidado de 2.3M de registros
    # Usamos low_memory=False para que no haya advertencias por el tamaño
    df = pd.read_csv(ruta_entrada, sep=';', encoding='latin1', low_memory=False)
    print(f"Registros iniciales: {len(df)}")

    # --- PASO 1: Eliminar Duplicados ---
    # Elimina filas que sean exactamente iguales en todas sus columnas
    df = df.drop_duplicates()
    print(f"Registros tras eliminar duplicados: {len(df)}")

    # --- PASO 2: Limpieza de Texto en todas las columnas tipo objeto ---
    print("Normalizando textos (Mayúsculas y espacios)...")
    columnas_texto = df.select_dtypes(include=['object']).columns
    for col in columnas_texto:
        df[col] = df[col].astype(str).str.upper().str.strip()

    # --- PASO 3: Tratamiento de Valores Nulos ---
    # Para columnas de texto, reemplazamos nulos por 'SIN_DATOS'
    df[columnas_texto] = df[columnas_texto].replace(['NAN', 'NONE', 'NULL', ''], 'SIN_DATOS')
    
    # Para columnas numéricas (puntajes), reemplazamos nulos por 0 o el promedio (aquí usamos 0)
    columnas_num = df.select_dtypes(include=[np.number]).columns
    df[columnas_num] = df[columnas_num].fillna(0)

    # --- PASO 4: Formateo de Columnas Específicas ---
    # Aseguramos que el periodo sea tratado como categoría o entero para ahorrar memoria
    if 'periodo' in df.columns:
        df['periodo'] = df['periodo'].astype(str)

    # --- PASO 5: Exportación Final ---
    print(f"Guardando base de datos limpia en: {ruta_salida}")
    # Guardamos con separador '|' (pipe) que es más seguro para bases de datos grandes
    df.to_csv(ruta_salida, index=False, sep='|', encoding='latin1')
    
    print("-" * 30)
    print("✅ LIMPIEZA GENERAL COMPLETADA")
    print(f"Archivo generado: BASES_LIMPIEZA_GENERAL.csv")
    print("-" * 30)

if __name__ == "__main__":
    limpieza_profesional()