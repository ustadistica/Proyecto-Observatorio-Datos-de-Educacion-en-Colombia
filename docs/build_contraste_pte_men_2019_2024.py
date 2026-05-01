"""
build_contraste_pte_men_2019_2024.py
====================================

Construye una tabla de contraste 2019-2024 entre:

1) Serie actual del pipeline consolidado (DNP/SIIF/interpolado), que contiene
   transferencias directas identificadas por IES.
2) Serie reportada en el consolidado "limpio" (universo MEN/API amplio), que
   incluye rubros agregados sin desglose por institución individual.

No toca el pipeline principal ni run_full_pipeline.py.
"""

from __future__ import annotations

from pathlib import Path
import unicodedata
import pandas as pd
import numpy as np


BASE = Path(__file__).resolve().parent.parent
PTE_PIPE_PATH = BASE / "datos" / "processed" / "pte" / "pte_consolidado_full.parquet"
PTE_MEN_PATH = BASE / "datos" / "processed" / "pte" / "pte_limpio_consolidado.parquet"

OUT_CONTRASTE = BASE / "datos" / "processed" / "pte" / "contraste_men_vs_fuentes_2019_2024.csv"
OUT_DIAG = BASE / "datos" / "processed" / "pte" / "diagnostico_cobertura_men_ies_2019_2024.csv"

YEARS = list(range(2019, 2025))

IES_REGEX = (
    r"LEY 30|ARTICULO 86|ARTICULO 87|INSTITUCIONES DE EDUCACION SUPERIOR|"
    r"IES PUBLICAS|A UNIVERSIDADES PARA FUNCIONAMIENTO|TRANSFERENCIAS A UNIVERSIDADES|UNIVERSIDAD"
)

ENTIDAD_UNIV_REGEX = r"UNIVERSIDAD|INSTITUCION UNIVERSITARIA|INSTITUTO TECNICO|ESCUELA TECNOLOGICA"


def ascii_norm(s: object) -> str:
    if pd.isna(s):
        return ""
    return (
        unicodedata.normalize("NFKD", str(s))
        .encode("ascii", "ignore")
        .decode("utf-8")
        .upper()
        .strip()
    )


def main() -> None:
    if not PTE_PIPE_PATH.exists():
        print(f"[ERROR] No existe: {PTE_PIPE_PATH}")
        return
    if not PTE_MEN_PATH.exists():
        print(f"[ERROR] No existe: {PTE_MEN_PATH}")
        return

    pipe = pd.read_parquet(PTE_PIPE_PATH)
    men = pd.read_parquet(PTE_MEN_PATH)

    pipe["anio_proceso"] = pd.to_numeric(pipe.get("anio_proceso"), errors="coerce").astype("Int64")
    pipe["pagos"] = pd.to_numeric(pipe.get("pagos"), errors="coerce").fillna(0.0)
    pipe = pipe[pipe["anio_proceso"].isin(YEARS)].copy()

    men["anio_proceso"] = pd.to_numeric(men.get("anio_proceso"), errors="coerce").astype("Int64")
    men["pagos"] = pd.to_numeric(men.get("pagos"), errors="coerce").fillna(0.0)
    men = men[men["anio_proceso"].isin(YEARS)].copy()

    for col in ["rubro", "descripcion", "nombreentidad", "vigencia_tipo"]:
        if col not in men.columns:
            men[col] = ""
        men[col] = men[col].map(ascii_norm)

    texto = men["rubro"] + " " + men["descripcion"] + " " + men["nombreentidad"]
    mask_ies_texto = texto.str.contains(IES_REGEX, regex=True, na=False)
    mask_univ_entidad = men["nombreentidad"].str.contains(ENTIDAD_UNIV_REGEX, regex=True, na=False)
    mask_vig_actual = men["vigencia_tipo"].eq("VIGENCIAACTUAL")

    rows: list[dict[str, object]] = []
    for year in YEARS:
        s_pipe = pipe[pipe["anio_proceso"] == year]
        s_men = men[men["anio_proceso"] == year]

        men_rows_total = int(len(s_men))
        men_rows_ies = int(mask_ies_texto.loc[s_men.index].sum()) if men_rows_total else 0
        men_rows_univ = int(mask_univ_entidad.loc[s_men.index].sum()) if men_rows_total else 0

        row = {
            "anio_proceso": year,
            "pipeline_rows": int(len(s_pipe)),
            "pipeline_entidades": int(s_pipe["nombre_uej"].nunique()) if "nombre_uej" in s_pipe.columns else np.nan,
            "pagos_pipeline_B": float(s_pipe["pagos"].sum() / 1e12),
            "men_rows_total": men_rows_total,
            "men_entidades_total": int(s_men["nombreentidad"].nunique()) if "nombreentidad" in s_men.columns else np.nan,
            "pagos_men_total_reportado_B": float(s_men["pagos"].sum() / 1e12),
            "pagos_men_vigencia_actual_B": float(s_men.loc[mask_vig_actual.loc[s_men.index], "pagos"].sum() / 1e12),
            "men_rows_filtro_ies": men_rows_ies,
            "pagos_men_filtro_ies_B": float(s_men.loc[mask_ies_texto.loc[s_men.index], "pagos"].sum() / 1e12),
            "pagos_men_filtro_ies_vig_actual_B": float(
                s_men.loc[(mask_ies_texto & mask_vig_actual).loc[s_men.index], "pagos"].sum() / 1e12
            ),
            "men_rows_universidad": men_rows_univ,
            "pagos_men_universidad_B": float(s_men.loc[mask_univ_entidad.loc[s_men.index], "pagos"].sum() / 1e12),
            "pagos_men_universidad_vig_actual_B": float(
                s_men.loc[(mask_univ_entidad & mask_vig_actual).loc[s_men.index], "pagos"].sum() / 1e12
            ),
        }

        row["pct_rows_filtro_ies"] = (men_rows_ies / men_rows_total * 100.0) if men_rows_total else 0.0
        row["pct_rows_universidad"] = (men_rows_univ / men_rows_total * 100.0) if men_rows_total else 0.0
        row["pct_pipeline_vs_men_total"] = (
            (row["pagos_pipeline_B"] / row["pagos_men_total_reportado_B"] * 100.0)
            if row["pagos_men_total_reportado_B"]
            else 0.0
        )
        row["pct_pipeline_vs_men_vig_actual"] = (
            (row["pagos_pipeline_B"] / row["pagos_men_vigencia_actual_B"] * 100.0)
            if row["pagos_men_vigencia_actual_B"]
            else 0.0
        )
        rows.append(row)

    contraste = pd.DataFrame(rows)

    round_cols = [c for c in contraste.columns if c.endswith("_B") or c.startswith("pct_")]
    contraste[round_cols] = contraste[round_cols].round(4)

    OUT_CONTRASTE.parent.mkdir(parents=True, exist_ok=True)
    contraste.to_csv(OUT_CONTRASTE, index=False)

    diag_cols = [
        "anio_proceso",
        "men_rows_total",
        "men_rows_filtro_ies",
        "pct_rows_filtro_ies",
        "men_rows_universidad",
        "pct_rows_universidad",
        "pagos_men_total_reportado_B",
        "pagos_men_filtro_ies_vig_actual_B",
        "pagos_pipeline_B",
        "pct_pipeline_vs_men_total",
        "pct_pipeline_vs_men_vig_actual",
    ]
    contraste[diag_cols].to_csv(OUT_DIAG, index=False)

    print("[OK] Archivo contraste:", OUT_CONTRASTE)
    print("[OK] Archivo diagnóstico:", OUT_DIAG)
    print()
    print("Resumen 2019-2024 (Billones COP):")
    print(
        contraste[
            [
                "anio_proceso",
                "pagos_pipeline_B",
                "pagos_men_total_reportado_B",
                "pagos_men_filtro_ies_vig_actual_B",
                "pct_pipeline_vs_men_total",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
