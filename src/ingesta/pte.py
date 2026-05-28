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
        
        match_anio = re.search(r"(201[5-9]|202[0-5])", texto_busqueda)
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
        match_anio = re.search(r"(201[5-9]|202[0-5])", ruta.name)
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
    Detecta y salta filas de metadatos; lee headers reales de la fila de datos.
    Aplica normalización cross-bright a los nombres de columna.
    """
    try:
        is_xlsx = ruta.suffix.lower() == ".xlsx"
        engine = "openpyxl" if is_xlsx else "xlrd"

        logger.info(f"  Leyendo {ruta.name} con engine='{engine}'...")
        # Leer sin header para detectar fila de columnas
        df_raw = pd.read_excel(ruta, engine=engine, header=None, dtype=str)

        # Reparar mojibake en todos los strings
        df_raw = reparar_encoding_df(df_raw)

        # Buscar fila que contiene los headers reales
        header_row = None
        for i, row in df_raw.iterrows():
            vals = [str(v).strip().upper() if pd.notna(v) else '' for v in row]
            if 'UEJ' in vals or 'NOMBRE UEJ' in vals or 'RUBRO' in vals:
                header_row = i
                break

        if header_row is None:
            logger.warning(f"  No se detectó fila de headers en {ruta.name}, usando fila 0")
            header_row = 0

        # Re-leer con header correcto
        df = pd.read_excel(ruta, engine=engine, header=header_row, dtype=str)
        df = reparar_encoding_df(df)

        # Cross-bright: normalizar headers por nombre (no por posición)
        import sys
        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))
        from src.ingesta.header_utils import normalise_header
        df.columns = [normalise_header(str(col)) for col in df.columns]

        # Eliminar filas vacías o de totales
        df = df.dropna(subset=['codigo_uej', 'rubro'], how='all')
        df = df[~df['codigo_uej'].astype(str).str.upper().isin(['TOTAL', 'NAN', ''])]

        # Estandarizar: crear columnas modernas desde columnas SIIF antiguas
        _estandarizar_siif_antiguo(df)

        # Extraer periodo
        anio, mes = extraer_periodo_xls(ruta)
        df["anio_proceso"] = anio
        df["mes_reporte"] = mes

        logger.info(f"  ✅ {ruta.name}: {len(df):,} filas, año={anio}, mes={mes}")
        return df, anio, mes

    except Exception as e:
        logger.error(f"  ❌ Error en {ruta.name}: {e}")
        return None, None, None


def _estandarizar_siif_antiguo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte las columnas de cuenta SIIF antiguas (cta, sub_cta, obj, ord, item, sub_item)
    al formato moderno (codigo_cuarto_nivel, codigo_quinto_nivel, nombre_*).
    Elimina las columnas antiguas del DataFrame.
    """
    # Crear codigo_cuarto_nivel y codigo_quinto_nivel desde la jerarquia de cuenta
    def _concat_cols(row, cols):
        vals = [str(row.get(c, '')).strip() for c in cols if pd.notna(row.get(c, ''))]
        return '.'.join(vals) if vals else None

    cuarto_cols = ['cta', 'sub_cta', 'obj', 'ord']
    quinto_cols = ['cta', 'sub_cta', 'obj', 'ord', 'item', 'sub_item']

    if all(c in df.columns for c in cuarto_cols):
        df['codigo_cuarto_nivel'] = df.apply(lambda r: _concat_cols(r, cuarto_cols), axis=1)
    if all(c in df.columns for c in quinto_cols):
        df['codigo_quinto_nivel'] = df.apply(lambda r: _concat_cols(r, quinto_cols), axis=1)

    # Rellenar nombres desde descripcion
    if 'descripcion' in df.columns:
        for col in ['nombre_rubro', 'nombre_tipo_gasto', 'nombre_detalle_gasto',
                    'nombre_cuarto_nivel', 'nombre_quinto_nivel']:
            if col not in df.columns:
                df[col] = df['descripcion']

    # Eliminar columnas SIIF antiguas
    old_cols = ['cta', 'sub_cta', 'obj', 'ord', 'sor_ord', 'item', 'sub_item', 'sub_item_2']
    for c in old_cols:
        if c in df.columns:
            df.drop(columns=[c], inplace=True)

    return df


def ingestar_excels_men(years: List[int]):
    """
    Convierte los XLS/XLSX del MEN a Parquet UTF-8 limpio en raw/pte/<año>/.
    Solo procesa años 2015-2018 (fuente manual).
    Agrega los 12 meses de cada año en 1 solo parquet anual (suma de valores).
    """
    RAW_PTE.mkdir(parents=True, exist_ok=True)

    # Los excels están en la raíz de raw/pte/ mezclados
    excels = list(RAW_PTE.glob("*.xls")) + list(RAW_PTE.glob("*.xlsx"))
    logger.info(f"Excels encontrados en raw/pte/: {len(excels)}")

    # Agrupar por año
    from collections import defaultdict
    year_dfs = defaultdict(list)

    for excel in excels:
        anio_ruta, mes_ruta = extraer_periodo_xls(excel)
        if anio_ruta is None or int(anio_ruta) not in years:
            continue

        df, anio_df, mes_df = leer_excel_men(excel)
        if df is None:
            continue

        year_dfs[int(anio_df)].append(df)
        logger.info(f"  📅 Añadido año={anio_df}, mes={mes_df}: {len(df):,} filas")

    # Agregar cada año (sumar meses)
    for year, frames in sorted(year_dfs.items()):
        logger.info(f"\n🧮 AGREGANDO AÑO {year} ({len(frames)} meses)...")

        # Concatenar todos los meses
        full_year = pd.concat(frames, ignore_index=True, sort=False)

        # Columnas numéricas a sumar
        numeric_cols = ['apropiacioninicial', 'adiciones', 'reducciones',
                        'apropiacionvigente', 'apropiacionbloqueada', 'cdp',
                        'apropiaciondisponible', 'compromisos', 'obligaciones',
                        'orden_pago', 'pagos']
        # Solo las que existen
        numeric_cols = [c for c in numeric_cols if c in full_year.columns]

        # Columnas categóricas para agrupar (todas excepto numéricas y mes_reporte)
        group_cols = [c for c in full_year.columns
                      if c not in numeric_cols and c not in ['mes_reporte']]

        # Convertir numéricas
        for c in numeric_cols:
            full_year[c] = pd.to_numeric(full_year[c], errors='coerce').fillna(0)

        # Agrupar y sumar
        agg = full_year.groupby(group_cols, as_index=False, dropna=False)[numeric_cols].sum()

        # Asegurar anio_proceso
        agg['anio_proceso'] = str(year)
        agg['mes_reporte'] = '12'  # representativo anual

        year_path = RAW_PTE / str(year)
        year_path.mkdir(parents=True, exist_ok=True)
        out_path = year_path / f"pte_manual_{year}.parquet"
        agg.to_parquet(out_path, index=False)
        logger.info(f"  💾 Guardado agregado: {out_path.name} ({len(agg):,} filas)")


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
    logger.info(f"Años objetivo: {years} (MODO 100% EXCEL MEN)")
    logger.info("=" * 65)

    # El usuario solicitó consumir EXCLUSIVAMENTE archivos Excel para todos los años
    logger.info(f"\n── Fuente Única: Excels MEN {years} ──")
    ingestar_excels_men(years)

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