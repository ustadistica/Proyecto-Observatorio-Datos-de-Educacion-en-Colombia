import pandas as pd
import time
import gc
from pathlib import Path

print("=" * 80)
print("LIMPIEZA GRADUADOS SNIES - VERSION FINAL SIN PERDIDA")
print("=" * 80)

# ==========================================
# RUTAS (IGUAL A MATRICULADOS)
# ==========================================
BASE_DIR = Path(__file__).parent.parent.parent
RAW_GRADUADOS = BASE_DIR / "datos" / "raw" / "snies" / "graduados"
PROCESSED_SNIES = BASE_DIR / "datos" / "processed" / "snies"

PROCESSED_SNIES.mkdir(parents=True, exist_ok=True)

# ==========================================
# NORMALIZADOR
# ==========================================
def norm(col):
    return (
        str(col)
        .lower()
        .strip()
        .replace('\n', ' ')
        .replace('\r', ' ')
        .replace('  ', ' ')
        .replace('_', ' ')
        .replace('*', '')
        .replace('á', 'a')
        .replace('é', 'e')
        .replace('í', 'i')
        .replace('ó', 'o')
        .replace('ú', 'u')
    )

# ==========================================
# MAPEO (ADAPTADO)
# ==========================================
MAPEO = {
    'codigo de la institucion': 'codigo_institucion',
    'ies padre': 'ies_padre',
    'institucion de educacion superior (ies)': 'nombre_institucion',
    'principal o seccional': 'tipo_ies',
    'tipo ies': 'tipo_ies',

    'id sector ies': 'id_sector',
    'sector ies': 'sector',

    'id caracter': 'id_caracter',
    'id caracter ies': 'id_caracter',
    'caracter ies': 'caracter',

    'codigo del departamento (ies)': 'codigo_depto_ies',
    'departamento de domicilio de la ies': 'depto_ies',
    'codigo del municipio (ies)': 'codigo_mcpio_ies',
    'municipio de domicilio de la ies': 'mcpio_ies',

    'codigo snies del programa': 'codigo_snies_programa',
    'programa academico': 'nombre_programa',

    'id nivel academico': 'id_nivel',
    'nivel academico': 'nivel',

    'id nivel de formacion': 'id_nivel_formacion',
    'nivel de formacion': 'nivel_formacion',

    'id metodologia': 'id_metodologia',
    'id modalidad': 'id_metodologia',
    'metodologia': 'metodologia',
    'modalidad': 'metodologia',

    'id area': 'id_area',
    'area de conocimiento': 'area_conocimiento',

    'id nucleo': 'id_nucleo',
    'nucleo basico del conocimiento (nbc)': 'nucleo_conocimiento',

    'codigo del departamento (programa)': 'codigo_depto_programa',
    'departamento de oferta del programa': 'depto_programa',
    'codigo del municipio (programa)': 'codigo_mcpio_programa',
    'municipio de oferta del programa': 'mcpio_programa',

    'id sexo': 'id_genero',
    'sexo': 'genero',

    'ano': 'anio',
    'año': 'anio',
    'año*': 'anio',
    'semestre': 'semestre',

    'graduados': 'graduados',

    'ies acreditada': 'ies_acreditada',
    'programa acreditado': 'programa_acreditado'
}

# ==========================================
# LIMPIEZA
# ==========================================
def limpiar_df(df):

    df.columns = [norm(c) for c in df.columns]
    df = df.rename(columns=lambda x: MAPEO.get(x, x))

    # 🔥 MISMA LOGICA QUE MATRICULADOS
    df = df.T.groupby(level=0).apply(lambda x: x.bfill().iloc[0]).T

    return df

# ==========================================
# PROCESAR ARCHIVO
# ==========================================
def procesar_archivo(archivo, anio):
    try:
        df = pd.read_parquet(archivo)
        print(f"Procesando: {archivo.name} {df.shape}")

        df = limpiar_df(df)

        if 'anio' not in df.columns:
            df['anio'] = anio

        return df

    except Exception as e:
        print("ERROR:", e)
        return None

# ==========================================
# PROCESAMIENTO POR AÑO
# ==========================================
for anio in range(2015, 2025):

    print(f"\nProcesando año {anio}")

    carpeta = RAW_GRADUADOS / str(anio)
    archivos = list(carpeta.glob("*.parquet"))

    dfs = []

    for archivo in archivos:
        df = procesar_archivo(archivo, anio)
        if df is not None:
            dfs.append(df)

        del df
        gc.collect()

    if dfs:
        df_anio = pd.concat(dfs, ignore_index=True)

        ruta = PROCESSED_SNIES / f"graduados_{anio}_limpio.parquet"
        df_anio.to_parquet(ruta, index=False)

        print(f"Guardado {anio}: {df_anio.shape}")

        del df_anio
        gc.collect()

# ==========================================
# CONSOLIDADO FINAL
# ==========================================
print("\nConcatenando todo...")

archivos = list(PROCESSED_SNIES.glob("graduados_*_limpio.parquet"))

if not archivos:
    print("⚠️ No se encontraron archivos procesados. Revisa la ruta RAW.")
else:
    dfs = [pd.read_parquet(f) for f in archivos]

    df_final = pd.concat(dfs, ignore_index=True)
    df_final = df_final.drop_duplicates()

    ruta_final = PROCESSED_SNIES / "graduados_limpio_consolidado.parquet"
    df_final.to_parquet(ruta_final, index=False)

    print("\nFINAL")
    print(df_final.shape)
    print("Columnas:", len(df_final.columns))
    print("Total graduados:", df_final["graduados"].sum())
