"""
generate_report_cross_bright_metodologia.py
===========================================

Genera un reporte HTML separado con la metodología Cross-Bright del proyecto PTE,
incluyendo:

1) Mapeo de variantes de columnas (header_utils.py)
2) Mapeo manual de variantes de entidades (mapear_entidades_pte.py)
3) Procesos clave de la canalización basada en run_full_pipeline.py
4) Controles de normalización, agregación y deduplicación lógica
5) Evidencia de contraste MEN vs pipeline 2019-2024
6) Recomendaciones para conseguir datos desagregados y narrativa normativa
"""

from __future__ import annotations

from pathlib import Path
import sys
from datetime import datetime
from io import BytesIO
import base64
import warnings

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=UserWarning)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE = PROJECT_ROOT
CONSOLIDADO_PATH = BASE / "datos" / "processed" / "pte" / "pte_consolidado_full.parquet"
CONTRASTE_PATH = BASE / "datos" / "processed" / "pte" / "contraste_men_vs_fuentes_2019_2024.csv"
OUTPUT_HTML = BASE / "docs" / "reporte_metodologia_cross_bright.html"


def fig_to_b64(fig: plt.Figure) -> str:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def fmt_b(value: float | int | None) -> str:
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return "N/A"
        return f"{float(value):,.2f}"
    except Exception:
        return "N/A"


def build_contrast_chart(contraste: pd.DataFrame | None) -> str | None:
    if contraste is None or contraste.empty:
        return None

    use = contraste.copy()
    use["anio_proceso"] = pd.to_numeric(use.get("anio_proceso"), errors="coerce")
    use = use.dropna(subset=["anio_proceso"]).sort_values("anio_proceso")

    for col in [
        "pagos_pipeline_B",
        "pagos_men_total_reportado_B",
        "pagos_men_filtro_ies_vig_actual_B",
    ]:
        if col in use.columns:
            use[col] = pd.to_numeric(use[col], errors="coerce")
        else:
            use[col] = np.nan

    fig, ax = plt.subplots(figsize=(11, 4.8), facecolor="#0f172a")
    ax.set_facecolor("#111827")

    ax.plot(
        use["anio_proceso"],
        use["pagos_pipeline_B"],
        "o-",
        color="#22c55e",
        linewidth=2.6,
        markersize=7,
        label="Pipeline (universo IES trazable)",
    )
    ax.plot(
        use["anio_proceso"],
        use["pagos_men_total_reportado_B"],
        "s--",
        color="#ef4444",
        linewidth=2.4,
        markersize=7,
        label="MEN/API total reportado",
    )

    if (use["pagos_men_filtro_ies_vig_actual_B"].fillna(0) > 0).any():
        ax.plot(
            use["anio_proceso"],
            use["pagos_men_filtro_ies_vig_actual_B"],
            "^:",
            color="#eab308",
            linewidth=2.2,
            markersize=7,
            label="MEN filtro textual IES (vigencia actual)",
        )

    ax.set_title(
        "Contraste de cobertura 2019-2024 (Billones COP)",
        color="white",
        fontsize=12,
        pad=10,
    )
    ax.set_xlabel("Año", color="#d1d5db")
    ax.set_ylabel("Billones COP", color="#d1d5db")
    ax.tick_params(colors="#d1d5db")
    ax.grid(axis="y", color="#374151", linewidth=0.6)
    ax.legend(facecolor="#111827", labelcolor="white", framealpha=0.7, fontsize=8.5)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    for sp in ["bottom", "left"]:
        ax.spines[sp].set_color("#4b5563")

    return fig_to_b64(fig)


def build_fuentes_chart(consolidado: pd.DataFrame | None) -> str | None:
    if consolidado is None or consolidado.empty:
        return None
    required = {"anio_proceso", "fuente_ingesta", "pagos"}
    if not required.issubset(set(consolidado.columns)):
        return None

    df = consolidado.copy()
    df["anio_proceso"] = pd.to_numeric(df["anio_proceso"], errors="coerce")
    df["pagos"] = pd.to_numeric(df["pagos"], errors="coerce")
    df = df.dropna(subset=["anio_proceso", "pagos", "fuente_ingesta"])

    agg = (
        df.groupby(["anio_proceso", "fuente_ingesta"], as_index=False)["pagos"].sum()
        .pivot(index="anio_proceso", columns="fuente_ingesta", values="pagos")
        .fillna(0)
        / 1e12
    )
    agg = agg.sort_index()
    if agg.empty:
        return None

    palette = {
        "men_excel": "#22c55e",
        "interpolado_2018_2020": "#f59e0b",
        "dnp_cuadro7": "#3b82f6",
        "siif_uej": "#a855f7",
        "desconocida": "#9ca3af",
    }

    fig, ax = plt.subplots(figsize=(11, 4.8), facecolor="#0f172a")
    ax.set_facecolor("#111827")
    bottoms = np.zeros(len(agg.index))
    years = agg.index.astype(int).tolist()

    ordered_cols = [
        "men_excel",
        "interpolado_2018_2020",
        "dnp_cuadro7",
        "siif_uej",
        "desconocida",
    ]
    for c in ordered_cols:
        if c not in agg.columns:
            continue
        vals = agg[c].values
        ax.bar(years, vals, bottom=bottoms, color=palette.get(c, "#9ca3af"), label=c, alpha=0.92)
        bottoms += vals

    ax.set_title("Pagos por fuente en el consolidado final", color="white", fontsize=12, pad=10)
    ax.set_xlabel("Año", color="#d1d5db")
    ax.set_ylabel("Billones COP", color="#d1d5db")
    ax.tick_params(colors="#d1d5db")
    ax.grid(axis="y", color="#374151", linewidth=0.6)
    ax.legend(facecolor="#111827", labelcolor="white", framealpha=0.7, fontsize=8.5)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    for sp in ["bottom", "left"]:
        ax.spines[sp].set_color("#4b5563")

    return fig_to_b64(fig)


def build_cross_bright_map_table() -> tuple[pd.DataFrame, int, int]:
    from src.ingesta import header_utils

    raw_map = getattr(header_utils, "_CROSS_BRIGHT_MAP", {})
    if not isinstance(raw_map, dict) or not raw_map:
        return pd.DataFrame(columns=["columna_canonica", "n_variantes", "ejemplos_variantes"]), 0, 0

    grouped: dict[str, list[str]] = {}
    for variant, canon in raw_map.items():
        grouped.setdefault(str(canon), []).append(str(variant))

    rows = []
    for canon, variants in grouped.items():
        vs = sorted(set(variants))
        sample = ", ".join(vs[:8])
        if len(vs) > 8:
            sample += ", ..."
        rows.append(
            {
                "columna_canonica": canon,
                "n_variantes": len(vs),
                "ejemplos_variantes": sample,
            }
        )

    table = pd.DataFrame(rows).sort_values(["n_variantes", "columna_canonica"], ascending=[False, True])
    return table, len(raw_map), len(grouped)


def build_entidades_map_table() -> tuple[pd.DataFrame, int, int, int]:
    from src.transformacion.mapear_entidades_pte import MAPA_ENTIDADES

    rows = []
    sin_codigo = 0
    for dirty, target in MAPA_ENTIDADES.items():
        clean_name, code = target
        if str(code) == "0":
            sin_codigo += 1
        rows.append(
            {
                "variante_detectada": dirty,
                "nombre_normalizado": clean_name,
                "codigo_ies": code,
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["mismo_nombre"] = (df["variante_detectada"] == df["nombre_normalizado"]).astype(int)
        df = df.sort_values(["mismo_nombre", "variante_detectada"], ascending=[True, True]).drop(columns=["mismo_nombre"])

    total = len(rows)
    con_codigo = total - sin_codigo
    return df, total, con_codigo, sin_codigo


def build_process_table() -> pd.DataFrame:
    rows = [
        {
            "proceso": "1) Limpieza previa y arranque de ingesta",
            "archivo": "run_full_pipeline.py",
            "detalle": "Elimina parquets antiguos en datos/raw/pte y ejecuta ingestar_excels_men(2015-2024).",
            "salida": "Parquets anuales pte_manual_<año>.parquet por fuente.",
        },
        {
            "proceso": "2) Normalización Cross-Bright de headers",
            "archivo": "src/ingesta/header_utils.py",
            "detalle": "Slugify + diccionario canónico para convertir variantes históricas al mismo nombre de columna.",
            "salida": "Estructura compatible entre MEN Excel, DNP Cuadro 7 y SIIF UEJ.",
        },
        {
            "proceso": "3) Reparación encoding y estandarización SIIF antiguo",
            "archivo": "src/ingesta/pte.py",
            "detalle": "Corrige mojibake latin1→UTF-8, detecta header real, crea niveles modernos y agrega meses por año.",
            "salida": "Datos anuales limpios y agregados; menor riesgo de duplicidad por cortes mensuales.",
        },
        {
            "proceso": "4) Ingesta DNP/SIIF + interpolación 2019",
            "archivo": "src/ingesta/pte.py",
            "detalle": "Lee Cuadro 7 (2020-2022), SIIF UEJ (2023-2024), filtra universidades e interpola 2019 entre 2018 y 2020.",
            "salida": "Serie 2019-2024 armonizada con fuente_ingesta explícita.",
        },
        {
            "proceso": "5) Consolidación final y control de universo",
            "archivo": "src/transformacion/consolidar_pte.py",
            "detalle": "Concatena parquets, tipifica numéricos, filtra MEN gestión general vs universidades en nuevas fuentes.",
            "salida": "pte_consolidado_full.parquet listo para reportes y cruces.",
        },
    ]
    return pd.DataFrame(rows)


def html_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    use = df.copy()
    if max_rows is not None:
        use = use.head(max_rows)
    return use.to_html(index=False, escape=True, border=0, classes="table")


def main() -> None:
    consolidado = None
    if CONSOLIDADO_PATH.exists():
        consolidado = pd.read_parquet(CONSOLIDADO_PATH)

    contraste = None
    if CONTRASTE_PATH.exists():
        contraste = pd.read_csv(CONTRASTE_PATH)

    map_table, n_variantes, n_canonicas = build_cross_bright_map_table()
    ent_table, n_ent_map, n_ent_con_codigo, n_ent_sin_codigo = build_entidades_map_table()
    process_table = build_process_table()

    total_rows = int(len(consolidado)) if consolidado is not None else 0
    total_entidades = int(consolidado["nombre_uej"].nunique()) if consolidado is not None and "nombre_uej" in consolidado.columns else 0
    total_fuentes = int(consolidado["fuente_ingesta"].nunique()) if consolidado is not None and "fuente_ingesta" in consolidado.columns else 0
    anios = []
    if consolidado is not None and "anio_proceso" in consolidado.columns:
        anios = sorted(
            pd.to_numeric(consolidado["anio_proceso"], errors="coerce").dropna().astype(int).unique().tolist()
        )

    cobertura_total_pct = np.nan
    pipeline_total_b = np.nan
    men_total_b = np.nan
    if contraste is not None and not contraste.empty:
        for col in ["pagos_pipeline_B", "pagos_men_total_reportado_B"]:
            contraste[col] = pd.to_numeric(contraste.get(col), errors="coerce")
        pipeline_total_b = float(contraste["pagos_pipeline_B"].sum())
        men_total_b = float(contraste["pagos_men_total_reportado_B"].sum())
        cobertura_total_pct = (pipeline_total_b / men_total_b * 100.0) if men_total_b else np.nan

    contrast_chart = build_contrast_chart(contraste)
    fuentes_chart = build_fuentes_chart(consolidado)

    contraste_tabla_html = ""
    if contraste is not None and not contraste.empty:
        show_cols = [
            "anio_proceso",
            "pagos_pipeline_B",
            "pagos_men_total_reportado_B",
            "pagos_men_filtro_ies_vig_actual_B",
            "pct_pipeline_vs_men_total",
            "men_rows_total",
            "men_rows_filtro_ies",
        ]
        show_cols = [c for c in show_cols if c in contraste.columns]
        if show_cols:
            tab = contraste[show_cols].copy()
            tab = tab.rename(
                columns={
                    "anio_proceso": "Año",
                    "pagos_pipeline_B": "Pipeline IES (B COP)",
                    "pagos_men_total_reportado_B": "MEN total reportado (B COP)",
                    "pagos_men_filtro_ies_vig_actual_B": "MEN filtro IES vig.actual (B COP)",
                    "pct_pipeline_vs_men_total": "Pipeline/MEN total (%)",
                    "men_rows_total": "Filas MEN/API",
                    "men_rows_filtro_ies": "Filas filtro IES",
                }
            )
            contraste_tabla_html = html_table(tab)

    # KPIs formateados
    anio_ini = anios[0] if anios else "N/A"
    anio_fin = anios[-1] if anios else "N/A"
    cov_txt = f"{cobertura_total_pct:,.2f}%" if not np.isnan(cobertura_total_pct) else "N/A"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Reporte Metodológico Cross-Bright — PTE</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; background: #0b1020; color: #dbe4ff; line-height: 1.5; }}
    .container {{ max-width: 1250px; margin: 0 auto; padding: 26px 18px 34px; }}
    .hero {{
      background: linear-gradient(135deg, #111827 0%, #1f2937 55%, #312e81 100%);
      border: 1px solid #334155;
      border-radius: 14px;
      padding: 26px;
      margin-bottom: 18px;
    }}
    .hero h1 {{ font-size: 1.85rem; color: white; margin-bottom: 10px; }}
    .hero p {{ color: #c7d2fe; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 11px; margin: 16px 0 22px; }}
    .kpi {{ background: #111827; border: 1px solid #334155; border-radius: 11px; padding: 14px; }}
    .kpi .val {{ font-size: 1.45rem; font-weight: 700; color: #60a5fa; }}
    .kpi .lbl {{ font-size: .82rem; color: #94a3b8; }}
    section {{ background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 18px; margin-bottom: 14px; }}
    section h2 {{ color: #f8fafc; font-size: 1.18rem; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
    section h3 {{ color: #c7d2fe; font-size: 1.02rem; margin: 14px 0 8px; }}
    .note {{ background: rgba(234,179,8,.10); border-left: 4px solid #eab308; color: #fef3c7; padding: 10px 12px; border-radius: 0 8px 8px 0; margin: 8px 0 12px; font-size: .94rem; }}
    .warn {{ background: rgba(239,68,68,.12); border-left: 4px solid #ef4444; color: #fecaca; padding: 10px 12px; border-radius: 0 8px 8px 0; margin: 8px 0 12px; font-size: .94rem; }}
    .ok {{ background: rgba(34,197,94,.10); border-left: 4px solid #22c55e; color: #dcfce7; padding: 10px 12px; border-radius: 0 8px 8px 0; margin: 8px 0 12px; font-size: .94rem; }}
    .chart {{ text-align: center; margin-top: 8px; }}
    .chart img {{ max-width: 100%; border-radius: 10px; border: 1px solid #334155; }}
    .table {{ width: 100%; border-collapse: collapse; font-size: .88rem; margin-top: 8px; }}
    .table th {{ background: #1e293b; color: #f8fafc; text-align: left; padding: 8px 10px; border-bottom: 1px solid #334155; }}
    .table td {{ padding: 8px 10px; border-bottom: 1px solid #273449; color: #dbe4ff; vertical-align: top; }}
    .table tr:hover td {{ background: #131f35; }}
    ul {{ margin-left: 18px; }}
    li {{ margin-bottom: 5px; }}
    code {{ background: #111827; padding: 1px 5px; border-radius: 5px; border: 1px solid #334155; color: #93c5fd; }}
    footer {{ text-align: center; color: #94a3b8; margin-top: 16px; font-size: .84rem; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="hero">
      <h1>Reporte Metodológico Cross-Bright (PTE 2015-2024)</h1>
      <p>
        Documento técnico separado para presentar el método de cruce, normalización de variantes,
        controles de deduplicación lógica, y contraste entre universo MEN total vs universo IES trazable.
      </p>
      <p style="font-size:.9rem;margin-top:7px;color:#a5b4fc;">
        Generado automáticamente: {datetime.now().strftime('%Y-%m-%d %H:%M')}
      </p>
    </div>

    <div class="grid">
      <div class="kpi"><div class="val">{anio_ini}–{anio_fin}</div><div class="lbl">Cobertura temporal consolidada</div></div>
      <div class="kpi"><div class="val">{total_rows:,}</div><div class="lbl">Filas en pte_consolidado_full</div></div>
      <div class="kpi"><div class="val">{total_entidades}</div><div class="lbl">Entidades únicas (nombre_uej)</div></div>
      <div class="kpi"><div class="val">{total_fuentes}</div><div class="lbl">Fuentes en consolidado</div></div>
      <div class="kpi"><div class="val">{n_variantes}</div><div class="lbl">Variantes de headers mapeadas</div></div>
      <div class="kpi"><div class="val">{n_canonicas}</div><div class="lbl">Columnas canónicas Cross-Bright</div></div>
      <div class="kpi"><div class="val">{n_ent_map}</div><div class="lbl">Variantes de entidades en MAPA_ENTIDADES</div></div>
      <div class="kpi"><div class="val">{cov_txt}</div><div class="lbl">Cobertura pipeline vs MEN total (2019-2024)</div></div>
    </div>

    <section>
      <h2>1) Procesos clave identificados desde <code>run_full_pipeline.py</code> y archivos referenciados</h2>
      <div class="ok">
        Se documentan 5 procesos operativos (ingesta, armonización, agregación, consolidación y control de universo)
        rastreables en archivos del pipeline principal.
      </div>
      {html_table(process_table)}
    </section>

    <section>
      <h2>2) Mapeo de variantes de columnas (Cross-Bright headers)</h2>
      <p>
        El diccionario de <code>src/ingesta/header_utils.py</code> permite alinear múltiples etiquetas históricas
        de columnas hacia un conjunto canónico estable. Esto evita quiebres por cambios de nomenclatura entre
        MEN Excel, DNP Cuadro 7 y SIIF por UEJ.
      </p>
      {html_table(map_table, max_rows=18)}
    </section>

    <section>
      <h2>3) Variantes de entidades y normalización nominal</h2>
      <p>
        El mapeo manual de <code>src/transformacion/mapear_entidades_pte.py</code> corrige entidades con variantes,
        errores de codificación y diferencias de escritura para sostener cruces con SNIES/ICFES.
      </p>
      <div class="note">
        Con código IES explícito: <strong>{n_ent_con_codigo}</strong> &nbsp;|&nbsp;
        Sin código (ministerio/u otras no IES): <strong>{n_ent_sin_codigo}</strong>
      </div>
      {html_table(ent_table, max_rows=20)}
    </section>

    <section>
      <h2>4) Controles de deduplicación lógica, consistencia y trazabilidad</h2>
      <ul>
        <li><strong>Agregación anual de 2015-2018:</strong> en <code>ingestar_excels_men()</code>, los cortes mensuales se agrupan por llaves categóricas y se suman métricas numéricas.</li>
        <li><strong>Normalización de encoding:</strong> <code>reparar_encoding_df()</code> corrige mojibake latin-1→UTF-8 antes de persistir en parquet.</li>
        <li><strong>Alineación semántica:</strong> <code>normalise_header()</code> reduce ruido de nombres y evita columnas duplicadas por variantes ortográficas/históricas.</li>
        <li><strong>Filtrado de universo:</strong> <code>consolidar_pte.py</code> separa explícitamente MEN gestión general (2015-2018) y universidades en fuentes DNP/SIIF/interpolado.</li>
        <li><strong>Trazabilidad por fuente:</strong> la columna <code>fuente_ingesta</code> se conserva para auditar cada segmento temporal y sus limitaciones.</li>
      </ul>
      <div class="warn">
        Importante: “deduplicación” aquí no significa solo borrar filas idénticas; también implica
        <strong>compactar cortes mensuales</strong>, controlar llaves de agregación y evitar doble conteo entre universos heterogéneos.
      </div>
    </section>

    <section>
      <h2>5) Evidencia de contraste MEN total vs serie IES trazable (2019-2024)</h2>
      <div class="warn">
        El contraste compara dos universos diferentes: (a) total MEN/API reportado (incluye rubros agregados)
        y (b) transferencias IES identificables en pipeline. La brecha no prueba error técnico; prueba diferencia
        de granularidad de publicación.
      </div>
      <p>
        Totales 2019-2024: Pipeline IES = <strong>{fmt_b(pipeline_total_b)} B</strong> vs MEN reportado total =
        <strong>{fmt_b(men_total_b)} B</strong>.
      </p>
      {('<div class="chart"><img src="data:image/png;base64,' + contrast_chart + '"/></div>') if contrast_chart else '<p>No hay gráfico de contraste disponible.</p>'}
      {contraste_tabla_html if contraste_tabla_html else '<p>No hay tabla de contraste disponible.</p>'}
    </section>

    <section>
      <h2>6) Distribución por fuentes en el consolidado final</h2>
      {('<div class="chart"><img src="data:image/png;base64,' + fuentes_chart + '"/></div>') if fuentes_chart else '<p>No hay gráfico de fuentes disponible.</p>'}
    </section>

    <section>
      <h2>7) Recomendaciones para obtener datos desagregados y sostener narrativa legal/institucional</h2>

      <h3>7.1 Recomendaciones de gestión de datos (accionables)</h3>
      <ul>
        <li>Solicitar a MEN/MHCP (derecho de petición) el <strong>detalle por IES</strong> para rubros Ley 30 (art. 86/87), separado por vigencia actual, reservas y cuentas por pagar.</li>
        <li>Pedir explícitamente <strong>diccionario de datos + histórico de cambios de estructura</strong> desde 2018 a la fecha.</li>
        <li>Exigir publicación abierta con <strong>ID único de entidad, rubro, vigencia y periodo</strong> para evitar ambigüedad textual.</li>
        <li>Solicitar metadatos de conciliación entre reportes agregados y desagregados para reconstruir trazabilidad completa 2019-2024.</li>
        <li>Incluir un anexo de “campos eliminados/agregados por año” como estándar de transparencia institucional.</li>
      </ul>

      <h3>7.2 Guion recomendado para explicar “qué cambió”</h3>
      <div class="note">
        Con la evidencia del pipeline no se demuestra directamente un cambio de Ley 30, sino un
        <strong>cambio de granularidad/formato de publicación y clasificación presupuestal</strong> a partir de 2019.
      </div>
      <ul>
        <li>Mensaje sugerido: “La regla de transferencias puede seguir vigente, pero el dato abierto dejó de venir con el mismo desglose por universidad”.</li>
        <li>Diferenciar claramente: <strong>cambio normativo</strong> vs <strong>cambio operativo de reporte</strong>.</li>
        <li>Para afirmar una “ley cambiada”, soportar con acto oficial (ley/decreto/resolución/circular) que modifique la forma de reporte o asignación.</li>
        <li>Mientras ese acto no esté anexado, comunicar la ruptura como <strong>brecha de transparencia de datos</strong>, no como error del modelo.</li>
      </ul>
    </section>

    <footer>
      Reporte metodológico Cross-Bright — Observatorio de Datos de Educación en Colombia
    </footer>
  </div>
</body>
</html>
"""

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"[OK] Reporte metodológico generado: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
