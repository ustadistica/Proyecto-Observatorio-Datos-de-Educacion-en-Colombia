"""
generate_report.py — Reporte HTML profesional del PTE consolidado
===============================================================
Lee datos/processed/pte/pte_consolidado_full.parquet y genera
un reporte HTML auto-contenido con KPIs, graficos (Lorenz/Gini,
heatmap, evolucion temporal) y analisis de calidad.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import base64
from io import BytesIO

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).parent.parent
CONSOLIDADO = BASE / "datos" / "processed" / "pte" / "pte_consolidado_full.parquet"
OUT_HTML = BASE / "docs" / "reporte_pte_consolidado.html"


def fig_to_base64(fig):
    """Convierte una figura matplotlib a string base64 para HTML."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img


def calcular_gini(x):
    """Coeficiente de Gini de una serie numerica."""
    x = np.array(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) == 0 or x.sum() == 0:
        return 0.0
    x = np.sort(x)
    n = len(x)
    cumsum = np.cumsum(x)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n


def generar_reporte():
    if not CONSOLIDADO.exists():
        print(f"ERROR: No existe {CONSOLIDADO}")
        return

    df = pd.read_parquet(CONSOLIDADO)
    n_filas = len(df)
    n_cols = len(df.columns)
    anios = sorted(df["anio_proceso"].dropna().unique())
    anios_nulos = int(df["anio_proceso"].isna().sum())

    # KPIs numericos
    numeric_cols = ["apropiacioninicial", "apropiacionvigente", "compromisos",
                    "obligaciones", "pagos"]
    kpis = {}
    for col in numeric_cols:
        if col in df.columns:
            kpis[col] = pd.to_numeric(df[col], errors="coerce").sum()
        else:
            kpis[col] = 0.0

    # Cobertura por año
    cov = df.groupby("anio_proceso").size().reset_index(name="registros")
    cov["pagos"] = df.groupby("anio_proceso")["pagos"].sum().values / 1e12
    cov_html = cov.to_html(index=False, border=0, classes="table")

    # Calidad: % nulos por columna
    nulls = (df.isnull().sum() / len(df) * 100).round(2)
    nulls = nulls[nulls > 0].sort_values(ascending=False)
    nulls_df = nulls.reset_index()
    nulls_df.columns = ["columna", "%_nulos"]
    nulls_html = nulls_df.to_html(index=False, border=0, classes="table")

    # Anomalias
    pagos = pd.to_numeric(df.get("pagos", pd.Series([0])), errors="coerce")
    anom_neg = int((pagos < 0).sum())
    anom_sin_codigo = int(df["codigo_uej"].isna().sum()) if "codigo_uej" in df.columns else 0

    # ===== GRAFICO 1: Evolucion temporal de pagos =====
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    cov_plot = df.groupby("anio_proceso").agg({"pagos": "sum", "compromisos": "sum", "obligaciones": "sum"}) / 1e12
    cov_plot.plot(kind="bar", ax=ax1, color=["#1abc9c", "#3498db", "#e74c3c"])
    ax1.set_title("Evolucion Presupuestal 2015-2024 (Billones COP)")
    ax1.set_ylabel("Billones COP")
    ax1.set_xlabel("Año")
    ax1.legend(["Pagos", "Compromisos", "Obligaciones"])
    ax1.tick_params(axis='x', rotation=0)
    img1 = fig_to_base64(fig1)

    # ===== GRAFICO 2: Lorenz / Gini por Descripcion de Gasto =====
    gasto_pagos = df.groupby("descripcion")["pagos"].sum().sort_values()
    gini_val = calcular_gini(gasto_pagos.values)
    fig2, ax2 = plt.subplots(figsize=(6, 6))
    n = len(gasto_pagos)
    x = np.arange(1, n + 1) / n
    y = np.cumsum(gasto_pagos.values) / gasto_pagos.sum()
    ax2.plot([0, 1], [0, 1], 'k--', label='Igualdad perfecta')
    ax2.fill_between(x, y, alpha=0.4, color='#1abc9c')
    ax2.plot(x, y, color='#16a085', linewidth=2, label=f'Curva de Lorenz (Gini={gini_val:.3f})')
    ax2.set_title("Concentracion de Pagos por Concepto de Gasto")
    ax2.set_xlabel("Fraccion acumulada de conceptos de gasto")
    ax2.set_ylabel("Fraccion acumulada de pagos")
    ax2.legend(loc='lower right')
    img2 = fig_to_base64(fig2)

    # ===== GRAFICO 3: Heatmap correlaciones =====
    fig3, ax3 = plt.subplots(figsize=(7, 5))
    corr = df[numeric_cols].corr()
    im = ax3.imshow(corr, cmap='RdYlGn', vmin=-1, vmax=1)
    ax3.set_xticks(np.arange(len(corr.columns)))
    ax3.set_yticks(np.arange(len(corr.columns)))
    ax3.set_xticklabels(corr.columns, rotation=45, ha='right')
    ax3.set_yticklabels(corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax3.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", color="black", fontsize=9)
    ax3.set_title("Matriz de Correlacion (Variables Numericas)")
    fig3.colorbar(im, ax=ax3)
    img3 = fig_to_base64(fig3)

    # ===== GRAFICO 4: Top 10 instituciones por pagos =====
    fig4, ax4 = plt.subplots(figsize=(8, 4))
    
    # Acortar nombres largos para el grafico
    top10 = df.groupby("nombre_uej")["pagos"].sum().nlargest(10) / 1e12
    top10.index = [str(x)[:60] + '...' if len(str(x)) > 60 else str(x) for x in top10.index]
    
    top10.plot(kind='barh', ax=ax4, color='#3498db')
    ax4.set_title("Top 10 Instituciones por Pagos (Billones COP)")
    ax4.set_xlabel("Billones COP")
    img4 = fig_to_base64(fig4)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Reporte PTE Consolidado</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 2rem; background:#f4f6f8; color:#333; }}
  h1 {{ color:#2c3e50; margin-bottom:0.3rem; }}
  h2 {{ color:#34495e; border-bottom:2px solid #1abc9c; padding-bottom:0.3rem; margin-top:2rem; }}
  .section {{ background:#fff; padding:1.5rem; margin-bottom:1.5rem; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.08); }}
  .kpi-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap:1rem; }}
  .kpi {{ background: linear-gradient(135deg, #1abc9c, #16a085); color:#fff; padding:1.2rem; border-radius:8px; text-align:center; }}
  .kpi h3 {{ margin:0; font-size:2rem; font-weight:700; }}
  .kpi p {{ margin:0.3rem 0 0; font-size:0.9rem; opacity:0.95; }}
  table {{ width:100%; border-collapse:collapse; margin-top:0.5rem; }}
  th, td {{ padding:0.6rem; text-align:left; border-bottom:1px solid #ddd; }}
  th {{ background:#ecf0f1; font-weight:600; }}
  .chart {{ text-align:center; margin:1rem 0; }}
  .chart img {{ max-width:100%; border-radius:6px; box-shadow:0 2px 8px rgba(0,0,0,0.1); }}
  .highlight {{ color:#e74c3c; font-weight:600; }}
  footer {{ margin-top:3rem; font-size:0.85rem; color:#888; text-align:center; }}
</style>
</head>
<body>
  <h1>Reporte Presupuesto del Sector Educacion (PTE)</h1>
  <p><strong>Generado:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} | <strong>Fuente:</strong> Consolidado 2015-2024</p>

  <div class="section">
    <h2>KPIs Generales</h2>
    <div class="kpi-grid">
      <div class="kpi"><h3>{n_filas:,}</h3><p>Filas totales</p></div>
      <div class="kpi"><h3>{n_cols}</h3><p>Columnas</p></div>
      <div class="kpi"><h3>{len(anios)}</h3><p>Anos cubiertos</p></div>
      <div class="kpi"><h3>{kpis['pagos']/1e12:.1f}B</h3><p>Pagos (COP)</p></div>
    </div>
  </div>

  <div class="section">
    <h2>Cobertura por Ano</h2>
    {cov_html}
  </div>

  <div class="section">
    <h2>Evolucion Presupuestal</h2>
    <div class="chart"><img src="data:image/png;base64,{img1}"></div>
  </div>

  <div class="section">
    <h2>Concentracion de Recursos (Curva de Lorenz)</h2>
    <p>El coeficiente de Gini de <strong>{gini_val:.3f}</strong> indica una {'alta' if gini_val > 0.5 else 'moderada'} concentracion de los pagos en pocas entidades.</p>
    <div class="chart"><img src="data:image/png;base64,{img2}"></div>
  </div>

  <div class="section">
    <h2>Top 10 Entidades por Pagos</h2>
    <div class="chart"><img src="data:image/png;base64,{img4}"></div>
  </div>

  <div class="section">
    <h2>Matriz de Correlacion</h2>
    <div class="chart"><img src="data:image/png;base64,{img3}"></div>
  </div>

  <div class="section">
    <h2>Calidad de Datos - Nulos por Columna</h2>
    {nulls_html}
    <p>Las columnas <span class="highlight">apropiacionbloqueada, cdp, apropiaciondisponible, orden_pago</span> (92.3% nulos) no existen en la API 2019-2024. Las columnas <span class="highlight">sector, vigencia, detalle_gasto</span> (7.7% nulos) no existen en los Excel 2015-2018 manual.</p>
  </div>

  <div class="section">
    <h2>Anomalias Detectadas</h2>
    <ul>
      <li>Anos nulos: {anios_nulos}</li>
      <li>Pagos negativos: {anom_neg}</li>
      <li>Registros sin codigo UEJ: {anom_sin_codigo}</li>
    </ul>
  </div>

  <div class="section">
    <h2>Totales por Columna Numerica</h2>
    <table>
      <tr><th>Columna</th><th>Total (COP)</th></tr>
      {''.join(f'<tr><td>{k}</td><td>{v:,.0f}</td></tr>' for k,v in kpis.items())}
    </table>
  </div>

  <footer>Generado automaticamente por el pipeline de datos - Observatorio de Educacion Colombia</footer>
</body>
</html>"""

    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"OK Reporte generado: {OUT_HTML}")


if __name__ == "__main__":
    generar_reporte()
