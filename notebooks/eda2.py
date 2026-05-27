import pandas as pd

# ==========================================
# CARGAR PARQUET
# ==========================================

df = pd.read_parquet(
    "datos/processed/snies/Matriculados_total.parquet"
)

# ==========================================
# VARIABLES A ANALIZAR
# ==========================================

variables = [
    "genero",
    "depto_programa",
    "caracter",
    "mcpio_programa",
    "mcpio_ies",
    "metodologia",
    "nivel",
    "nivel_formacion",
    "nombre_institucion",
    "sector",
    "nucleo_conocimiento",
    "anio",
    "area_conocimiento",
    "nombre_programa",
    "semestre"
]

# ==========================================
# ANÁLISIS DE matriculados
# ==========================================

for var in variables:

    print("\n" + "="*60)
    print(f"matriculados POR: {var.upper()}")
    print("="*60)

    resumen = (
        df.groupby(var)["matriculados"]
        .sum()
        .sort_values(ascending=False)
    )

    print(resumen.head(20))