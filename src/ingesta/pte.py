"""
pte.py — Ingesta Raw del PTE (Presupuesto del Sector Educación)
===============================================================
Fuentes:
  A) 2015-2018: Reportes XLS/XLSX del Ministerio de Educación Nacional
     https://www.mineducacion.gov.co → encoding latin-1 (SIIF Nación)
  B) 2019-2024: API Socrata de MinHacienda
     https://www.datos.gov.co/resource/5phs-yqfw → UTF-8 nativo

Responsabilidad de este script: SOLO descarga y guarda raw.
El encoding se corrige AQUÍ para que los parquets raw ya sean UTF-8 limpio.
La limpieza estructural la hace limpieza_pte.py.
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, List

import pandas as pd

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Rutas ────────────────────────────────────────────────────────────────────
if Path("/content/drive/MyDrive").exists():
    BASE_DIR = Path("/content/drive/MyDrive/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia")
else:
    BASE_DIR = Path(__file__).parent.parent.parent

RAW_PTE = BASE_DIR / "datos" / "raw" / "pte"
SOCRATA_DOMAIN = "www.datos.gov.co"
DATASET_HACIENDA = "5phs-yqfw"


# ── Utilidades de encoding ───────────────────────────────────────────────────

def reparar_encoding_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Corrige mojibake latin-1→UTF-8 en TODAS las columnas de texto del DataFrame.

    El SIIF Nación exporta los XLS con encoding Windows-1252/latin-1. Al leerlos
    con pandas sin especificar encoding, los caracteres especiales (tildes, ñ)
    quedan corruptos: 'EDUCACIÓN' → 'EDUCACI⿄N'.

    Esta función los repara en el momento de la ingesta, antes de guardar a Parquet.
    """
    def _fix(val):
        if not isinstance(val, str):
            return val
        try:
            return val.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            return val

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(_fix)
    return df


MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", "mayo": "05", "junio": "06",
    "julio": "07", "agosto": "08", "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
}

def extraer_periodo_xls(ruta: Path) -> tuple[str, str]:
    """Extrae año y mes (YYYY, MM) desde el contenido, con fallback al nombre."""
    anio, mes = None, None
    try:
        is_xlsx = ruta.suffix.lower() == ".xlsx"
        engine = "openpyxl" if is_xlsx else "xlrd"
        df_check = pd.read_excel(ruta, engine=engine, header=None, nrows=10, dtype=str)
        
        texto_busqueda = " ".join(df_check.fillna("").values.flatten()).lower()
        import unicodedata
        texto_busqueda = unicodedata.normalize("NFKD", texto_busqueda).encode("ASCII", "ignore").decode("utf-8")
        
        match_anio = re.search(r"(201[5678])", texto_busqueda)
        if match_anio:
            anio = match_anio.group(1)
            
        # Priorizar expresiones como "de diciembre de" o "a diciembre de"
        for n_m, num_m in MESES.items():
            if re.search(r"(?:de|a)\s+" + n_m + r"\b", texto_busqueda):
                mes = num_m
                break
                
        # Si falló la búsqueda prioritaria, buscar el nombre aislado
        if not mes:
            for n_m, num_m in MESES.items():
                if re.search(r"\b" + n_m + r"\b", texto_busqueda):
                    mes = num_m
                    break
    except Exception:
        pass

    if not anio:
        match_anio = re.search(r"(201[5678])", ruta.name)
        if match_anio:
            anio = match_anio.group(1)
            
    if not mes:
        for n_m, num_m in MESES.items():
            if n_m in ruta.name.lower():
                mes = num_m
                break

    return anio, mes


# ── Fuente A: Excel MEN 2015-2018 ─────────────────────────────────────────────

def leer_excel_men(ruta: Path) -> Optional[pd.DataFrame]:
    """
    Lee un XLS/XLSX del MEN con encoding correcto (latin-1 → UTF-8).

    Parámetros críticos:
    - engine='xlrd' para .xls (Office 97-2003)
    - engine='openpyxl' para .xlsx
    - NO usar 'encoding' en read_excel; el fix se hace post-lectura sobre strings.
    """
    try:
        is_xlsx = ruta.suffix.lower() == ".xlsx"
        engine = "openpyxl" if is_xlsx else "xlrd"

        logger.info(f"  Leyendo {ruta.name} con engine='{engine}'...")
        df = pd.read_excel(ruta, engine=engine, header=None, dtype=str)

        # Reparar mojibake en todos los strings
        df = reparar_encoding_df(df)

        # Extraer periodo (para trazabilidad y nombre)
        anio, mes = extraer_periodo_xls(ruta)
        df["anio_reporte"] = anio
        df["mes_reporte"] = mes

        logger.info(f"  ✅ {ruta.name}: {len(df):,} filas, año={anio}, mes={mes}")
        return df, anio, mes

    except Exception as e:
        logger.error(f"  ❌ Error en {ruta.name}: {e}")
        return None, None, None


def ingestar_excels_men(years: List[int]):
    """
    Convierte los XLS/XLSX del MEN a Parquet UTF-8 limpio en raw/pte/<año>/.
    Solo procesa años 2015-2018 (fuente manual).
    """
    RAW_PTE.mkdir(parents=True, exist_ok=True)

    # Los excels están en la raíz de raw/pte/ mezclados
    excels = list(RAW_PTE.glob("*.xls")) + list(RAW_PTE.glob("*.xlsx"))
    logger.info(f"Excels encontrados en raw/pte/: {len(excels)}")

    for excel in excels:
        anio_ruta, mes_ruta = extraer_periodo_xls(excel)
        if anio_ruta is None or int(anio_ruta) not in years:
            continue

        df, anio_df, mes_df = leer_excel_men(excel)
        if df is None:
            continue

        year_path = RAW_PTE / str(anio_df)
        year_path.mkdir(parents=True, exist_ok=True)

        # Nombre estandarizado (ej: pte_manual_2015_01.parquet)
        if mes_df:
            out_path = year_path / f"pte_manual_{anio_df}_{mes_df}.parquet"
        else:
            nombre_limpio = re.sub(r"[^a-z0-9_]", "_", excel.stem.lower()).strip("_")
            nombre_limpio = re.sub(r"_+", "_", nombre_limpio)
            out_path = year_path / f"pte_manual_{anio_df}_{nombre_limpio}.parquet"

        df.to_parquet(out_path, index=False)
        logger.info(f"  💾 Guardado: {out_path.name}")


# ── Fuente B: API Socrata 2019-2024 ──────────────────────────────────────────

def fetch_pte_api(year: int, token: str = None) -> pd.DataFrame:
    """
    Descarga datos de la API Socrata de MinHacienda para el año indicado.
    Filtra solo registros del sector EDUCACION.

    La API retorna JSON con encoding UTF-8 nativo, pero los textos del SIIF
    a veces tienen residuos latin-1. Se aplica el mismo fix de encoding.

    Requiere: pip install sodapy
    """
    try:
        from sodapy import Socrata
    except ImportError:
        logger.error("sodapy no está instalado. Ejecuta: pip install sodapy")
        return pd.DataFrame()

    client = Socrata(SOCRATA_DOMAIN, token or os.getenv("SOCRATA_APP_TOKEN"), timeout=120)
    where = f"anio = '{year}' AND upper(sector) like '%EDUCACION%'"
    logger.info(f"📡 Descargando API Socrata {year}... (filtro: sector EDUCACION)")

    results = []
    offset = 0
    limit = 50_000
    while True:
        chunk = client.get(DATASET_HACIENDA, where=where, limit=limit, offset=offset)
        if not chunk:
            break
        results.extend(chunk)
        offset += limit
        logger.info(f"  → {len(results):,} registros acumulados...")

    client.close()
    logger.info(f"  ✅ Total descargado: {len(results):,} registros")

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame.from_records(results)

    # API es UTF-8 pero por si acaso aplicamos fix
    df = reparar_encoding_df(df)
    return df


def ingestar_api_socrata(years: List[int], token: str = None, forzar: bool = False):
    """
    Descarga y guarda como Parquet los datos de la API para los años indicados.
    Solo procesa años 2019-2024 (fuente API).
    """
    RAW_PTE.mkdir(parents=True, exist_ok=True)

    for year in years:
        if year < 2019:
            continue

        year_path = RAW_PTE / str(year)
        year_path.mkdir(parents=True, exist_ok=True)

        out_path = year_path / f"pte_api_{year}.parquet"
        if out_path.exists() and not forzar:
            logger.info(f"  [{year}] Ya existe. Omitiendo (usa --forzar para regenerar).")
            continue

        logger.info(f"\n🚀 PROCESANDO AÑO API: {year}")
        df = fetch_pte_api(year, token=token)

        if df.empty:
            logger.warning(f"  ⚠️ Sin datos para {year}")
            continue

        df.to_parquet(out_path, index=False)
        logger.info(f"  💾 Guardado: {out_path.name} ({len(df):,} filas)")


# ── Punto de entrada ─────────────────────────────────────────────────────────

def ejecutar_ingesta_total(
    years: List[int] = None,
    token: str = None,
    forzar: bool = False
):
    """
    Ejecuta la ingesta completa:
    - Años 2015-2018: convierte XLS del MEN a Parquet
    - Años 2019-2024: descarga de la API Socrata

    Args:
        years:  Lista de años a procesar. Default: 2015-2024.
        token:  App Token de Socrata (opcional, aumenta límite de peticiones).
        forzar: Si True, sobreescribe parquets existentes.
    """
    if years is None:
        years = list(range(2015, 2025))

    logger.info("=" * 65)
    logger.info("INICIANDO INGESTA PTE — Presupuesto del Sector Educación")
    logger.info(f"Años objetivo: {years}")
    logger.info("=" * 65)

    anios_manual = [y for y in years if y < 2019]
    anios_api    = [y for y in years if y >= 2019]

    if anios_manual:
        logger.info(f"\n── Fuente A: Excels MEN {anios_manual} ──")
        ingestar_excels_men(anios_manual)

    if anios_api:
        logger.info(f"\n── Fuente B: API Socrata {anios_api} ──")
        ingestar_api_socrata(anios_api, token=token, forzar=forzar)

    logger.info("\n" + "=" * 65)
    logger.info("INGESTA PTE COMPLETADA")
    logger.info(f"Parquets guardados en: {RAW_PTE}")
    logger.info("Siguiente paso: python src/ingesta/limpieza_pte.py")
    logger.info("=" * 65)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingesta del dataset PTE")
    parser.add_argument("--years", nargs="+", type=int, default=list(range(2015, 2025)))
    parser.add_argument("--token", type=str, default=None, help="App Token Socrata")
    parser.add_argument("--forzar", action="store_true", help="Sobreescribir existentes")
    args = parser.parse_args()
    ejecutar_ingesta_total(years=args.years, token=args.token, forzar=args.forzar)