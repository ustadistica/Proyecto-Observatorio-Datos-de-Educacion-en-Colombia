"""
pte.py — Ingesta Raw del PTE (Presupuesto del Sector Educación)
===============================================================
Fuentes:
  A) 2015-2018: Reportes XLS/XLSX del Ministerio de Educación Nacional
     https://www.mineducacion.gov.co → encoding latin-1 (SIIF Nación)
  B) 2019-2024: API Socrata de MinHacienda
     https://www.datos.gov.co/resource/5phs-yqfw → UTF-8 nativo

Responsabilidad de este script: SOLO descarga y guarda raw.
El encoding se corrige AQUÍ para que los parquets raw ya sean UTF-8 limpio..
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
        
        match_anio = re.search(r"(20[12][0-9])", texto_busqueda)
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
        match_anio = re.search(r"(20[12][0-9])", ruta.name)
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


# ── Fuente B: Excels SIIF/DNP 2019-2024 ──────────────────────────────────────

import unicodedata

def _ascii_norm(s: str) -> str:
    if not isinstance(s, str): return ''
    return unicodedata.normalize('NFKD', s).encode('ASCII','ignore').decode('utf-8').upper().strip()


# Archivos SIIF/DNP en la raíz de raw/pte/ (sin subcarpeta de año)
_SIIF_FILES = {
    2020: "08. Ejecuci\u00f3n Presupuesto General de la Naci\u00f3n detalle por Sector, entidad y rubro 2020.xlsx",
    2021: "08. Ejecuci\u00f3n Presupuesto General de la Naci\u00f3n detalle por Sector, entidad y rubro.xlsx",
    2022: "08. Ejecuci\u00f3n Presupuesto General de la Naci\u00f3n detalle por Sector, entidad y rubro (1).xlsx",
    2023: "3. Reporte de SIIF Ejecuci\u00f3n Agregada (Acumulada a Diciembre de 2023) Vigencia actual, Reservas presupuestales y Cuentas por pagar.xlsx",
    2024: "03. Reporte de SIIF Ejecuci\u00f3n Agregada (Acumulada a Dic de 2024) Vigencia actual, Reservas presupuestales y Cu.xlsx",
}

# Rubros genéricos (no asignados a una sola universidad) que se suman como "MEN-General"
_RUBROS_GENERALES = [
    'A UNIVERSIDADES PARA FUNCIONAMIENTO',
    'DESCUENTO VOTACIONES',
    'APOYO PARA FOMENTAR EL ACCESO',
    'FONDO SOLIDARIO',
    'MATRICULA CERO',
    'SEGURIDAD HUMANA',
    'RECONCEPTUALIZACION',
    'ORGANOS ASESORES',
]


def _es_rubro_general(desc: str) -> bool:
    s = _ascii_norm(str(desc))
    return any(k in s for k in _RUBROS_GENERALES)


def _clean_uni_name(desc: str) -> str:
    """Extrae y normaliza el nombre de universidad de una descripción de rubro."""
    s = _ascii_norm(str(desc))
    # Quitar prefijos numéricos tipo '2202-0700-27--'
    s = re.sub(r'^[\d\-\.]+\s*', '', s)
    # Quitar 'APORTES PARA LA FINANCIACION DE (LA|EL)?'
    s = re.sub(r'APORTES PARA LA FINANCIACI[ON]+\s+DE\s+(LA\s+|EL\s+)?', '', s)
    # Quitar 'UNIVERSIDADES PUBLICAS - '
    s = re.sub(r'UNIVERSIDADES\s+P[UBLICAS]+\s*-\s*', '', s)
    # Quitar sufijos: ' - NACIONAL', ' - SEDE X'
    s = re.sub(r'\s*-\s*(NACIONAL|SEDE\s+\w+)\s*$', '', s)
    # Quitar paréntesis
    s = re.sub(r'\s*\(.*?\)', '', s)
    return s.strip()


def leer_dnp_cuadro7(filepath: Path, year: int) -> Optional[pd.DataFrame]:
    """Lee el DNP Cuadro 7 (2020-2022) y retorna DataFrame normalizado."""
    try:
        df_raw = pd.read_excel(filepath, sheet_name=0, engine='openpyxl', header=None, dtype=str)
        # Detectar fila de header
        header_row = None
        for i, row in df_raw.iterrows():
            vals = row.dropna().astype(str).tolist()
            if any('Entidad' in v or 'ENTIDAD' in v for v in vals):
                header_row = i; break
        if header_row is None:
            logger.warning('  DNP: No se encontró fila header en ' + filepath.name)
            return None

        df = pd.read_excel(filepath, sheet_name=0, engine='openpyxl', header=header_row, dtype=str)
        df = reparar_encoding_df(df)

        # Encontrar columnas clave
        entity_col = next((c for c in df.columns if 'Entidad' in str(c) or 'entidad' in str(c).lower()), None)
        pago_col   = next((c for c in df.columns if str(c).strip() in ['Pago', 'PAGO', 'Pagos', 'PAGOS']), None)
        if not pago_col:
            # Buscar por posición: la columna 'Pago' en Cuadro7 es la 5ª columna numérica
            pago_col = next((c for c in df.columns if re.match(r'^Pago', str(c), re.I) and 'Aprop' not in str(c) and '/' not in str(c)), None)
        aprop_col = next((c for c in df.columns if 'Vigente' in str(c) or 'vigente' in str(c).lower()), None)

        if not entity_col or not pago_col:
            logger.warning('  DNP: Columnas clave no encontradas en ' + filepath.name)
            return None

        # Convertir numéricos
        for col in [pago_col, aprop_col]:
            if col: df[col] = pd.to_numeric(df[col], errors='coerce')

        # Filtrar filas de universidades (individuales, no genéricas)
        mask_univ  = df[entity_col].astype(str).str.contains('UNIVERSIDAD', case=False, na=False)
        mask_no_gen = ~df[entity_col].astype(str).apply(_es_rubro_general)
        df_uni = df[mask_univ & mask_no_gen].copy()

        if df_uni.empty:
            logger.warning('  DNP: Sin universidades individuales en ' + filepath.name)
            return None

        # Normalizar nombre
        df_uni['nombre_uej']   = df_uni[entity_col].apply(_clean_uni_name)
        df_uni['codigo_uej']   = df_uni[entity_col].apply(lambda x: re.match(r'^[\d\-]+', str(x)).group() if re.match(r'^[\d\-]+', str(x)) else '')
        df_uni['descripcion']  = df_uni[entity_col].apply(_ascii_norm)
        df_uni['pagos']        = pd.to_numeric(df_uni[pago_col], errors='coerce')
        df_uni['apropiacionvigente'] = pd.to_numeric(df_uni[aprop_col], errors='coerce') if aprop_col else None
        df_uni['compromisos']  = pd.to_numeric(df_uni.get(next((c for c in df_uni.columns if 'Compromiso' in str(c)), pago_col), 0), errors='coerce')
        df_uni['obligaciones'] = pd.to_numeric(df_uni.get(next((c for c in df_uni.columns if 'Obligaci' in str(c)), pago_col), 0), errors='coerce')
        df_uni['anio_proceso'] = str(year)
        df_uni['mes_reporte']  = '12'
        df_uni['sector']       = 'EDUCACION'
        df_uni['fuente_ingesta'] = 'dnp_cuadro7'

        # Agrupar por universidad (colapsar posibles duplicados)
        num_cols = ['pagos', 'apropiacionvigente', 'compromisos', 'obligaciones']
        grp_cols = ['anio_proceso', 'mes_reporte', 'nombre_uej', 'codigo_uej', 'descripcion', 'sector', 'fuente_ingesta']
        existing_num = [c for c in num_cols if c in df_uni.columns]
        agg = df_uni.groupby(grp_cols, as_index=False, dropna=False)[existing_num].sum()

        logger.info('  [OK] DNP ' + str(year) + ': ' + str(len(agg)) + ' universidades | ' +
                    str(round(agg['pagos'].sum()/1e12, 2)) + ' B COP')
        return agg

    except Exception as e:
        logger.error('  Error DNP ' + filepath.name + ': ' + str(e))
        return None


def leer_siif_uej(filepath: Path, year: int) -> Optional[pd.DataFrame]:
    """Lee el SIIF por UEJ (2023-2024) y retorna DataFrame normalizado."""
    try:
        xl = pd.ExcelFile(filepath, engine='openpyxl')
        sheet = next((s for s in xl.sheet_names if 'VIGENCIA' in s.upper() or s.lower() == 'vigencia'), xl.sheet_names[0])
        df = pd.read_excel(filepath, sheet_name=sheet, engine='openpyxl', header=3, dtype=str)
        df = reparar_encoding_df(df)

        nombre_col = next((c for c in df.columns if 'NOMBRE' in str(c).upper() and 'UEJ' in str(c).upper()), None)
        pagos_col  = next((c for c in df.columns if str(c).strip().upper() in ['PAGOS', 'PAGO']), None)
        aprop_col  = next((c for c in df.columns if 'VIGENTE' in str(c).upper()), None)
        uej_col    = next((c for c in df.columns if str(c).strip().upper() == 'UEJ'), None)

        if not nombre_col or not pagos_col:
            logger.warning('  SIIF: Columnas no encontradas en ' + filepath.name)
            return None

        for col in [pagos_col, aprop_col]:
            if col: df[col] = pd.to_numeric(df[col], errors='coerce')

        mask = df[nombre_col].astype(str).str.contains('UNIVERSIDAD', case=False, na=False)
        df_uni = df[mask].copy()

        df_uni['nombre_uej']   = df_uni[nombre_col].apply(_clean_uni_name)
        df_uni['codigo_uej']   = df_uni[uej_col].astype(str) if uej_col else ''
        df_uni['descripcion']  = df_uni[nombre_col].apply(_ascii_norm)
        df_uni['pagos']        = pd.to_numeric(df_uni[pagos_col], errors='coerce')
        df_uni['apropiacionvigente'] = pd.to_numeric(df_uni[aprop_col], errors='coerce') if aprop_col else None
        df_uni['anio_proceso'] = str(year)
        df_uni['mes_reporte']  = '12'
        df_uni['sector']       = 'EDUCACION'
        df_uni['fuente_ingesta'] = 'siif_uej'

        num_cols = ['pagos', 'apropiacionvigente']
        grp_cols = ['anio_proceso', 'mes_reporte', 'nombre_uej', 'codigo_uej', 'descripcion', 'sector', 'fuente_ingesta']
        existing_num = [c for c in num_cols if c in df_uni.columns]
        agg = df_uni.groupby(grp_cols, as_index=False, dropna=False)[existing_num].sum()

        logger.info('  [OK] SIIF ' + str(year) + ': ' + str(len(agg)) + ' universidades | ' +
                    str(round(agg['pagos'].sum()/1e12, 2)) + ' B COP')
        return agg

    except Exception as e:
        logger.error('  Error SIIF ' + filepath.name + ': ' + str(e))
        return None


def interpolar_2019(df_2018: pd.DataFrame, df_2020: pd.DataFrame) -> pd.DataFrame:
    """Estima 2019 como promedio entre 2018 y 2020, por universidad. Dado que los datos de 2019 solo se encuentran en el DNP donde exigen estado de 
    colaborador para su descarga, se interpola entre 2018 y 2020.
    El parquet 2018 (MEN) guarda el nombre en 'descripcion', no en 'nombre_uej',
    por lo que se extrae via regex antes de cruzar con 2020 (DNP).
    """
    import unicodedata, re as _re

    def _ascii(s):
        if not isinstance(s, str): return ''
        return unicodedata.normalize('NFKD', s).encode('ASCII','ignore').decode('utf-8').upper().strip()

    def _extract_uni(desc):
        s = _ascii(str(desc))
        # Nombres directos tipo 'UNIVERSIDAD NACIONAL DE COLOMBIA'
        if _re.match(r'^UNIVERSIDAD\s+', s) and len(s) < 100:
            name = _re.sub(r'\s*-\s*(NACIONAL|SEDE\s+\w+)$', '', s)
            return name.strip()
        # Patrones tipo 'APORTES PARA LA FINANCIACION DE LA UNIVERSIDAD X'
        m = _re.search(r'(UNIVERSIDAD[\w\s\-\.]+)', s)
        if m:
            name = m.group(1)
            name = _re.sub(r'\s*-\s*(NACIONAL|SEDE\s+\w+)$', '', name)
            name = _re.sub(r'\s+LEY\s+.*$', '', name)
            name = _re.sub(r'\s+ART[\.\s].*$', '', name)
            name = _re.sub(r'\s+PARA\s+.*$', '', name)
            return name.strip()
        return None

    # Extraer universidades del 2018 MEN
    col_desc = 'descripcion' if 'descripcion' in df_2018.columns else None
    if col_desc is None:
        logger.warning('  2019: Sin columna descripcion en parquet 2018'); return pd.DataFrame()

    df_2018 = df_2018[df_2018['anio_proceso'].astype(str) == '2018'].copy()
    df_2018['pagos'] = pd.to_numeric(df_2018.get('pagos', 0), errors='coerce')
    df_2018['_uni'] = df_2018[col_desc].apply(_extract_uni)
    df_2018 = df_2018.dropna(subset=['_uni'])
    df_2018 = df_2018[df_2018['_uni'].str.contains('UNIVERSIDAD', na=False)]

    if df_2018.empty:
        logger.warning('  2019: Sin universidades extraídas del parquet 2018'); return pd.DataFrame()

    m18 = df_2018.groupby('_uni')['pagos'].sum().reset_index()
    m18.columns = ['nombre_uej', 'p18']

    m20 = df_2020.groupby('nombre_uej')['pagos'].sum().reset_index()
    m20.columns = ['nombre_uej', 'p20']

    # Cruce fuzzy simplificado: limpiar nombres antes de cruzar
    def _key(s):
        s = _ascii(str(s))
        for tok in ['UNIVERSIDAD','DE ','DEL ','LA ','EL ','-','  ']:
            s = s.replace(tok, ' ')
        return ' '.join(s.split())[:40]

    m18['_key'] = m18['nombre_uej'].apply(_key)
    m20['_key'] = m20['nombre_uej'].apply(_key)

    merged = m18.merge(m20, on='_key', how='inner', suffixes=('_18','_20'))
    merged['pagos']             = (merged['p18'] + merged['p20']) / 2
    merged['apropiacionvigente'] = merged['pagos']
    merged['nombre_uej']        = merged['nombre_uej_18']
    merged['anio_proceso']      = '2019'
    merged['mes_reporte']       = '12'
    merged['sector']            = 'EDUCACION'
    merged['fuente_ingesta']    = 'interpolado_2018_2020'
    merged['codigo_uej']        = ''
    merged['descripcion']       = merged['nombre_uej']

    result = merged[['anio_proceso','mes_reporte','nombre_uej','codigo_uej',
                     'descripcion','sector','fuente_ingesta','pagos','apropiacionvigente']]
    return result



def ingestar_excels_siif(years: List[int]):
    """
    Lee los Excels DNP/SIIF para 2020-2024 y guarda un parquet por año.
    También interpola 2019 combinando datos de 2018 (MEN) y 2020 (DNP).
    """
    RAW_PTE.mkdir(parents=True, exist_ok=True)
    frames_dnp = {}

    for year in sorted(years):
        if year not in _SIIF_FILES:
            continue
        fp = RAW_PTE / _SIIF_FILES[year]
        if not fp.exists():
            logger.warning('  [MISS] No encontrado: ' + fp.name); continue

        logger.info('\n📂 Procesando año ' + str(year) + '...')
        if year in [2020, 2021, 2022]:
            df = leer_dnp_cuadro7(fp, year)
        else:
            df = leer_siif_uej(fp, year)

        if df is None or df.empty:
            continue

        frames_dnp[year] = df
        year_path = RAW_PTE / str(year)
        year_path.mkdir(parents=True, exist_ok=True)
        out = year_path / ('pte_manual_' + str(year) + '.parquet')
        df.to_parquet(out, index=False)
        logger.info('  💾 Guardado: ' + out.name)

    # Interpolar 2019 si tenemos 2018 y 2020
    if 2019 in years and 2020 in frames_dnp:
        pte_2018_path = RAW_PTE / '2018' / 'pte_manual_2018.parquet'
        if pte_2018_path.exists():
            logger.info('\n📂 Interpolando 2019 (promedio 2018+2020)...')
            df_2018 = pd.read_parquet(pte_2018_path)
            df_2019 = interpolar_2019(df_2018, frames_dnp[2020])
            year_path = RAW_PTE / '2019'
            year_path.mkdir(parents=True, exist_ok=True)
            out_2019 = year_path / 'pte_manual_2019.parquet'
            df_2019.to_parquet(out_2019, index=False)
            logger.info('  [OK] 2019 interpolado: ' + str(len(df_2019)) + ' universidades | ' +
                        str(round(df_2019['pagos'].sum()/1e12, 2)) + ' B COP')
            logger.info('  💾 Guardado: ' + out_2019.name)
        else:
            logger.warning('  Sin parquet 2018 para interpolar 2019')


# ── Punto de entrada ─────────────────────────────────────────────────────────

def ejecutar_ingesta_total(
    years: List[int] = None,
    forzar: bool = False
):
    """
    Ejecuta la ingesta completa:
    - Años 2015-2018: convierte XLS del MEN a Parquet
    - Años 2019-2024: lee Excels DNP/SIIF + interpola 2019
    """
    if years is None:
        years = list(range(2015, 2025))

    logger.info("=" * 65)
    logger.info("INICIANDO INGESTA PTE — Presupuesto del Sector Educación")
    logger.info("Años objetivo: " + str(years))
    logger.info("=" * 65)

    anios_men  = [y for y in years if y < 2019]
    anios_siif = [y for y in years if y >= 2019]

    if anios_men:
        logger.info("\n── Fuente A: Excels MEN " + str(anios_men) + " ──")
        ingestar_excels_men(anios_men)

    if anios_siif:
        logger.info("\n── Fuente B: Excels SIIF/DNP " + str(anios_siif) + " ──")
        ingestar_excels_siif(anios_siif)

    logger.info("\n" + "=" * 65)
    logger.info("INGESTA PTE COMPLETADA")
    logger.info("Parquets guardados en: " + str(RAW_PTE))
    logger.info("=" * 65)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingesta del dataset PTE")
    parser.add_argument("--years", nargs="+", type=int, default=list(range(2015, 2025)))
    parser.add_argument("--forzar", action="store_true", help="Sobreescribir existentes")
    args = parser.parse_args()
    ejecutar_ingesta_total(years=args.years, forzar=args.forzar)

