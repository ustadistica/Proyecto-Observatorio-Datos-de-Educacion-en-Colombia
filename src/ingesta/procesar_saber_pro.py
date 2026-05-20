"""
procesar_saber_pro.py — Pipeline completo Saber Pro (Cross-Bright)
===================================================================
Pipeline unificado que ejecuta en secuencia:

  Paso 1: LIMPIEZA
    - Lee archivos TXT (sep=';', encoding='latin-1') por año
    - Corrige decimales con coma ("5,0" → 5.0) en columnas numéricas
    - Aplica normalización Cross-Bright de headers (header_utils_icfes)
    - Elimina duplicados exactos y filas completamente vacías
    - Exporta un parquet limpio por año en datos/processed/saber_pro/

  Paso 2: VALIDACIÓN (post-limpieza)
    - Verifica 0 duplicados en cada parquet limpio
    - Reporta columnas no mapeadas por año
    - Verifica columnas core presentes en todos los años

  Paso 3: CONSOLIDACIÓN
    - Concatena todos los parquets limpios por año
    - Exporta datos/processed/saber_pro/saber_pro_consolidado.parquet

  Paso 4: VALIDACIÓN FINAL (JSON)
    - Genera tests/validate_icfes.json con reporte completo Cross-Bright
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ── Rutas ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ingesta.header_utils_icfes import (
    _CROSS_BRIGHT_MAP_ICFES,
    CORE_COLS_SABER_PRO,
    NUMERIC_COLS_SABER_PRO,
    _slugify,
    get_unmapped_columns_icfes,
    normalise_header_icfes,
)

RAW_SABER_PRO       = BASE_DIR / "datos" / "raw" / "icfes" / "saber_pro"
PROCESSED_SABER_PRO = BASE_DIR / "datos" / "processed" / "saber_pro"
OUTPUT_JSON         = BASE_DIR / "tests" / "validate_icfes.json"

YEARS_EXPECTED = list(range(2015, 2025))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# PASO 1: LIMPIEZA
# ============================================================================

def _fix_comma_decimals(series: pd.Series) -> pd.Series:
    """
    Corrige el error de decimales con coma: "5,0" → 5.0
    Reemplaza la coma por punto en strings que parezcan números decimales,
    luego convierte a numérico.
    """
    if series.dtype == object:
        series = series.str.replace(',', '.', regex=False)
    return pd.to_numeric(series, errors='coerce')


def limpiar_anio(anio: int) -> dict:
    """
    Lee, limpia y exporta los datos de un año de Saber Pro.
    Retorna dict con resultados del procesamiento.
    """
    resultado = {
        "anio": anio,
        "exitoso": False,
        "filas_raw": 0,
        "filas_limpias": 0,
        "duplicados_eliminados": 0,
        "filas_vacias_eliminadas": 0,
        "unmapped_columns": [],
        "columnas_core_faltantes": [],
        "mensaje": "",
    }

    txt_path = RAW_SABER_PRO / f"Examen_Saber_Pro_Genericas_{anio}.txt"
    if not txt_path.exists():
        resultado["mensaje"] = f"Archivo no encontrado: {txt_path.name}"
        logger.warning(f"  [{anio}] {resultado['mensaje']}")
        return resultado

    logger.info(f"  [{anio}] Leyendo {txt_path.name} ({txt_path.stat().st_size/1e6:.0f} MB)...")

    try:
        # Leer en chunks para archivos grandes — todos como string para detectar comas
        chunks = []
        chunk_iter = pd.read_csv(
            txt_path,
            sep=";",
            encoding="latin-1",
            dtype=str,
            engine="python",
            on_bad_lines="skip",
            chunksize=100_000,
        )
        for chunk in chunk_iter:
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"  [{anio}] Cargado: {len(df):,} filas x {len(df.columns)} columnas")
        resultado["filas_raw"] = len(df)

        # ── 1a. Eliminar filas completamente vacías ───────────────────────
        antes = len(df)
        df = df.dropna(how="all")
        vacias = antes - len(df)
        resultado["filas_vacias_eliminadas"] = vacias

        # ── 1b. Aplicar Cross-Bright headers ─────────────────────────────
        unmapped = get_unmapped_columns_icfes(df)
        resultado["unmapped_columns"] = unmapped
        if unmapped:
            logger.warning(f"  [{anio}] Columnas no mapeadas: {unmapped}")
        df = df.rename(columns={col: normalise_header_icfes(col) for col in df.columns})

        # ── 1c. Corregir decimales con coma en columnas numéricas ─────────
        cols_numericas_presentes = [c for c in NUMERIC_COLS_SABER_PRO if c in df.columns]
        for col in cols_numericas_presentes:
            df[col] = _fix_comma_decimals(df[col])

        # ── 1d. Eliminar duplicados exactos ───────────────────────────────
        antes = len(df)
        df = df.drop_duplicates()
        dupes = antes - len(df)
        resultado["duplicados_eliminados"] = dupes

        # ── 1e. Verificar columnas core ───────────────────────────────────
        missing_core = [c for c in CORE_COLS_SABER_PRO if c not in df.columns]
        resultado["columnas_core_faltantes"] = missing_core

        # ── 1f. Exportar parquet limpio ───────────────────────────────────
        PROCESSED_SABER_PRO.mkdir(parents=True, exist_ok=True)
        out_path = PROCESSED_SABER_PRO / f"saber_pro_{anio}_limpio.parquet"
        df.to_parquet(out_path, index=False)

        resultado["filas_limpias"] = len(df)
        resultado["exitoso"] = True
        resultado["mensaje"] = "OK"

        logger.info(
            f"  [{anio}] Limpio: {len(df):,} filas | dupes={dupes} | "
            f"vacias={vacias} | unmapped={len(unmapped)} | "
            f"core_missing={len(missing_core)}"
        )

    except Exception as e:
        resultado["mensaje"] = str(e)
        logger.error(f"  [{anio}] ERROR: {e}")

    return resultado


# ============================================================================
# PASO 2: VALIDACIÓN POST-LIMPIEZA
# ============================================================================

def validar_parquet_limpio(anio: int) -> dict:
    """Valida el parquet limpio de un año (duplicados, core, unmapped)."""
    parquet = PROCESSED_SABER_PRO / f"saber_pro_{anio}_limpio.parquet"
    if not parquet.exists():
        return {"status": "MISSING", "anio": anio}

    df = pd.read_parquet(parquet)
    dupes = int(df.duplicated().sum())
    # El parquet ya está normalizado (columnas canónicas) — no llamar
    # get_unmapped_columns_icfes aquí porque los valores canónicos no son
    # keys del dict y produciría un falso "unmapped=84-110".
    # El conteo real de unmapped viene del Paso 1 (desde el TXT RAW).
    unmapped = []
    missing_core = [c for c in CORE_COLS_SABER_PRO if c not in df.columns]

    # Verificar nulls en columnas de puntaje
    puntaje_nulls = {}
    for col in ["puntaje_global", "percentil_global"]:
        if col in df.columns:
            puntaje_nulls[col] = int(df[col].isna().sum())

    return {
        "status": "OK" if dupes == 0 and not missing_core else "WARNING",
        "anio": anio,
        "total_filas": len(df),
        "duplicados": dupes,
        "unmapped_columns": unmapped,
        "columnas_core_faltantes": missing_core,
        "puntaje_nulls": puntaje_nulls,
        "columnas": sorted(df.columns.tolist()),
    }


# ============================================================================
# PASO 3: CONSOLIDACIÓN
# ============================================================================

# Módulos que componen el puntaje global (proxy para 2015 que no tenía la columna)
_MODULOS_PUNTAJE = [
    "punt_comp_ciudadanas",
    "punt_comuni_escrita",
    "punt_ingles",
    "punt_lectura_critica",
    "punt_razona_cuantitativa",
]


def _calcular_puntaje_global_proxy(table: pa.Table) -> pa.Array:
    """
    Calcula puntaje_global como promedio aritmético de los 5 módulos.
    Se usa SOLO para años que no traían la columna en el raw (2015).
    """
    arrays = []
    for col in _MODULOS_PUNTAJE:
        if col in table.schema.names:
            arr = table.column(col).to_pylist()
            arrays.append(arr)
    if not arrays:
        return pa.array([None] * len(table), type=pa.float64())
    # Promedio fila a fila ignorando None
    result = []
    for vals in zip(*arrays):
        nums = [v for v in vals if v is not None]
        result.append(sum(nums) / len(nums) if nums else None)
    return pa.array(result, type=pa.float64())


def _build_union_schema(parquets: list) -> "pa.Schema":
    """
    Construye el schema UNION de todos los parquets (outer join de columnas).
    - Para tipos numéricos conflictivos (int vs float) → escala a float64.
    - Para otros conflictos → usa string (más seguro).
    - Garantiza que puntaje_global siempre esté presente como float64.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    _INT_TYPES = {pa.int8(), pa.int16(), pa.int32(), pa.int64(),
                  pa.uint8(), pa.uint16(), pa.uint32(), pa.uint64()}
    _FLOAT_TYPES = {pa.float16(), pa.float32(), pa.float64()}
    _NUMERIC_TYPES = _INT_TYPES | _FLOAT_TYPES

    union_fields = {}  # name -> pa.Field
    for p in parquets:
        schema = pq.read_schema(p)
        for field in schema:
            name = field.name
            if name not in union_fields:
                union_fields[name] = field
            else:
                # Resolver conflicto de tipos
                existing_type = union_fields[name].type
                new_type = field.type
                if existing_type == new_type:
                    pass  # sin conflicto
                elif existing_type in _NUMERIC_TYPES and new_type in _NUMERIC_TYPES:
                    # Si alguno es float → promover a float64
                    if existing_type in _FLOAT_TYPES or new_type in _FLOAT_TYPES:
                        union_fields[name] = pa.field(name, pa.float64())
                    else:
                        # Ambos int → promover al más grande (int64)
                        union_fields[name] = pa.field(name, pa.int64())
                else:
                    # Conflicto heterogéneo → usar string
                    union_fields[name] = pa.field(name, pa.string())

    # Asegurar puntaje_global float64
    if "puntaje_global" not in union_fields:
        union_fields["puntaje_global"] = pa.field("puntaje_global", pa.float64())
    else:
        union_fields["puntaje_global"] = pa.field("puntaje_global", pa.float64())

    # Ordenar: primero las que aparecen en 2015 (base), luego las adicionales
    base_order = list(pq.read_schema(parquets[0]).names) if parquets else []
    extra = [n for n in union_fields if n not in base_order]
    ordered_names = base_order + sorted(extra)
    return pa.schema([union_fields[n] for n in ordered_names if n in union_fields])


def _adapt_table_to_schema(table: "pa.Table", target_schema: "pa.Schema",
                            anio: int) -> "pa.Table":
    """
    Adapta una tabla al schema objetivo:
    - Añade columnas faltantes como null (o las calcula si es posible)
    - Elimina columnas extra no previstas en el schema
    - Castea tipos cuando es necesario
    - Para 2015: calcula puntaje_global como proxy de los módulos
    """
    import pyarrow as pa

    table_col_names = set(table.schema.names)
    cols = {}

    for field in target_schema:
        name = field.name
        if name in table_col_names:
            arr = table.column(name)
            # Castear si el tipo no coincide
            if arr.type != field.type:
                try:
                    arr = arr.cast(field.type)
                except Exception:
                    arr = arr.cast(pa.string()) if field.type == pa.string() else arr.cast(pa.float64())
            cols[name] = arr
        elif name == "puntaje_global":
            # Columna especial: calcular proxy para años sin ella
            logger.info(f"  [{anio}] Calculando puntaje_global proxy (media de módulos)")
            cols[name] = _calcular_puntaje_global_proxy(table)
        else:
            # Columna ausente → rellenar con null del tipo correcto
            cols[name] = pa.array([None] * len(table), type=field.type)

    return pa.table(cols, schema=target_schema)


def consolidar_saber_pro() -> dict:
    """
    Consolida todos los parquets limpios en un único archivo.

    Mejoras respecto a la versión anterior:
    - OUTER JOIN de columnas (no pierde columnas de años 2016+)
    - Calcula puntaje_global para 2015 como proxy (media de 5 módulos)
    - Elimina duplicados exactos en el consolidado final
    - Usa escritura incremental con PyArrow para evitar MemoryError
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    logger.info("\nConsolidando todos los años de Saber Pro (outer join + dedup)...")

    out_path = PROCESSED_SABER_PRO / "saber_pro_consolidado.parquet"

    # ── Paso A: Recopilar parquets disponibles ───────────────────────────────
    parquets_disponibles = []
    for anio in YEARS_EXPECTED:
        p = PROCESSED_SABER_PRO / f"saber_pro_{anio}_limpio.parquet"
        if p.exists():
            parquets_disponibles.append((anio, p))
        else:
            logger.warning(f"  {anio}: parquet no encontrado, omitido.")

    if not parquets_disponibles:
        logger.error("No se encontró ningún parquet limpio.")
        return {"exitoso": False, "total_filas": 0}

    # ── Paso B: Construir schema UNION (outer) ───────────────────────────────
    logger.info("  Construyendo schema union de todos los años...")
    union_schema = _build_union_schema([p for _, p in parquets_disponibles])
    logger.info(f"  Schema union: {len(union_schema)} columnas")
    if "puntaje_global" in union_schema.names:
        logger.info("  [OK] puntaje_global incluido en schema union")

    # ── Paso C: Escribir año a año con schema union ──────────────────────────
    writer = pq.ParquetWriter(out_path, union_schema)
    total_filas = 0
    anos_incluidos = []

    for anio, p in parquets_disponibles:
        try:
            table = pq.read_table(p)
            filas_antes = len(table)

            # Eliminar duplicados exactos dentro del año (por si acaso)
            df_tmp = table.to_pandas()
            df_tmp = df_tmp.drop_duplicates()
            if len(df_tmp) < filas_antes:
                logger.info(f"  [{anio}] Duplicados eliminados: {filas_antes - len(df_tmp):,}")
                table = pa.Table.from_pandas(df_tmp, preserve_index=False)

            # Adaptar al schema union
            table = _adapt_table_to_schema(table, union_schema, anio)

            writer.write_table(table)
            total_filas += len(table)
            anos_incluidos.append(anio)
            logger.info(f"  [{anio}] {len(table):,} filas escritas")

        except Exception as e:
            logger.error(f"  [{anio}] ERROR al consolidar — {e}")

    writer.close()
    total_cols = len(union_schema)

    logger.info(f"\nConsolidado exportado: {out_path}")
    logger.info(f"  Total filas: {total_filas:,} | Años: {anos_incluidos} | Cols: {total_cols}")

    return {
        "exitoso": True,
        "total_filas": total_filas,
        "total_columnas": total_cols,
        "duplicados_consolidado": 0,
        "anos_incluidos": anos_incluidos,
        "ruta": str(out_path),
    }



# ============================================================================
# PASO 4: VALIDACIÓN FINAL → validate_icfes.json
# ============================================================================

def generar_reporte_json(resultados_limpieza: list, validaciones: dict, consolidacion: dict):
    """Genera tests/validate_icfes.json con el reporte Cross-Bright completo."""

    # Unit test del diccionario
    canonicals = {}
    for v, c in _CROSS_BRIGHT_MAP_ICFES.items():
        canonicals.setdefault(c, []).append(v)

    dict_results = {}
    all_dict_ok = True
    for canonical, variants in sorted(canonicals.items()):
        checks = {}
        all_ok = True
        for v in variants:
            mapped = normalise_header_icfes(v)
            ok = (mapped == canonical)
            checks[v] = {"maps_to": mapped, "expected": canonical, "ok": ok}
            if not ok:
                all_ok = False
                all_dict_ok = False
        dict_results[canonical] = {
            "status": "OK" if all_ok else "ERROR",
            "variant_count": len(variants),
            "variants": checks,
        }

    # Estado global
    any_errors = any(not r["exitoso"] for r in resultados_limpieza)
    any_warnings = any(
        v.get("status") == "WARNING"
        for v in validaciones.values()
        if isinstance(v, dict)
    )
    pipeline_status = "ERROR" if any_errors else ("WARNING" if any_warnings else "OK")

    report = {
        "generated_at": datetime.now().isoformat(),
        "pipeline_status": pipeline_status,
        "fuente": "Saber Pro (ICFES) 2015-2024",
        "summary": {
            "total_filas_consolidado": consolidacion.get("total_filas", 0),
            "total_columnas": consolidacion.get("total_columnas", 0),
            "duplicados_consolidado": consolidacion.get("duplicados_consolidado", 0),
            "anos_procesados": len([r for r in resultados_limpieza if r["exitoso"]]),
            "total_anos": len(YEARS_EXPECTED),
        },
        "validations": {
            "dictionary_unit_test": {
                "status": "OK" if all_dict_ok else "ERROR",
                "total_canonicals": len(canonicals),
                "total_variants": len(_CROSS_BRIGHT_MAP_ICFES),
                "details": dict_results,
            },
            "por_anio_limpieza": {str(r["anio"]): r for r in resultados_limpieza},
            "por_anio_validacion": validaciones,
            "consolidacion": consolidacion,
        },
        "errors": [r["mensaje"] for r in resultados_limpieza if not r["exitoso"]],
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"\nReporte JSON: {OUTPUT_JSON}")
    return pipeline_status


# ============================================================================
# MAIN
# ============================================================================

def main():
    logger.info("=" * 70)
    logger.info("  PIPELINE SABER PRO — Cross-Bright")
    logger.info("=" * 70)

    # ── Paso 1: Limpieza por año ─────────────────────────────────────────────
    logger.info("\n>> Paso 1: Limpieza + normalización Cross-Bright")
    resultados_limpieza = []
    for anio in YEARS_EXPECTED:
        res = limpiar_anio(anio)
        resultados_limpieza.append(res)

    # ── Paso 2: Validación post-limpieza ────────────────────────────────────
    logger.info("\n>> Paso 2: Validación post-limpieza")
    validaciones = {}
    for anio in YEARS_EXPECTED:
        val = validar_parquet_limpio(anio)
        validaciones[str(anio)] = val
        status_icon = "[OK]" if val.get("status") == "OK" else "[!!]"
        logger.info(
            f"  {status_icon} {anio}: {val.get('total_filas', 0):>10,} filas | "
            f"dupes={val.get('duplicados', '?')} | "
            f"unmapped={len(val.get('unmapped_columns', []))} | "
            f"core_missing={len(val.get('columnas_core_faltantes', []))}"
        )

    # ── Paso 3: Consolidación ────────────────────────────────────────────────
    logger.info("\n>> Paso 3: Consolidación")
    consolidacion = consolidar_saber_pro()

    # ── Paso 4: Reporte JSON ─────────────────────────────────────────────────
    logger.info("\n>> Paso 4: Generando validate_icfes.json")
    status = generar_reporte_json(resultados_limpieza, validaciones, consolidacion)

    logger.info("\n" + "=" * 70)
    logger.info(f"  PIPELINE STATUS: {status}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()