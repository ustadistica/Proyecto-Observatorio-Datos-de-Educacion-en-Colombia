"""
limpieza_snies.py — Limpieza y normalización Cross-Bright de datos SNIES
=========================================================================
Lee los archivos RAW de graduados y matriculados (datos/raw/snies/),
aplica el diccionario Cross-Bright de header_utils_snies.py para
unificar nombres de columnas, castea las métricas a int, y exporta
archivos limpios consolidados a datos/processed/snies/.
"""

import unicodedata
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

from src.ingesta.header_utils_snies import (
    normalise_header_snies,
    get_unmapped_columns,
    _slugify,
)

RAW_SNIES       = BASE_DIR / "datos" / "raw" / "snies"
PROCESSED_SNIES = BASE_DIR / "datos" / "processed" / "snies"

# Columnas de texto categórico donde se corrige mojibake y se deduplicanvariantes
_COLS_CATEGORICAS = [
    'area_conocimiento', 'nivel_academico', 'nivel_formacion', 'metodologia',
    'nombre_programa', 'nombre_institucion', 'sector_ies', 'caracter_ies',
    'departamento_ies', 'municipio_ies', 'departamento_programa', 'municipio_programa',
]


def _fix_mojibake(s: str) -> str:
    """
    Corrige texto con mojibake latin-1/utf-8 y normaliza acentos a ASCII.
    Ejemplo: 'ECONOM\xcdA' → 'ECONOMIA'
    """
    if not isinstance(s, str):
        return s
    # Intento 1: es latin-1 reinterpretado como utf-8
    try:
        s = s.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    # Quitar acentos para unificar variantes con/sin tilde
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')


# Columnas canónicas que DEBEN existir en el resultado final
CORE_COLUMNS = {
    'graduados':    ['anio_proceso', 'semestre', 'codigo_institucion', 'nombre_institucion',
                     'codigo_snies_programa', 'nombre_programa', 'graduados'],
    'matriculados': ['anio_proceso', 'semestre', 'codigo_institucion', 'nombre_institucion',
                     'codigo_snies_programa', 'nombre_programa', 'matriculados'],
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza las columnas usando el diccionario Cross-Bright de SNIES.
    Pasos:
      1. Limpia newlines, espacios extra del nombre de columna.
      2. Aplica el slug -> canonical del diccionario.
      3. Elimina columnas duplicadas (conserva la primera).
    """
    # Paso 1: Limpiar nombres de columna (newlines, espacios multiples)
    clean_names = {}
    for col in df.columns:
        cleaned = str(col).replace('\n', ' ').replace('\r', ' ')
        # Eliminar sufijos como "Matriculados 2015" → "Matriculados"
        import re
        cleaned = re.sub(r'\s+\d{4}$', '', cleaned).strip()
        clean_names[col] = cleaned
    df = df.rename(columns=clean_names)

    # Paso 2: Aplicar Cross-Bright normalisation
    new_cols = {}
    for col in df.columns:
        canonical = normalise_header_snies(col)
        new_cols[col] = canonical
    df = df.rename(columns=new_cols)

    # Paso 3: Eliminar columnas duplicadas (conservar primera ocurrencia)
    df = df.loc[:, ~df.columns.duplicated()]

    return df


def _cast_metrics(df: pd.DataFrame, categoria: str) -> pd.DataFrame:
    """Castea las columnas de métricas y claves a tipos numéricos."""
    # Métrica principal (graduados o matriculados)
    if categoria in df.columns:
        df[categoria] = pd.to_numeric(df[categoria], errors='coerce').fillna(0).astype(int)
    else:
        logger.warning(f"   Columna '{categoria}' no encontrada tras normalización.")

    # Semestre
    if 'semestre' in df.columns:
        df['semestre'] = pd.to_numeric(df['semestre'], errors='coerce').fillna(1).astype(int)

    # Año
    if 'anio_proceso' in df.columns:
        df['anio_proceso'] = pd.to_numeric(df['anio_proceso'], errors='coerce').fillna(0).astype(int)

    # Códigos numéricos
    for col in ['codigo_institucion', 'codigo_snies_programa', 'codigo_depto_ies',
                'codigo_mcpio_ies', 'codigo_depto_programa', 'codigo_mcpio_programa',
                'id_sector', 'id_caracter', 'id_genero', 'id_nucleo',
                'id_area_conocimiento', 'id_nivel_formacion', 'id_metodologia']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def procesar_categoria(categoria: str):
    """Procesa graduados o matriculados desde los RAW individuales."""
    categoria_path = RAW_SNIES / categoria
    if not categoria_path.exists():
        logger.error(f"No existe la ruta {categoria_path}")
        return

    archivos = []
    for year_dir in sorted(categoria_path.iterdir()):
        if year_dir.is_dir():
            for f in year_dir.glob("*.parquet"):
                archivos.append(f)

    logger.info(f"Archivos {categoria} encontrados: {len(archivos)}")
    frames = []

    for archivo in archivos:
        anio = archivo.parent.name
        logger.info(f"   Cargando {archivo.name} (anio={anio})...")
        try:
            df = pd.read_parquet(archivo)

            # 1. Normalizar columnas con Cross-Bright
            df = _normalise_columns(df)

            # 2. Inyectar año si no existe
            if 'anio_proceso' not in df.columns:
                df['anio_proceso'] = anio

            # 3. Auditoría: columnas no mapeadas
            unmapped = get_unmapped_columns(df)
            if unmapped:
                logger.info(f"      Columnas preservadas (no mapeadas): {unmapped}")

            frames.append(df)
            logger.info(f"      OK: {len(df):,} registros")
        except Exception as e:
            logger.error(f"      ERROR en {archivo.name}: {e}")

    if not frames:
        logger.error(f"No se cargó ningún archivo de {categoria}.")
        return

    # Concatenar
    logger.info(f"Concatenando {len(frames)} archivos de {categoria}...")
    df_all = pd.concat(frames, ignore_index=True)
    logger.info(f"Total registros crudos: {len(df_all):,}")

    # Casteo de métricas
    logger.info("Casteando metricas a tipos numericos...")
    df_all = _cast_metrics(df_all, categoria)

    # Normalizar textos en columnas string
    logger.info("Normalizando textos (fix mojibake + UPPER + STRIP)...")
    text_cols = df_all.select_dtypes(include=['object']).columns

    # Paso 1: corregir mojibake y eliminar acentos en columnas categóricas clave
    cols_moji = [c for c in _COLS_CATEGORICAS if c in df_all.columns]
    for col in cols_moji:
        df_all[col] = df_all[col].map(
            lambda x: _fix_mojibake(x) if isinstance(x, str) else x
        )
    if cols_moji:
        logger.info(f"   Mojibake corregido en: {cols_moji}")

    # Paso 2: UPPER + STRIP en todas las columnas texto
    for col in text_cols:
        df_all[col] = df_all[col].astype(str).str.upper().str.strip()

    # Paso 3a: Convertir a NULL los valores centinela del SNIES que no aportan información
    # ('SIN INFORMACIÓN' → NULL, 'SIN CLASIFICAR' → NULL, etc.)
    _SIN_INFO_VALS = [
        'NAN', 'NONE', 'NULL', '',
        'SIN INFORMACION', 'SIN INFORMACIÓN', 'SIN CLASIFICAR',
        'SIN INFO', 'SIN DATO', 'NO REPORTA', 'NO APLICA',
    ]
    df_all[text_cols] = df_all[text_cols].replace(_SIN_INFO_VALS, np.nan)

    # Paso 3b: Normalizar sector_ies: 'PRIVADA' → 'PRIVADO' (variante de género)
    if 'sector_ies' in df_all.columns:
        df_all['sector_ies'] = df_all['sector_ies'].replace({'PRIVADA': 'PRIVADO'})

    # Paso 3c: Normalizar area_conocimiento — eliminar comas y espacios múltiples
    #          para unificar variantes como "ECONOMIA, ADMINISTRACION..." vs "ECONOMIA ADMINISTRACION..."
    if 'area_conocimiento' in df_all.columns:
        def _norm_area(s):
            if not isinstance(s, str):
                return s
            # Eliminar comas, puntos y normalizar espacios
            s = s.replace(',', ' ').replace('.', ' ')
            s = ' '.join(s.split())  # colapsar espacios múltiples
            return s
        df_all['area_conocimiento'] = df_all['area_conocimiento'].map(_norm_area)
        logger.info(f"   area_conocimiento normalizada → {df_all['area_conocimiento'].nunique()} valores únicos")

    # Paso 3d: Normalizar nivel_formacion — unificar variantes de género y truncados
    #          'UNIVERSITARIA' = 'UNIVERSITARIO', 'TECNOLOGICA' = 'TECNOLOGICO', etc.
    #          También corrige valores truncados por límite de caracteres en fuentes SNIES.
    #          Se elige la forma masculina como canónica (más frecuente en SNIES reciente).
    if 'nivel_formacion' in df_all.columns:
        import re
        # Primero: correcciones de valores truncados (antes del replace por regex)
        _NF_TRUNCATED = {
            'ESPECIALIZACION TECNICO PROFESION': 'ESPECIALIZACION TECNICO PROFESIONAL',
            'ESPECIALIZACION TECNICO PROFESI':   'ESPECIALIZACION TECNICO PROFESIONAL',
        }
        df_all['nivel_formacion'] = df_all['nivel_formacion'].replace(_NF_TRUNCATED)

        # Luego: unificación de variantes de género (femenino → masculino canónico)
        _NF_GENDER_MAP = {
            r'\bUNIVERSITARIA\b':      'UNIVERSITARIO',
            r'\bTECNOLOGICA\b':        'TECNOLOGICO',
            r'\bTECNICA\b':            'TECNICO',
            r'\bPROFESIONAL\b':        'PROFESIONAL',  # ya es neutro
        }
        for pat, repl in _NF_GENDER_MAP.items():
            df_all['nivel_formacion'] = df_all['nivel_formacion'].str.replace(
                pat, repl, regex=True, case=False
            )
        logger.info(f"   nivel_formacion normalizada → {df_all['nivel_formacion'].nunique()} valores únicos")
        logger.info(f"   Valores: {sorted(df_all['nivel_formacion'].dropna().unique().tolist())}")

    # Paso 3: deduplicar registros exactos (misma combinación tras normalización)
    antes_dedup = len(df_all)
    df_all = df_all.drop_duplicates()
    dupes_elim = antes_dedup - len(df_all)
    if dupes_elim > 0:
        logger.info(f"   Duplicados exactos eliminados tras normalización: {dupes_elim:,}")

    # Filtrar rango de años válido
    df_all = df_all[df_all['anio_proceso'].between(2014, 2025)]

    # Verificar columnas core
    logger.info("Verificando columnas core...")
    for col in CORE_COLUMNS[categoria]:
        if col not in df_all.columns:
            logger.warning(f"   FALTA columna core: {col}")

    # Resumen por año
    logger.info(f"\n--- RESUMEN {categoria.upper()} POR AÑO ---")
    resumen = df_all.groupby('anio_proceso')[categoria].sum()
    for anio, total in resumen.items():
        logger.info(f"   {anio}: {total:>12,}")

    # Exportar
    PROCESSED_SNIES.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_SNIES / f"snies_{categoria}_limpio_consolidado.parquet"
    df_all.to_parquet(out_path, index=False)
    logger.info(f"\nExportado: {out_path}")
    logger.info(f"   Filas: {len(df_all):,}  |  Columnas: {len(df_all.columns)}")
    logger.info(f"   Columnas: {sorted(df_all.columns.tolist())}")


def limpieza_snies():
    """Punto de entrada principal."""
    logger.info("=" * 70)
    logger.info("  LIMPIEZA SNIES — Cross-Bright Pipeline")
    logger.info("=" * 70)
    PROCESSED_SNIES.mkdir(parents=True, exist_ok=True)

    for cat in ['graduados', 'matriculados']:
        logger.info(f"\n{'='*70}")
        logger.info(f"  PROCESANDO: {cat.upper()}")
        logger.info(f"{'='*70}")
        procesar_categoria(cat)


# Alias para compatibilidad con el pipeline anterior
limpieza_snies_ultra_corregida = limpieza_snies


if __name__ == "__main__":
    limpieza_snies()