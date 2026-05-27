from sodapy import Socrata
import pandas as pd
import os

# ================= CONFIG =================
DOMAIN = "www.datos.gov.co"

# 📁 Carpeta donde guardarás los parquet (luego los subes a OneDrive)
OUTPUT_DIR = "datos/procesados"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 📅 Rango de años
START_YEAR = 2015
END_YEAR = 2024

# ✅ Dataset oficial SNIES - Matrícula
DATASET_ID = "5wck-szir"

# ================= CLIENT =================
client = Socrata(DOMAIN, None)

# ================= FUNCIONES =================

def descargar_matriculados() -> pd.DataFrame:
    print("🔽 Descargando datos de matrícula...")

    results = client.get(DATASET_ID, limit=2000000)
    df = pd.DataFrame(results)

    print(f"✅ Filas descargadas: {df.shape[0]}")
    return df


def detectar_columna_anio(df: pd.DataFrame) -> str:
    posibles = ["anio", "a_o", "year", "periodo"]

    for col in posibles:
        if col in df.columns:
            print(f"📅 Columna de año detectada: {col}")
            return col

    raise ValueError("❌ No se encontró columna de año")


def filtrar_por_anio(df: pd.DataFrame, col_anio: str) -> pd.DataFrame:
    df[col_anio] = pd.to_numeric(df[col_anio], errors="coerce")

    df_filtrado = df[
        (df[col_anio] >= START_YEAR) &
        (df[col_anio] <= END_YEAR)
    ]

    print(f"📊 Filas después del filtro ({START_YEAR}-{END_YEAR}): {df_filtrado.shape[0]}")
    return df_filtrado


def guardar_parquet(df: pd.DataFrame):
    path = os.path.join(OUTPUT_DIR, "matriculados.parquet")
    df.to_parquet(path, index=False)

    print(f"💾 Archivo guardado en: {path}")


# ================= PIPELINE =================

def run():
    df = descargar_matriculados()

    col_anio = detectar_columna_anio(df)

    df = filtrar_por_anio(df, col_anio)

    guardar_parquet(df)

    print("\n✅ Proceso de ingesta finalizado correctamente")


# ================= MAIN =================

if __name__ == "__main__":
    run()