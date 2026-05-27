import pandas as pd
from pathlib import Path

print("=" * 80)
print("TRANSFORMACION FINAL SNIES - GRADUADOS")
print("=" * 80)

# ==========================================
# RUTAS (AUTOMÁTICAS)
# ==========================================

BASE_DIR = Path(__file__).resolve()

while not (BASE_DIR / "datos").exists():
    BASE_DIR = BASE_DIR.parent

PROCESSED = BASE_DIR / "datos" / "processed" / "snies"

INPUT = PROCESSED / "graduados_limpio_consolidado.parquet"
OUTPUT = PROCESSED / "graduados_final.parquet"

print("BASE_DIR:", BASE_DIR)
print("INPUT:", INPUT)
print("OUTPUT:", OUTPUT)

# ==========================================
# CARGAR
# ==========================================

df = pd.read_parquet(INPUT)

print("Base cargada:", df.shape)

# ==========================================
# ELIMINAR VARIABLES CON MUCHOS NULOS
# ==========================================

columnas_drop = [
    'id cine campo amplio\tdesc',
    'id area de conocimiento',
    'cdigo del municipio (programa)',
    'codigo del municipio',
    'cine campo amplio',
    'id cine campo amplio desc',
    'id cine campo detallado',
    'codigo del municipio ies',
    'desc cine campo detallado',
    'desc cine codigo detallado',
    'id cine codigo detallado',
    'id cine campo amplio',
    'desc cine campo amplio',
    'ies_acreditada',
    'programa_acreditado',
    'codigo_mcpio_ies',
    'id cine campo especifico',
    'desc cine campo especifico',
    'codigo_mcpio_programa',
    'id_area'
]

df = df.drop(
    columns=[c for c in columnas_drop if c in df.columns],
    errors='ignore'
)

# ==========================================
# TIPOS NUMÉRICOS
# ==========================================

# graduados
df["graduados"] = (
    pd.to_numeric(
        df["graduados"],
        errors="coerce"
    )
    .fillna(0)
    .astype("Int64")
)

# semestre
df["semestre"] = (
    pd.to_numeric(
        df["semestre"],
        errors="coerce"
    )
    .astype("Int64")
)

df["semestre"] = df["semestre"].replace({
    1.0: 1,
    2.0: 2
})

# anio
df["anio"] = (
    pd.to_numeric(
        df["anio"],
        errors="coerce"
    )
    .astype("Int64")
)

# ==========================================
# LIMPIEZA TEXTO GENERAL
# ==========================================

def clean_text(s):

    if pd.isna(s):
        return pd.NA

    return (
        str(s)
        .lower()
        .strip()
        .replace("á","a")
        .replace("é","e")
        .replace("í","i")
        .replace("ó","o")
        .replace("ú","u")
    )

# ==========================================
# LIMPIEZAS ESPECÍFICAS
# ==========================================

# AREA
df["area_conocimiento"] = (
    df["area_conocimiento"]
    .apply(clean_text)
    .replace({
        "economia administracion contaduria y afines":
            "economia, administracion, contaduria y afines",

        "ingenieria arquitectura urbanismo y afines":
            "ingenieria, arquitectura, urbanismo y afines"
    })
)

# CARACTER
df["caracter"] = (
    df["caracter"]
    .apply(clean_text)
)

# GENERO
df["genero"] = (
    df["genero"]
    .apply(clean_text)
    .replace({
        "m": "masculino",
        "hombre": "masculino",
        "f": "femenino",
        "mujer": "femenino"
    })
)

# 🔥 ELIMINAR NULOS EN GENERO
df = df[df["genero"].notna()]

# NIVEL
df["nivel"] = (
    df["nivel"]
    .apply(clean_text)
)

# SECTOR
df["sector"] = (
    df["sector"]
    .apply(clean_text)
    .replace({
        "privada": "privado"
    })
)

# 🔥 ELIMINAR NULOS EN SECTOR
df = df[df["sector"].notna()]

# TIPO IES
df["tipo_ies"] = (
    df["tipo_ies"]
    .apply(clean_text)
)

# METODOLOGIA
df["metodologia"] = (
    df["metodologia"]
    .apply(clean_text)
)

# NIVEL FORMACION
df["nivel_formacion"] = (
    df["nivel_formacion"]
    .apply(clean_text)
    .replace({
        "universitaria": "universitario",
        "tecnologica": "tecnologico"
    })
)

# NUCLEO
df["nucleo_conocimiento"] = (
    df["nucleo_conocimiento"]
    .apply(clean_text)
)

# ==========================================
# DEPARTAMENTOS
# ==========================================

def limpiar_departamento(x):

    x = clean_text(x)

    if pd.isna(x):
        return pd.NA

    if "bogota" in x:
        return "bogota"

    if "antioquia" in x:
        return "antioquia"

    if "valle" in x:
        return "valle del cauca"

    if "santander" in x:
        return "santander"

    return x

df["depto_ies"] = (
    df["depto_ies"]
    .apply(limpiar_departamento)
)

df["depto_programa"] = (
    df["depto_programa"]
    .apply(limpiar_departamento)
)

# ==========================================
# MUNICIPIOS
# ==========================================

def limpiar_municipio(x):

    x = clean_text(x)

    if pd.isna(x):
        return pd.NA

    if "bogota" in x:
        return "bogota"

    if "medellin" in x:
        return "medellin"

    return x

df["mcpio_ies"] = (
    df["mcpio_ies"]
    .apply(limpiar_municipio)
)

df["mcpio_programa"] = (
    df["mcpio_programa"]
    .apply(limpiar_municipio)
)

# ==========================================
# PROGRAMA
# ==========================================

df["nombre_programa"] = (
    df["nombre_programa"]
    .apply(clean_text)
)

# ==========================================
# INSTITUCIÓN
# ==========================================

df["nombre_institucion"] = (
    df["nombre_institucion"]
    .apply(clean_text)
)

# ==========================================
# RESULTADO FINAL
# ==========================================

print("\nDespues de limpieza:", df.shape)

# ==========================================
# GUARDAR
# ==========================================

df.to_parquet(
    OUTPUT,
    index=False
)

print("\nArchivo guardado en:")
print(OUTPUT.resolve())