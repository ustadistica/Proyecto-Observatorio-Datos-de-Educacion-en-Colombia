import pandas as pd
import numpy as np
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent.parent.parent
RAW_SNIES = BASE_DIR / "datos" / "raw" / "snies"
PROCESSED_SNIES = BASE_DIR / "datos" / "processed" / "snies"

def limpieza_snies_ultra_corregida():
    """
    Limpieza ULTRA corregida de datos SNIES
    Maneja nombres de columnas problemáticos y duplicados
    """
    print("--- INICIANDO LIMPIEZA ULTRA CORREGIDA DE DATOS SNIES ---")
    
    # Crear directorio de salida
    PROCESSED_SNIES.mkdir(parents=True, exist_ok=True)
    
    # Procesar cada categoría por separado
    categorias = ['graduados', 'matriculados']
    
    for categoria in categorias:
        print(f"\n--- PROCESANDO {categoria.upper()} ---")
        procesar_categoria_ultra_corregida(categoria)

def procesar_categoria_ultra_corregida(categoria):
    """
    Procesa una categoría específica de SNIES con manejo robusto de columnas
    """
    # Listar archivos de la categoría
    categoria_path = RAW_SNIES / categoria
    if not categoria_path.exists():
        print(f"   No existe la categoría {categoria}")
        return
    
    archivos_categoria = []
    for year_dir in categoria_path.iterdir():
        if year_dir.is_dir():
            for archivo in year_dir.glob("*.parquet"):
                archivos_categoria.append(archivo)
    
    print(f"   Archivos {categoria} encontrados: {len(archivos_categoria)}")
    
    lista_dataframes = []
    
    # Cargar y procesar cada archivo de la categoría
    for archivo in archivos_categoria:
        print(f"   Cargando {archivo.name}...")
        try:
            # Leer el archivo parquet
            df_temp = pd.read_parquet(archivo)
            
            # Para matriculados, saltar las primeras 2 filas que son metadata
            if categoria == 'matriculados' and len(df_temp) > 2:
                # Usar la fila 2 como header y eliminar filas 0-1
                nuevos_headers = df_temp.iloc[2].tolist()
                df_temp = df_temp[3:].reset_index(drop=True)
                df_temp.columns = nuevos_headers
            
            # Extraer el año del directorio
            anio = archivo.parent.name
            df_temp['anio_proceso'] = anio
            
            # Procesar el dataframe con manejo robusto de columnas
            df_temp = procesar_dataframe_ultra_corregido(df_temp, categoria)
            
            lista_dataframes.append(df_temp)
            print(f"      OK {len(df_temp)} registros cargados.")
        except Exception as e:
            print(f"      ERROR en {archivo.name}: {e}")
    
    # Unir todos los dataframes de la categoría
    if lista_dataframes:
        print(f"\n   Concatenando {len(lista_dataframes)} archivos de {categoria}...")
        df_consolidado = pd.concat(lista_dataframes, ignore_index=True)
        print(f"   Registros consolidados de {categoria}: {len(df_consolidado)}")
        
        # --- PASO 1: Limpieza de Texto ---
        print("   Normalizando textos...")
        columnas_texto = df_consolidado.select_dtypes(include=['object']).columns
        for col in columnas_texto:
            df_consolidado[col] = df_consolidado[col].astype(str).str.upper().str.strip()

        # --- PASO 2: Tratamiento de Valores Nulos ---
        # Reemplazar valores nulos con NaN (no con 'SIN_DATOS') para manejo correcto en tablas de hechos
        df_consolidado[columnas_texto] = df_consolidado[columnas_texto].replace(['NAN', 'NONE', 'NULL', ''], np.nan)
        columnas_num = df_consolidado.select_dtypes(include=[np.number]).columns
        df_consolidado[columnas_num] = df_consolidado[columnas_num].fillna(0)

        # --- PASO 3: Normalización EXTREMA de nombres de columnas ---
        print("   Normalizando nombres de columnas...")
        df_consolidado = normalizar_nombres_columnas_extrema(df_consolidado)
        
        # --- PASO 4: Mapeo de columnas normalizadas a nombres estandar ---
        print("   Mapeando columnas normalizadas a nombres estandar...")
        
        # Los nombres exactos despues de normalizar (incluyendo caracteres raros)
        mapeo_columnas_normalizadas = {
            # Columnas de institucion
            'instituci_n_de_educaci_n_superior_ies': 'inst_nombre_institucion',
            'institucion_de_educacion_superior_ies': 'inst_nombre_institucion',
            'ies': 'inst_nombre_institucion',
            # Columnas de programa
            'programa_acad_mico': 'estu_prgm_academico',
            'programa_academico': 'estu_prgm_academico',
            # Columnas de codigo
            'c_digo_de_la_instituci_n': 'inst_codigo_institucion',
            'codigo_de_la_institucion': 'inst_codigo_institucion',
            'c_digo_snies_del_programa': 'prgm_codigo_snies',
            'codigo_snies_del_programa': 'prgm_codigo_snies',
            # Anio
            'anio_proceso': 'anio_proceso'
        }
        
        # Renombrar columnas segun el mapeo
        for col_original, col_nueva in mapeo_columnas_normalizadas.items():
            if col_original in df_consolidado.columns:
                df_consolidado = df_consolidado.rename(columns={col_original: col_nueva})
                print(f"      Renombrada columna: {col_original} -> {col_nueva}")
        
        # --- PASO 5: Validación y creación de columnas clave ---
        print("   Validando columnas clave...")
        columnas_clave = ['inst_nombre_institucion', 'estu_prgm_academico', 'anio_proceso']
        
        # Crear columnas clave si no existen
        for col in columnas_clave:
            if col not in df_consolidado.columns:
                print(f"      Advertencia: Columna clave '{col}' no encontrada, creando con valor por defecto")
                df_consolidado[col] = 'SIN_DATOS'

        # --- PASO 5: Cuadratura de datasets ---
        print("   Realizando cuadratura...")
        df_consolidado = cuadrar_datasets_ultra_corregido(df_consolidado)
        
        # --- PASO 6: Exportación Final ---
        ruta_salida = PROCESSED_SNIES / f"snies_{categoria}_limpio_consolidado.parquet"
        print(f"   Guardando {categoria} en: {ruta_salida}")
        df_consolidado.to_parquet(ruta_salida, index=False)
        
        print(f"   COMPLETADO: {categoria.upper()}")
        print(f"      Archivo generado: {ruta_salida}")
        print(f"      Registros procesados: {len(df_consolidado)}")
        print(f"      Columnas: {len(df_consolidado.columns)}")
    else:
        print(f"\n   No se cargó ningún archivo de {categoria}. Verifica los archivos en la carpeta raw/snies/{categoria}/")

def procesar_dataframe_ultra_corregido(df, categoria):
    """
    Procesa un dataframe de una categoría específica con manejo robusto de columnas
    """
    # Manejar columnas duplicadas
    df = manejar_columnas_duplicadas_ultra_corregido(df, categoria)
    
    # Normalizar nombres de columnas
    df = normalizar_nombres_columnas_extrema(df)
    
    return df

def manejar_columnas_duplicadas_ultra_corregido(df, categoria):
    """
    Maneja columnas duplicadas renombrándolas de forma única para una categoría
    """
    # Identificar columnas duplicadas
    columnas_duplicadas = df.columns.duplicated()
    if columnas_duplicadas.any():
        print(f"      Columnas duplicadas detectadas: {sum(columnas_duplicadas)}")
        
        # Renombrar columnas duplicadas
        nuevos_nombres = []
        contador_duplicados = {}
        
        for col in df.columns:
            if col in contador_duplicados:
                contador_duplicados[col] += 1
                nuevo_nombre = f"{col}_{contador_duplicados[col]}_{categoria}"
            else:
                contador_duplicados[col] = 0
                nuevo_nombre = f"{col}_{categoria}"
            nuevos_nombres.append(nuevo_nombre)
        
        df.columns = nuevos_nombres
        print(f"      Columnas renombradas exitosamente")
    
    return df

def normalizar_nombres_columnas_extrema(df):
    """
    Normaliza nombres de columnas de forma extrema para evitar cualquier problema
    """
    nuevos_nombres = []
    
    for col in df.columns:
        # Convertir a string y eliminar caracteres problemáticos
        col_str = str(col)
        
        # Reemplazar caracteres especiales y símbolos
        col_limpio = re.sub(r'[^a-zA-Z0-9_]', '_', col_str)
        
        # Eliminar múltiples guiones bajos consecutivos
        col_limpio = re.sub(r'_+', '_', col_limpio)
        
        # Eliminar guiones bajos al inicio y final
        col_limpio = col_limpio.strip('_')
        
        # Convertir a minúsculas
        col_limpio = col_limpio.lower()
        
        # Si el nombre está vacío o solo tiene guiones, usar un nombre genérico
        if not col_limpio or col_limpio == '_':
            col_limpio = f'columna_{len(nuevos_nombres)}'
        
        nuevos_nombres.append(col_limpio)
    
    df.columns = nuevos_nombres
    return df

def cuadrar_datasets_ultra_corregido(df):
    """
    Realiza cuadratura de datasets para asegurar consistencia
    """
    print("      Cuadrando datasets...")
    
    # 1. Asegurar consistencia en valores de columnas clave
    if 'inst_nombre_institucion' in df.columns:
        # Normalizar nombres de instituciones
        df['inst_nombre_institucion'] = df['inst_nombre_institucion'].str.replace(r'\s+', ' ', regex=True)
    
    if 'estu_prgm_academico' in df.columns:
        # Normalizar nombres de programas
        df['estu_prgm_academico'] = df['estu_prgm_academico'].str.replace(r'\s+', ' ', regex=True)
    
    # 2. Validar rangos de años
    if 'anio_proceso' in df.columns:
        try:
            df['anio_proceso'] = pd.to_numeric(df['anio_proceso'], errors='coerce')
            df = df[df['anio_proceso'].between(2015, 2025)]
            print(f"      Años validados: {df['anio_proceso'].min()} - {df['anio_proceso'].max()}")
        except:
            print("      No se pudo validar el rango de años")
    
    print(f"      Cuadratura completada: {len(df)} registros finales")
    return df

if __name__ == "__main__":
    limpieza_snies_ultra_corregida()