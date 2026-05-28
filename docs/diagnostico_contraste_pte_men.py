"""
diagnostico_contraste_pte_men.py
================================

Lee el contraste 2019-2024 y muestra un resumen ejecutivo de cobertura:
- cuánto presupuesto aparece en el universo MEN/API total,
- cuánto capta la serie pipeline por IES,
- brecha porcentual por año.
"""

from pathlib import Path
import pandas as pd


BASE = Path(__file__).resolve().parent.parent
CONTRASTE_PATH = BASE / "datos" / "processed" / "pte" / "contraste_men_vs_fuentes_2019_2024.csv"


def main() -> None:
    if not CONTRASTE_PATH.exists():
        print(f"[ERROR] No existe {CONTRASTE_PATH}")
        print("Primero ejecuta: python docs/build_contraste_pte_men_2019_2024.py")
        return

    df = pd.read_csv(CONTRASTE_PATH)
    num_cols = [
        "pagos_pipeline_B",
        "pagos_men_total_reportado_B",
        "pagos_men_filtro_ies_vig_actual_B",
        "pct_pipeline_vs_men_total",
        "pct_pipeline_vs_men_vig_actual",
        "pct_rows_filtro_ies",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    print("=" * 88)
    print("DIAGNÓSTICO DE CONTRASTE MEN VS PIPELINE IES (2019-2024)")
    print("=" * 88)

    show_cols = [
        "anio_proceso",
        "pagos_pipeline_B",
        "pagos_men_total_reportado_B",
        "pagos_men_filtro_ies_vig_actual_B",
        "pct_pipeline_vs_men_total",
        "pct_pipeline_vs_men_vig_actual",
        "pct_rows_filtro_ies",
    ]
    show_cols = [c for c in show_cols if c in df.columns]
    print(df[show_cols].to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

    total_pipe = df.get("pagos_pipeline_B", pd.Series(dtype=float)).sum()
    total_men = df.get("pagos_men_total_reportado_B", pd.Series(dtype=float)).sum()
    total_men_ies = df.get("pagos_men_filtro_ies_vig_actual_B", pd.Series(dtype=float)).sum()

    print("\n" + "-" * 88)
    print(f"Total pipeline IES (2019-2024):              {total_pipe:,.2f} B COP")
    print(f"Total MEN/API reportado (2019-2024):         {total_men:,.2f} B COP")
    print(f"Total MEN filtro IES vigencia actual:         {total_men_ies:,.2f} B COP")
    if total_men > 0:
        print(f"Cobertura pipeline frente a MEN total:        {(total_pipe/total_men)*100:,.2f}%")
    print("-" * 88)


if __name__ == "__main__":
    main()
