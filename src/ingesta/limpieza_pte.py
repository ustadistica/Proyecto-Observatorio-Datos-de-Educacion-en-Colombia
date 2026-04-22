"""
limpieza_pte.py — Limpieza y Consolidación del Dataset PTE
===========================================================
RESPONSABILIDAD: Solo limpia y consolida los parquets raw.
NO crea dimensiones ni tabla de hechos — eso lo hace generar_dimensiones_hechos_pte.py.

Entrada:  datos/raw/pte/<año>/*.parquet
Salida:   datos/processed/pte/pte_limpio_consolidado.parquet

PROBLEMA RESUELTO:
  Las dos fuentes tienen estructuras completamente distintas:

  Fuente A — Excels MEN (2015-2018):
    - Headers en fila 3 (filas 0-2 son cabecera institucional)
    - Columnas: 'NOMBRE UEJ', 'APR. INICIAL', 'DESCRIPCION', etc. (mayúsculas)
    - Encoding: latin-1 (ya corregido en pte.py antes de guardar raw)

  Fuente B — API Socrata (2019-2024):
    - Headers directos en la primera fila (JSON de la API)
    - Columnas: 'nombreentidad', 'nombrenivelrubrogasto', 'apropiacioninicial', etc.
    - Jerarquía de rubro expandida en múltiples columnas

ESQUEMA CANÓNICO DE SALIDA (siempre el mismo, ambas fuentes):
  nombreentidad, rubro, descripcion, fuente, recurso,
  apropiacioninicial, apropiacionvigente, compromisos, obligaciones, pagos,
  anio_proceso, tipo_fuente, uej_codigo,
  tipo_gasto, nivel_rubro, detalle_gasto, cuarto_nivel, quinto_nivel
"""

import pandas as pd
import numpy as np
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
RAW_PTE       = BASE_DIR / "datos" / "raw"       / "pte"
PROCESSED_PTE = BASE_DIR / "datos" / "processed" / "pte"

# ── Esquema canónico fijo ─────────────────────────────────────────────────────
COLUMNAS_CANONICAS = [
    "nombreentidad",
    "uej_codigo",
    "rubro",
    "descripcion",
    "fuente",
    "recurso",
    "apropiacioninicial",
    "apropiacionvigente",
    "compromisos",
    "obligaciones",
    "pagos",
    "anio_proceso",
    "tipo_fuente",
    # Jerarquía de rubro (solo disponible en API post-2019)
    "tipo_gasto",
    "nivel_rubro",
    "detalle_gasto",
    "cuarto_nivel",
    "quinto_nivel",
]

COLUMNAS_NUMERICAS = [
    "apropiacioninicial", "apropiacionvigente",
    "compromisos", "obligaciones", "pagos",
]


# ── Utilidades ────────────────────────────────────────────────────────────────

def limpiar_col(serie: pd.Series) -> pd.Series:
    """Normalización vectorizada de texto: upper + strip + nulls."""
    s = serie.astype(str).str.upper().str.strip()
    return s.replace({"NAN": np.nan, "NONE": np.nan, "NULL": np.nan,
                      "": np.nan, "SIN_DATOS": np.nan, "<NA>": np.nan})


def a_float(serie: pd.Series) -> pd.Series:
    """Convierte serie de strings a float limpio (acepta coma decimal)."""
    s = serie.astype(str).str.replace(",", ".", regex=False).str.strip()
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def normalizar_nombres_col(df: pd.DataFrame) -> pd.DataFrame:
    """Lleva todos los nombres de columna a snake_case minúsculas."""
    nuevos = {}
    for col in df.columns:
        nc = (str(col).lower().strip()
              .replace(" ", "_").replace(".", "_")
              .replace("-", "_").replace("/", "_"))
        nc = re.sub(r"_+", "_", nc).strip("_")
        if nc != col:
            nuevos[col] = nc
    return df.rename(columns=nuevos)


# ── Mapeo Fuente A: Excels MEN (2015-2018) ────────────────────────────────────
MAPA_EXCEL_MEN = {
    "NOMBRE UEJ": "nombreentidad", "NOMBREUEJ": "nombreentidad",
    "NOMBRE_UEJ": "nombreentidad", "UEJ": "uej_codigo",
    "RUBRO": "rubro",
    "DESCRIPCION": "descripcion", "DESCRIPCIÓN": "descripcion",
    "FUENTE": "fuente",
    "REC": "recurso",    "RECURSO": "recurso",
    "SITUACION": "situacion", "SIT": "situacion",
    "APR. INICIAL": "apropiacioninicial", "APR.INICIAL": "apropiacioninicial",
    "APROPIACION INICIAL": "apropiacioninicial",
    "APROPIACIONINICIAL": "apropiacioninicial",
    "APR. VIGENTE": "apropiacionvigente", "APR.VIGENTE": "apropiacionvigente",
    "APROPIACION VIGENTE": "apropiacionvigente",
    "APROPIACIONVIGENTE": "apropiacionvigente",
    "COMPROMISOS": "compromisos", "COMPROMISO": "compromisos",
    "OBLIGACIONES": "obligaciones", "OBLIGACION": "obligaciones",
    "PAGOS": "pagos",
}


def procesar_excel_men(df_raw: pd.DataFrame, anio: int) -> pd.DataFrame | None:
    """
    Transforma un Parquet raw del Excel MEN al esquema canónico.

    Los archivos MEN tienen la estructura:
    - Filas 0-2: cabecera institucional (título, entidad, fecha)
    - Fila 3:    headers reales de columnas
    - Fila 4+:   datos presupuestales
    """
    logger.info(f"  [MEN {anio}] Buscando headers reales...")

    if len(df_raw) < 5:
        logger.warning(f"  [MEN {anio}] Archivo demasiado corto, omitiendo.")
        return None

    idx_header = None
    for i in range(min(15, len(df_raw))):
        vals = [str(x).upper().strip() for x in df_raw.iloc[i].values]
        if "UEJ" in vals or "NOMBRE UEJ" in vals or "RUBRO" in vals:
            idx_header = i
            break

    if idx_header is None:
        logger.warning(f"  [MEN {anio}] No se encontraron headers en las primeras filas. OMITIENDO.")
        return None

    headers = df_raw.iloc[idx_header].values
    df = pd.DataFrame(df_raw.iloc[idx_header+1:].values, columns=headers).reset_index(drop=True)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    # Renombrar al esquema canónico
    rename_map = {col: MAPA_EXCEL_MEN[str(col).upper().strip()]
                  for col in df.columns
                  if str(col).upper().strip() in MAPA_EXCEL_MEN}
    df = df.rename(columns=rename_map)

    # Inferir nombreentidad si no se encontró
    if "nombreentidad" not in df.columns:
        for col in df.columns:
            sample = df[col].dropna().head(10).astype(str).str.upper()
            if sample.str.contains(r"MINISTERIO|EDUCACION|ICFES|SENA|UNIVERSIDAD", regex=True).any():
                df = df.rename(columns={col: "nombreentidad"})
                logger.info(f"    ↳ 'nombreentidad' inferida desde '{col}'")
                break

    if "nombreentidad" not in df.columns:
        logger.warning(f"  [MEN {anio}] Sin columna entidad. OMITIENDO.")
        return None

    # Eliminar filas vacías / totales / notas
    df = df.dropna(subset=["nombreentidad"])
    df = df[~df["nombreentidad"].astype(str).str.upper()
            .str.startswith(("FUENTE:", "TOTAL", "SUBTOTAL", "NOTA:"), na=False)]
    df = df[df["nombreentidad"].astype(str).str.strip() != ""]

    # Limpiar texto
    for col in ["nombreentidad", "descripcion", "fuente", "recurso", "rubro", "uej_codigo"]:
        if col in df.columns:
            df[col] = limpiar_col(df[col])

    # Montos
    for col in COLUMNAS_NUMERICAS:
        df[col] = a_float(df[col]) if col in df.columns else 0.0

    # Columnas de jerarquía (no disponibles en MEN)
    for col in ["tipo_gasto", "nivel_rubro", "detalle_gasto", "cuarto_nivel", "quinto_nivel"]:
        df[col] = np.nan

    df["anio_proceso"] = int(anio)
    df["tipo_fuente"] = "MANUAL_MEN"

    logger.info(f"  [MEN {anio}] {len(df):,} registros procesados.")
    return df


# ── Mapeo Fuente B: API Socrata (2019-2024) ───────────────────────────────────
MAPA_API_SOCRATA = {
    "nombreentidad": "nombreentidad",
    "codigoentidad": "uej_codigo",
    # 'fuente' ya existe → no renombrar (evita duplicado)
    "recursospresupuestales": "fuente",   # solo si 'fuente' no existe aún
    "situacion": "situacion",
    "apropiacioninicial": "apropiacioninicial",
    "apropiacionvigente": "apropiacionvigente",
    "compromisos": "compromisos",
    "obligaciones": "obligaciones",
    "pagos": "pagos",
    # Jerarquía nominal
    "nombretipogasto":       "tipo_gasto",
    "nombrenivelrubrogasto": "nivel_rubro",
    "nombredetallegasto":    "detalle_gasto",
    "nombrecuartonivel":     "cuarto_nivel",
    "nombrequintonivel":     "quinto_nivel",
    # Jerarquía códigos (para construir rubro)
    "codigotipogasto":       "cod_tipo_gasto",
    "codigonivelrubrogasto": "cod_nivel_rubro",
    "codigodetallegasto":    "cod_detalle_gasto",
    "codigocuartonivel":     "cod_cuarto_nivel",
    "codigoquintonivel":     "cod_quinto_nivel",
    # Metadatos
    "anio":             "anio_api",
    "nombremes":        "mes",
    "sector":           "sector",
    "detalleprogramas": "detalle_programas",
    "adiciones":        "adiciones_cop",
    "reducciones":      "reducciones_cop",
    "vigencia":         "vigencia_tipo",
}


def procesar_api_socrata(df_raw: pd.DataFrame, anio: int) -> pd.DataFrame | None:
    """
    Transforma un Parquet raw de la API Socrata al esquema canónico.
    Construye 'rubro' y 'descripcion' concatenando los niveles jerárquicos.
    """
    logger.info(f"  [API {anio}] Normalizando esquema...")

    df = df_raw.copy().reset_index(drop=True)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]  # eliminar cols duplicadas
    df = normalizar_nombres_col(df)

    # Renombrar con control de destinos únicos (evita duplicar 'fuente')
    rename_map = {}
    destinos = set(df.columns)  # ya usados
    for col in df.columns:
        if col in MAPA_API_SOCRATA:
            destino = MAPA_API_SOCRATA[col]
            # No renombrar si el destino ya existe como col original y no es la misma col
            if destino in destinos and destino != col:
                continue
            rename_map[col] = destino
            destinos.add(destino)

    df = df.rename(columns=rename_map)
    df.columns = list(df.columns)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    # Garantizar 'fuente' (puede venir como recursospresupuestales ya renombrado)
    if "fuente" not in df.columns:
        df["fuente"] = np.nan

    # Construir 'rubro' desde códigos jerárquicos
    cols_cod = [c for c in ["cod_tipo_gasto", "cod_nivel_rubro", "cod_detalle_gasto",
                             "cod_cuarto_nivel", "cod_quinto_nivel"] if c in df.columns]
    if cols_cod:
        partes = df[cols_cod].fillna("").astype(str)
        df["rubro"] = partes.apply(
            lambda r: "-".join(v for v in r if v and v not in ("nan", "None", "")),
            axis=1
        ).replace("", np.nan)
    elif "rubro" not in df.columns:
        df["rubro"] = np.nan

    # Construir 'descripcion' desde nombres jerárquicos
    cols_nom = [c for c in ["tipo_gasto", "nivel_rubro", "detalle_gasto",
                             "cuarto_nivel", "quinto_nivel"] if c in df.columns]
    if cols_nom:
        partes = df[cols_nom].fillna("").astype(str)
        df["descripcion"] = partes.apply(
            lambda r: " > ".join(v for v in r if v and v not in ("nan", "None", "")),
            axis=1
        ).replace("", np.nan)
    elif "descripcion" not in df.columns:
        df["descripcion"] = np.nan

    # Limpiar texto (vectorizado)
    for col in ["nombreentidad", "descripcion", "fuente", "rubro", "uej_codigo",
                "tipo_gasto", "nivel_rubro", "detalle_gasto", "cuarto_nivel", "quinto_nivel"]:
        if col in df.columns:
            df[col] = limpiar_col(df[col])

    # Montos
    for col in COLUMNAS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ".", regex=False),
                                    errors="coerce").fillna(0.0)
        else:
            df[col] = 0.0

    # Jerarquía vacía si no se construyó
    for col in ["tipo_gasto", "nivel_rubro", "detalle_gasto", "cuarto_nivel", "quinto_nivel"]:
        if col not in df.columns:
            df[col] = np.nan
    if "recurso" not in df.columns:
        df["recurso"] = np.nan
    if "uej_codigo" not in df.columns:
        df["uej_codigo"] = np.nan

    df["anio_proceso"] = int(anio)
    df["tipo_fuente"] = "API_SOCRATA"

    # Descartar filas sin valor presupuestario
    df = df[df[COLUMNAS_NUMERICAS].sum(axis=1) > 0].reset_index(drop=True)

    logger.info(f"  [API {anio}] {len(df):,} registros procesados.")
    return df


# ── Función principal ─────────────────────────────────────────────────────────

def limpieza_pte_profesional() -> pd.DataFrame | None:
    """
    Lee todos los Parquets raw de datos/raw/pte/<año>/,
    los normaliza al esquema canónico y guarda el consolidado limpio.

    Salida: datos/processed/pte/pte_limpio_consolidado.parquet
    Siguiente paso: python src/transformacion/generar_dimensiones_hechos_pte.py
    """
    logger.info("=" * 65)
    logger.info("LIMPIEZA PTE — Consolidación al Esquema Canónico")
    logger.info("=" * 65)

    PROCESSED_PTE.mkdir(parents=True, exist_ok=True)

    lista_dfs: list[pd.DataFrame] = []

    anios_dirs = sorted([d for d in RAW_PTE.iterdir() if d.is_dir() and d.name.isdigit()])
    logger.info(f"Años encontrados: {[d.name for d in anios_dirs]}")

    for year_dir in anios_dirs:
        anio = int(year_dir.name)
        archivos = list(year_dir.glob("*.parquet"))

        if not archivos:
            logger.warning(f"  [{anio}] Sin parquets. Saltando.")
            continue

        logger.info(f"\n── Procesando año {anio} ({len(archivos)} archivo(s)) ──")

        for archivo in archivos:
            try:
                df_raw = pd.read_parquet(archivo)
                logger.info(f"  Leyendo {archivo.name}: {len(df_raw):,} filas")

                # Detectar fuente por presencia de columnas API
                cols_lower = [c.lower() for c in df_raw.columns]
                es_api = (
                    "nombreentidad" in cols_lower
                    and ("apropiacioninicial" in cols_lower or "nombreentidad" in cols_lower)
                    and any(c in cols_lower for c in [
                        "codigotipogasto", "nombretipogasto", "recursospresupuestales"
                    ])
                )

                if es_api or anio >= 2019:
                    df_proc = procesar_api_socrata(df_raw, anio)
                else:
                    df_proc = procesar_excel_men(df_raw, anio)

                if df_proc is not None and len(df_proc) > 0:
                    lista_dfs.append(df_proc)

            except Exception as e:
                logger.error(f"  ERROR en {archivo.name}: {e}")
                import traceback; traceback.print_exc()

    if not lista_dfs:
        logger.error("No se cargó ningún archivo.")
        return None

    # ── Consolidar ─────────────────────────────────────────────────────────
    logger.info(f"\nConsolidando {len(lista_dfs)} DataFrames...")
    # Pre-normalizar índices y eliminar cols duplicadas antes del concat
    lista_clean = []
    for df_i in lista_dfs:
        df_i = df_i.reset_index(drop=True)
        df_i = df_i.loc[:, ~df_i.columns.duplicated(keep="first")]
        lista_clean.append(df_i)

    df_total = pd.concat(lista_clean, ignore_index=True, sort=False)
    logger.info(f"Total antes de deduplicar: {len(df_total):,}")

    df_total = df_total.drop_duplicates()
    logger.info(f"Total tras deduplicar: {len(df_total):,}")

    # ── Garantizar esquema canónico completo ────────────────────────────────
    for col in COLUMNAS_CANONICAS:
        if col not in df_total.columns:
            df_total[col] = np.nan

    # Reordenar: canónicas primero, el resto al final
    otras = [c for c in df_total.columns if c not in COLUMNAS_CANONICAS]
    df_total = df_total[COLUMNAS_CANONICAS + otras]

    # Tipos garantizados
    for col in COLUMNAS_NUMERICAS:
        df_total[col] = pd.to_numeric(df_total[col], errors="coerce").fillna(0.0)
    df_total["anio_proceso"] = pd.to_numeric(df_total["anio_proceso"], errors="coerce").astype("Int64")

    # ── Guardar ─────────────────────────────────────────────────────────────
    ruta = PROCESSED_PTE / "pte_limpio_consolidado.parquet"
    df_total.to_parquet(ruta, index=False)

    logger.info(f"\n✅ Consolidado: {ruta}")
    logger.info(f"   {len(df_total):,} filas · {len(df_total.columns)} columnas")

    # ── Reporte de calidad ───────────────────────────────────────────────────
    logger.info("\n" + "=" * 65)
    logger.info("CALIDAD DEL CONSOLIDADO")
    logger.info("=" * 65)
    for col in COLUMNAS_CANONICAS:
        nulls = df_total[col].isna().sum()
        pct   = nulls / len(df_total) * 100
        icon  = "✅" if pct == 0 else "⚠️" if pct < 50 else "🔴"
        logger.info(f"  {icon} {col}: {nulls:,} nulos ({pct:.1f}%)")

    logger.info("\n  💰 Totales presupuestales:")
    for col in COLUMNAS_NUMERICAS:
        logger.info(f"     {col}: ${df_total[col].sum():,.0f} COP")

    logger.info("\nSiguiente paso:")
    logger.info("  python src/transformacion/generar_dimensiones_hechos_pte.py")
    logger.info("=" * 65)
    return df_total


if __name__ == "__main__":
    limpieza_pte_profesional()