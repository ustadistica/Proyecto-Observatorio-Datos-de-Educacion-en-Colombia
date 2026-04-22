"""
crear_modelo_estrella_pte.py — Orquestador del Pipeline PTE + DuckDB
=====================================================================
RESPONSABILIDAD:
  1. Verifica que existan los artefactos de las etapas previas.
  2. Opcionalmente ejecuta las etapas anteriores si no existen.
  3. Crea la base de datos DuckDB del Modelo Estrella PTE con las
     4 tablas (3 dims + 1 fact) y vistas analíticas precalculadas.
  4. Valida integridad referencial y reporta estadísticas finales.

Pipeline completo PTE:
  [1] src/ingesta/pte.py              → raw/pte/<año>/*.parquet
  [2] src/ingesta/limpieza_pte.py     → processed/pte/pte_limpio_consolidado.parquet
  [3] src/transformacion/generar_dimensiones_hechos_pte.py
                                      → processed/pte/dimensiones/*.parquet
                                      → processed/pte/hechos/fact_presupuesto.parquet
  [4] src/modelo/crear_modelo_estrella_pte.py ← ESTE SCRIPT
                                      → processed/modelos/pte/modelo_estrella_pte.duckdb

Uso:
  python src/modelo/crear_modelo_estrella_pte.py
  python src/modelo/crear_modelo_estrella_pte.py --reconstruir   # regenera todo
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import duckdb

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR      = Path(__file__).parent.parent.parent
PROCESSED_PTE = BASE_DIR / "datos" / "processed" / "pte"
MODELOS_DIR   = BASE_DIR / "datos" / "processed" / "modelos" / "pte"

# ── Rutas de artefactos ───────────────────────────────────────────────────────
CONSOLIDADO   = PROCESSED_PTE / "pte_limpio_consolidado.parquet"
DIM_ENTIDAD   = PROCESSED_PTE / "dimensiones" / "dim_entidad.parquet"
DIM_PERIODO   = PROCESSED_PTE / "dimensiones" / "dim_periodo.parquet"
DIM_RUBRO     = PROCESSED_PTE / "dimensiones" / "dim_rubro.parquet"
FACT          = PROCESSED_PTE / "hechos"      / "fact_presupuesto.parquet"
DB_PATH       = MODELOS_DIR   / "modelo_estrella_pte.duckdb"


# ── Verificación de pre-requisitos ────────────────────────────────────────────

def verificar_artefactos(reconstruir: bool = False) -> bool:
    """
    Comprueba que los parquets necesarios existan.
    Si no existen (o reconstruir=True), ejecuta las etapas previas.
    """
    artefactos_ok = all([
        CONSOLIDADO.exists(),
        DIM_ENTIDAD.exists(), DIM_PERIODO.exists(), DIM_RUBRO.exists(),
        FACT.exists(),
    ])

    if artefactos_ok and not reconstruir:
        logger.info("✅ Todos los artefactos existen. Usando los ya generados.")
        return True

    if reconstruir:
        logger.info("🔄 Modo --reconstruir: regenerando todo desde limpieza...")
    else:
        logger.info("⚠️  Artefactos faltantes. Ejecutando pipeline previo...")

    # ── Etapa 2: Limpieza ────────────────────────────────────────────────────
    if not CONSOLIDADO.exists() or reconstruir:
        logger.info("\n[ETAPA 2] Ejecutando limpieza_pte.py...")
        sys.path.insert(0, str(BASE_DIR))
        from src.ingesta.limpieza_pte import limpieza_pte_profesional
        df = limpieza_pte_profesional()
        if df is None or len(df) == 0:
            logger.error("Limpieza falló. Abortando.")
            return False

    # ── Etapa 3: Dimensiones y Hechos ────────────────────────────────────────
    dims_faltan = not all([DIM_ENTIDAD.exists(), DIM_PERIODO.exists(),
                           DIM_RUBRO.exists(), FACT.exists()])
    if dims_faltan or reconstruir:
        logger.info("\n[ETAPA 3] Ejecutando generar_dimensiones_hechos_pte.py...")
        sys.path.insert(0, str(BASE_DIR))
        from src.transformacion.generar_dimensiones_hechos_pte import generar_dimensiones_hechos
        ok = generar_dimensiones_hechos()
        if not ok:
            logger.error("Generación de dimensiones/hechos falló. Abortando.")
            return False

        logger.info("\n[ETAPA 3.5] Mapeando Códigos IES/DANE a Entidades...")
        from src.transformacion.mapear_entidades_pte import mapear_entidades
        ok_mapeo = mapear_entidades()
        if not ok_mapeo:
            logger.error("Mapeo de entidades falló. Abortando.")
            return False

    return True


# ── Construcción del DuckDB ───────────────────────────────────────────────────

def crear_modelo_estrella_duckdb():
    """
    Crea la base de datos DuckDB del Modelo Estrella PTE:
    - Carga las 4 tablas desde Parquet
    - Crea vistas analíticas predefinidas
    - Valida integridad referencial
    - Reporta estadísticas de calidad
    """
    logger.info("\n" + "=" * 65)
    logger.info("CREANDO MODELO ESTRELLA PTE — DuckDB")
    logger.info("=" * 65)

    MODELOS_DIR.mkdir(parents=True, exist_ok=True)

    # Borrar DB anterior
    if DB_PATH.exists():
        os.remove(DB_PATH)
        logger.info(f"  🗑️  BD anterior eliminada.")

    conn = duckdb.connect(str(DB_PATH))
    logger.info(f"  📁 BD nueva: {DB_PATH}")

    # ── Cargar tablas ─────────────────────────────────────────────────────────
    logger.info("\n── Cargando tablas ──")

    tablas = {
        "dim_entidad":      DIM_ENTIDAD,
        "dim_periodo":      DIM_PERIODO,
        "dim_rubro":        DIM_RUBRO,
        "fact_presupuesto": FACT,
    }

    for nombre, ruta in tablas.items():
        ruta_posix = ruta.as_posix()
        conn.execute(f"CREATE TABLE {nombre} AS SELECT * FROM read_parquet('{ruta_posix}')")
        n = conn.execute(f"SELECT COUNT(*) FROM {nombre}").fetchone()[0]
        logger.info(f"  ✅ {nombre}: {n:,} registros")

    # ── Vistas analíticas ─────────────────────────────────────────────────────
    logger.info("\n── Creando vistas analíticas ──")

    # Vista 1: Fact desnormalizada (para dashboard sin joins)
    conn.execute("""
        CREATE VIEW v_presupuesto_completo AS
        SELECT
            e.nombreentidad,
            e.uej_codigo,
            p.anio_proceso,
            r.rubro,
            r.descripcion,
            r.tipo_gasto,
            r.nivel_rubro,
            r.detalle_gasto,
            f.tipo_fuente,
            f.fuente,
            f.apropiacioninicial,
            f.apropiacionvigente,
            f.compromisos,
            f.obligaciones,
            f.pagos,
            -- Métricas derivadas
            ROUND(f.pagos / NULLIF(f.apropiacionvigente, 0) * 100, 2) AS pct_ejecucion,
            f.apropiacionvigente - f.pagos                             AS saldo_por_pagar
        FROM fact_presupuesto f
        LEFT JOIN dim_entidad  e ON f.id_entidad  = e.id_entidad
        LEFT JOIN dim_periodo   p ON f.id_periodo  = p.id_periodo
        LEFT JOIN dim_rubro     r ON f.id_rubro    = r.id_rubro
    """)
    logger.info("  ✅ v_presupuesto_completo")

    # Vista 2: KPIs por año
    conn.execute("""
        CREATE VIEW v_kpis_anual AS
        SELECT
            p.anio_proceso,
            SUM(f.apropiacioninicial)  AS total_apropiacion_inicial,
            SUM(f.apropiacionvigente)  AS total_apropiacion_vigente,
            SUM(f.compromisos)         AS total_compromisos,
            SUM(f.obligaciones)        AS total_obligaciones,
            SUM(f.pagos)               AS total_pagos,
            ROUND(SUM(f.pagos) / NULLIF(SUM(f.apropiacionvigente), 0) * 100, 2) AS pct_ejecucion,
            COUNT(DISTINCT f.id_entidad) AS n_entidades
        FROM fact_presupuesto f
        LEFT JOIN dim_periodo p ON f.id_periodo = p.id_periodo
        GROUP BY p.anio_proceso
        ORDER BY p.anio_proceso
    """)
    logger.info("  ✅ v_kpis_anual")

    # Vista 3: Concentración por entidad
    conn.execute("""
        CREATE VIEW v_ejecucion_por_entidad AS
        SELECT
            e.nombreentidad,
            e.uej_codigo,
            p.anio_proceso,
            SUM(f.apropiacionvigente) AS apropiacion_vigente,
            SUM(f.pagos)              AS pagos,
            ROUND(SUM(f.pagos) / NULLIF(SUM(f.apropiacionvigente), 0) * 100, 2) AS pct_ejecucion
        FROM fact_presupuesto f
        LEFT JOIN dim_entidad  e ON f.id_entidad = e.id_entidad
        LEFT JOIN dim_periodo   p ON f.id_periodo = p.id_periodo
        GROUP BY e.nombreentidad, e.uej_codigo, p.anio_proceso
        ORDER BY p.anio_proceso, pagos DESC
    """)
    logger.info("  ✅ v_ejecucion_por_entidad")

    # Vista 4: Tipo de gasto (Funcionamiento vs Inversión)
    conn.execute("""
        CREATE VIEW v_tipo_gasto_anual AS
        SELECT
            p.anio_proceso,
            COALESCE(r.tipo_gasto, 'SIN CLASIFICAR') AS tipo_gasto,
            SUM(f.apropiacionvigente)                 AS apropiacion_vigente,
            SUM(f.pagos)                              AS pagos
        FROM fact_presupuesto f
        LEFT JOIN dim_periodo p ON f.id_periodo = p.id_periodo
        LEFT JOIN dim_rubro   r ON f.id_rubro   = r.id_rubro
        GROUP BY p.anio_proceso, tipo_gasto
        ORDER BY p.anio_proceso, pagos DESC
    """)
    logger.info("  ✅ v_tipo_gasto_anual")

    # ── Validación de integridad ──────────────────────────────────────────────
    logger.info("\n── Validación de integridad referencial ──")

    orf_ent = conn.execute("""
        SELECT COUNT(*) FROM fact_presupuesto f
        LEFT JOIN dim_entidad e ON f.id_entidad = e.id_entidad
        WHERE e.id_entidad IS NULL
    """).fetchone()[0]

    orf_per = conn.execute("""
        SELECT COUNT(*) FROM fact_presupuesto f
        LEFT JOIN dim_periodo p ON f.id_periodo = p.id_periodo
        WHERE p.id_periodo IS NULL
    """).fetchone()[0]

    orf_rub = conn.execute("""
        SELECT COUNT(*) FROM fact_presupuesto f
        LEFT JOIN dim_rubro r ON f.id_rubro = r.id_rubro
        WHERE r.id_rubro IS NULL AND f.id_rubro IS NOT NULL
    """).fetchone()[0]

    logger.info(f"  Fact sin entidad:  {orf_ent:,} registros {'✅' if orf_ent == 0 else '⚠️'}")
    logger.info(f"  Fact sin período:  {orf_per:,} registros {'✅' if orf_per == 0 else '⚠️'}")
    logger.info(f"  Fact sin rubro:    {orf_rub:,} registros {'ℹ️ (normal para MANUAL_MEN)' if orf_rub > 0 else '✅'}")

    # ── KPIs rápidos ─────────────────────────────────────────────────────────
    logger.info("\n── KPIs del modelo ──")

    kpis = conn.execute("""
        SELECT
            COUNT(*)                       AS total_hechos,
            SUM(apropiacioninicial)        AS total_apropiacion_inicial,
            SUM(apropiacionvigente)        AS total_apropiacion_vigente,
            SUM(pagos)                     AS total_pagos,
            ROUND(SUM(pagos)/NULLIF(SUM(apropiacionvigente),0)*100, 2) AS pct_ejecucion_global
        FROM fact_presupuesto
    """).fetchone()

    logger.info(f"  Total hechos:              {kpis[0]:>12,}")
    logger.info(f"  Apropiación inicial COP:   ${kpis[1]:>20,.0f}")
    logger.info(f"  Apropiación vigente COP:   ${kpis[2]:>20,.0f}")
    logger.info(f"  Pagos ejecutados COP:      ${kpis[3]:>20,.0f}")
    logger.info(f"  % Ejecución global:        {kpis[4]:>10.1f}%")

    logger.info("\n  KPIs por año:")
    rows = conn.execute("SELECT * FROM v_kpis_anual").fetchall()
    for row in rows:
        logger.info(f"    {int(row[0])}: pagos=${row[5]:,.0f} · ejecución={row[6]:.1f}%")

    # ── Tamaño del archivo ────────────────────────────────────────────────────
    conn.close()
    db_mb = DB_PATH.stat().st_size / (1024 * 1024)

    logger.info("\n" + "=" * 65)
    logger.info("MODELO ESTRELLA PTE CREADO EXITOSAMENTE")
    logger.info("=" * 65)
    logger.info(f"  📦 Archivo:  {DB_PATH}")
    logger.info(f"  📐 Tamaño:   {db_mb:.1f} MB")
    logger.info(f"  📋 Tablas:   dim_entidad, dim_periodo, dim_rubro, fact_presupuesto")
    logger.info(f"  👁️  Vistas:   v_presupuesto_completo, v_kpis_anual,")
    logger.info(f"               v_ejecucion_por_entidad, v_tipo_gasto_anual")
    logger.info("=" * 65)


# ── Punto de entrada ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Crea el Modelo Estrella PTE en DuckDB"
    )
    parser.add_argument(
        "--reconstruir", action="store_true",
        help="Regenera todo desde la limpieza (ignora artefactos existentes)"
    )
    args = parser.parse_args()

    logger.info("PIPELINE PTE — Modelo Estrella")
    logger.info(f"  Modo: {'RECONSTRUCCIÓN TOTAL' if args.reconstruir else 'incremental'}")
    logger.info(f"  Base de datos: {DB_PATH}")

    # Verificar o ejecutar etapas previas
    ok = verificar_artefactos(reconstruir=args.reconstruir)
    if not ok:
        logger.error("Pipeline abortado por errores en etapas previas.")
        sys.exit(1)

    # Crear el DuckDB
    crear_modelo_estrella_duckdb()


if __name__ == "__main__":
    main()