"""
generar_dimensiones_hechos_pte.py — Transformación al Modelo Estrella PTE
==========================================================================
RESPONSABILIDAD: Lee el consolidado limpio y genera las 4 tablas del modelo:
  - dim_entidad.parquet
  - dim_periodo.parquet
  - dim_rubro.parquet
  - fact_presupuesto.parquet

Entrada:  datos/processed/pte/pte_limpio_consolidado.parquet
          (generado por src/ingesta/limpieza_pte.py)

Salida:   datos/processed/pte/dimensiones/dim_entidad.parquet
          datos/processed/pte/dimensiones/dim_periodo.parquet
          datos/processed/pte/dimensiones/dim_rubro.parquet
          datos/processed/pte/hechos/fact_presupuesto.parquet

Siguiente paso: python src/modelo/crear_modelo_estrella_pte.py
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR      = Path(__file__).parent.parent.parent
PROCESSED_PTE = BASE_DIR / "datos" / "processed" / "pte"
CONSOLIDADO   = PROCESSED_PTE / "pte_limpio_consolidado.parquet"
DIM_DIR       = PROCESSED_PTE / "dimensiones"
HECHOS_DIR    = PROCESSED_PTE / "hechos"

COLUMNAS_NUMERICAS = [
    "apropiacioninicial", "apropiacionvigente",
    "compromisos", "obligaciones", "pagos",
]


def generar_dimensiones_hechos() -> bool:
    """
    Genera las dimensiones y la tabla de hechos del Modelo Estrella PTE
    a partir del consolidado limpio.

    Returns:
        True si se generó todo correctamente, False si hubo error.
    """
    logger.info("=" * 65)
    logger.info("GENERANDO DIMENSIONES Y HECHOS PTE")
    logger.info("Entrada: pte_limpio_consolidado.parquet")
    logger.info("=" * 65)

    if not CONSOLIDADO.exists():
        logger.error(f"No existe el consolidado en: {CONSOLIDADO}")
        logger.error("Ejecuta primero: python src/ingesta/limpieza_pte.py")
        return False

    DIM_DIR.mkdir(parents=True, exist_ok=True)
    HECHOS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"\nLeyendo consolidado...")
    df = pd.read_parquet(CONSOLIDADO)
    logger.info(f"  {len(df):,} filas · {len(df.columns)} columnas")

    # ── 1. dim_entidad ────────────────────────────────────────────────────────
    logger.info("\n── dim_entidad ──")

    # Incluir uej_codigo si está disponible
    cols_ent = ["nombreentidad"]
    if "uej_codigo" in df.columns and df["uej_codigo"].notna().any():
        cols_ent.append("uej_codigo")

    dim_entidad = (
        df[cols_ent].dropna(subset=["nombreentidad"])
        .drop_duplicates(subset=cols_ent)
        .sort_values("nombreentidad")
        .reset_index(drop=True)
    )
    dim_entidad.insert(0, "id_entidad", dim_entidad.index + 1)

    ruta_ent = DIM_DIR / "dim_entidad.parquet"
    dim_entidad.to_parquet(ruta_ent, index=False)
    logger.info(f"  ✅ {len(dim_entidad):,} entidades → {ruta_ent.name}")
    logger.info(f"     Columnas: {dim_entidad.columns.tolist()}")

    # ── 2. dim_periodo ────────────────────────────────────────────────────────
    logger.info("\n── dim_periodo ──")

    dim_periodo = (
        df[["anio_proceso"]].dropna()
        .drop_duplicates()
        .sort_values("anio_proceso")
        .reset_index(drop=True)
    )
    dim_periodo.insert(0, "id_periodo", dim_periodo.index + 1)

    ruta_per = DIM_DIR / "dim_periodo.parquet"
    dim_periodo.to_parquet(ruta_per, index=False)
    logger.info(f"  ✅ {len(dim_periodo):,} períodos → {ruta_per.name}")
    logger.info(f"     Años: {sorted(dim_periodo['anio_proceso'].astype(str).tolist())}")

    # ── 3. dim_rubro ─────────────────────────────────────────────────────────
    logger.info("\n── dim_rubro ──")

    # Columnas descriptivas del rubro (incluye jerarquía API si existe)
    cols_rub_base = ["rubro", "descripcion"]
    cols_rub_extra = [c for c in ["tipo_gasto", "nivel_rubro", "detalle_gasto",
                                   "cuarto_nivel", "quinto_nivel"]
                      if c in df.columns and df[c].notna().any()]
    cols_rub = cols_rub_base + cols_rub_extra

    # Deduplicar por descripcion, priorizando las filas que SÍ traen el desglose (API) y no los nulos del Excel
    dim_rubro = (
        df[cols_rub].dropna(subset=["descripcion"])
        .sort_values(["descripcion", "quinto_nivel", "tipo_gasto"], na_position="last")
        .drop_duplicates(subset=["descripcion"], keep="first")
        .sort_values("descripcion")
        .reset_index(drop=True)
    )
    dim_rubro.insert(0, "id_rubro", dim_rubro.index + 1)

    ruta_rub = DIM_DIR / "dim_rubro.parquet"
    dim_rubro.to_parquet(ruta_rub, index=False)
    logger.info(f"  ✅ {len(dim_rubro):,} rubros únicos → {ruta_rub.name}")
    logger.info(f"     Columnas: {dim_rubro.columns.tolist()}")

    # ── 4. fact_presupuesto ───────────────────────────────────────────────────
    logger.info("\n── fact_presupuesto ──")

    # Mapas de surrogate keys
    map_ent = dict(zip(dim_entidad["nombreentidad"], dim_entidad["id_entidad"]))
    map_per = dict(zip(dim_periodo["anio_proceso"].astype(str), dim_periodo["id_periodo"]))
    map_rub = dict(zip(dim_rubro["descripcion"], dim_rubro["id_rubro"]))

    fact = df.copy()
    fact["id_entidad"] = fact["nombreentidad"].map(map_ent)
    fact["id_periodo"] = fact["anio_proceso"].astype(str).map(map_per)
    fact["id_rubro"]   = fact["descripcion"].map(map_rub)

    # Asegurar tipos numéricos en medidas
    for col in COLUMNAS_NUMERICAS:
        fact[col] = pd.to_numeric(fact[col], errors="coerce").fillna(0.0)

    # Solo filas con id_entidad e id_periodo resueltos y con valor real
    fact = fact.dropna(subset=["id_entidad", "id_periodo"])
    fact = fact[fact[COLUMNAS_NUMERICAS].sum(axis=1) > 0]

    # Columnas finales de la fact
    cols_fact = ["id_entidad", "id_rubro", "id_periodo"] + COLUMNAS_NUMERICAS
    # Incluir tipo_fuente y anio_proceso para filtros rápidos en el dashboard
    if "tipo_fuente"  in fact.columns: cols_fact.append("tipo_fuente")
    if "fuente"       in fact.columns: cols_fact.append("fuente")

    fact = fact[cols_fact].reset_index(drop=True)

    # Castear IDs a Int64 (nullable)
    for col in ["id_entidad", "id_periodo", "id_rubro"]:
        fact[col] = fact[col].astype("Int64")

    ruta_fact = HECHOS_DIR / "fact_presupuesto.parquet"
    fact.to_parquet(ruta_fact, index=False)
    logger.info(f"  ✅ {len(fact):,} hechos → {ruta_fact.name}")

    # Reporte de integridad
    nulos_ids = fact[["id_entidad", "id_rubro", "id_periodo"]].isna().sum()
    logger.info(f"     IDs nulos: {nulos_ids.to_dict()}")

    # ── Resumen final ────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 65)
    logger.info("RESUMEN DIMENSIONES Y HECHOS")
    logger.info("=" * 65)

    for nombre, ruta, n in [
        ("dim_entidad",     ruta_ent,  len(dim_entidad)),
        ("dim_periodo",     ruta_per,  len(dim_periodo)),
        ("dim_rubro",       ruta_rub,  len(dim_rubro)),
        ("fact_presupuesto",ruta_fact, len(fact)),
    ]:
        size_kb = ruta.stat().st_size / 1024
        logger.info(f"  {nombre}: {n:,} registros · {size_kb:.0f} KB")

    logger.info("\n  💰 Totales en fact_presupuesto:")
    for col in COLUMNAS_NUMERICAS:
        logger.info(f"     {col}: ${fact[col].sum():,.0f} COP")

    logger.info("\nSiguiente paso:")
    logger.info("  python src/modelo/crear_modelo_estrella_pte.py")
    logger.info("=" * 65)
    return True


if __name__ == "__main__":
    ok = generar_dimensiones_hechos()
    exit(0 if ok else 1)