import pandas as pd

# ==========================================
# CARGAR PARQUET
# ==========================================

df = pd.read_parquet(
    "datos/processed/snies/matriculados_final.parquet"
)

print("Parquet cargado correctamente")
print(f"Filas originales: {len(df):,}")

# ==========================================
# LIMPIAR SEMESTRE
# Convierte:
# 1.0 -> 1
# 2.0 -> 2
# ==========================================

df["semestre"] = (
    pd.to_numeric(df["semestre"], errors="coerce")
    .astype("Int64")
)

# ==========================================
# LIMPIAR AÑO
# Convierte:
# 2023.0 -> 2023
# 2024.0 -> 2024
# ==========================================

df["anio"] = (
    pd.to_numeric(df["anio"], errors="coerce")
    .astype("Int64")
)

df["matriculados"] = (
    pd.to_numeric(df["matriculados"], errors="coerce")
    .fillna(0)
    .astype("Int64")
)

# ==========================================
# LIMPIAR VARIABLE SECTOR
# ==========================================

df["sector"] = (
    df["sector"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# Unificar categorías equivalentes
df["sector"] = df["sector"].replace({
    "privada": "privado"
})

# ==========================================
# FILTRO METODOLÓGICO SNIES
# ==========================================

# Identificar SENA
filtro_sena = (
    df["nombre_institucion"]
    .str.contains(
        "SERVICIO NACIONAL DE APRENDIZAJE-SENA-",
        case=False,
        na=False
    )
)

# ==========================================
# REGLA:
#
# - Todas las instituciones:
#       SOLO semestre 1
#
# - SENA:
#       SOLO semestre 2
# ==========================================

# Instituciones normales -> semestre 1
normal = df[
    (~filtro_sena) &
    (df["semestre"] == 1)
]

# SENA -> semestre 2
sena = df[
    (filtro_sena) &
    (df["semestre"] == 2)
]

# ==========================================
# UNIR DATAFRAMES
# ==========================================

df_final = pd.concat(
    [normal, sena],
    ignore_index=True
)

# ==========================================
# INFORMACIÓN FINAL
# ==========================================

print("\n===================================")
print("VALIDACIONES")
print("===================================")

print(f"\nFilas finales: {len(df_final):,}")

print("\nDistribución semestre:")
print(df_final["semestre"].value_counts(dropna=False))

print("\nDistribución año:")
print(df_final["anio"].value_counts(dropna=False).sort_index())

# ==========================================
# EXPORTAR NUEVO PARQUET
# ==========================================

ruta_salida = (
    "datos/processed/snies/Matriculados_total.parquet"
)

df_final.to_parquet(
    ruta_salida,
    index=False
)

print("\n===================================")
print("EXPORTACIÓN COMPLETADA")
print("===================================")

print(f"\nNuevo parquet generado:")
print(ruta_salida)