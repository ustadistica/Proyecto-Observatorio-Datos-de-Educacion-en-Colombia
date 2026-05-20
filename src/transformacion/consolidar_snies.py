"""
consolidar_snies.py — Consolida graduados y matriculados SNIES en dataset final
================================================================================
Lee los archivos limpios generados por limpieza_snies.py y produce:
  - dataset_snies_consolidado.parquet  (merge anual por IES)

Aplica la regla metodológica oficial del MEN para el cálculo de matrícula anual:
  "Sem1 de todas las IES (excepto SENA) + Sem2 solo del SENA"
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_SNIES = BASE_DIR / "datos" / "processed" / "snies"


def consolidar_snies():
    """
    Consolida graduados y matriculados limpios en un único dataset unificado.
    """
    logger.info("Iniciando consolidacion final de SNIES...")

    path_grad = PROCESSED_SNIES / "snies_graduados_limpio_consolidado.parquet"
    path_mat  = PROCESSED_SNIES / "snies_matriculados_limpio_consolidado.parquet"

    if not path_grad.exists() or not path_mat.exists():
        logger.error("No se encontraron los archivos limpios. Ejecute limpieza_snies.py primero.")
        return

    df_grad = pd.read_parquet(path_grad)
    df_mat  = pd.read_parquet(path_mat)

    logger.info(f"Graduados cargados:    {len(df_grad):,} filas")
    logger.info(f"Matriculados cargados: {len(df_mat):,} filas")

    # ── 1. Asegurar tipos numéricos ──────────────────────────────────────────
    df_grad['graduados']    = pd.to_numeric(df_grad['graduados'], errors='coerce').fillna(0).astype(int)
    df_grad['anio_proceso'] = pd.to_numeric(df_grad['anio_proceso'], errors='coerce').fillna(0).astype(int)

    df_mat['matriculados']  = pd.to_numeric(df_mat['matriculados'], errors='coerce').fillna(0).astype(int)
    df_mat['anio_proceso']  = pd.to_numeric(df_mat['anio_proceso'], errors='coerce').fillna(0).astype(int)
    df_mat['semestre']      = pd.to_numeric(df_mat['semestre'], errors='coerce').fillna(1).astype(int)

    # ── 2. Aplicar regla MEN para matrícula anual ────────────────────────────
    logger.info("Aplicando regla metodologica MEN para matricula anual...")
    df_mat['nombre_institucion'] = df_mat['nombre_institucion'].fillna("").astype(str).str.upper()

    cond_ies_s1  = (df_mat['semestre'] == 1) & (~df_mat['nombre_institucion'].str.contains('SENA', na=False))
    cond_sena_s2 = (df_mat['semestre'] == 2) & (df_mat['nombre_institucion'].str.contains('SENA', na=False))
    df_mat_anual = df_mat[cond_ies_s1 | cond_sena_s2].copy()

    # ── 3. Agregar por año + institución ─────────────────────────────────────
    logger.info("Agregando matriculados (regla MEN)...")
    agg_mat = df_mat_anual.groupby(
        ['anio_proceso', 'codigo_institucion', 'nombre_institucion'], as_index=False
    ).agg(total_matriculados=('matriculados', 'sum'))

    logger.info("Agregando graduados...")
    agg_grad = df_grad.groupby(
        ['anio_proceso', 'codigo_institucion', 'nombre_institucion'], as_index=False
    ).agg(total_graduados=('graduados', 'sum'))

    # ── 4. Merge final ───────────────────────────────────────────────────────
    logger.info("Cruce final Matriculados x Graduados...")
    df_final = pd.merge(
        agg_mat, agg_grad,
        on=['anio_proceso', 'codigo_institucion', 'nombre_institucion'],
        how='outer'
    )
    df_final['total_matriculados'] = df_final['total_matriculados'].fillna(0).astype(int)
    df_final['total_graduados']    = df_final['total_graduados'].fillna(0).astype(int)

    # ── 5. Verificación contra cifras oficiales ──────────────────────────────
    logger.info("\n" + "=" * 70)
    logger.info("  VERIFICACION CONTRA REPORTE OFICIAL SNIES")
    logger.info("=" * 70)
    for year in range(2015, 2025):
        dy = df_final[df_final['anio_proceso'] == year]
        t_mat  = dy['total_matriculados'].sum()
        t_grad = dy['total_graduados'].sum()
        logger.info(f"  {year}  |  Matriculados: {t_mat:>10,}  |  Graduados: {t_grad:>10,}")

    # ── 6. Exportar ──────────────────────────────────────────────────────────
    out_path = PROCESSED_SNIES / "dataset_snies_consolidado.parquet"
    df_final.to_parquet(out_path, index=False)
    logger.info(f"\nArchivo consolidado exportado: {out_path}")
    logger.info(f"   Filas: {len(df_final):,}  |  Columnas: {len(df_final.columns)}")


if __name__ == "__main__":
    consolidar_snies()
