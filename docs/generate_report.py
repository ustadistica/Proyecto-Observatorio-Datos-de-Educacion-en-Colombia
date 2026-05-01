"""
generate_report.py — Reporte HTML del PTE Consolidado (2015-2024)
=================================================================
Lee pte_consolidado_full.parquet y genera un reporte auto-contenido
con KPIs, gráficos de evolución, Lorenz/Gini, heatmap y cobertura
claramente diferenciando las 4 fuentes del pipeline.
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
import matplotlib.patches as mpatches

BASE        = Path(__file__).parent.parent
CONSOLIDADO = BASE / "datos" / "processed" / "pte" / "pte_consolidado_full.parquet"
SERIE_CSV   = BASE / "datos" / "processed" / "serie_nacional_eficiencia.csv"
CONTRASTE_CSV = BASE / "datos" / "processed" / "pte" / "contraste_men_vs_fuentes_2019_2024.csv"
OUT_HTML    = BASE / "docs" / "reporte_pte_consolidado.html"

PALETTE = {
    'men_excel':              '#2ecc71',
    'interpolado_2018_2020':  '#f39c12',
    'dnp_cuadro7':            '#3498db',
    'siif_uej':               '#9b59b6',
    'desconocida':            '#95a5a6',
}
LABEL = {
    'men_excel':              'MEN Excel (2015-2018)',
    'interpolado_2018_2020':  'Interpolado 2019',
    'dnp_cuadro7':            'DNP Cuadro 7 (2020-2022)',
    'siif_uej':               'SIIF por UEJ (2023-2024)',
    'desconocida':            'Desconocida',
}

def fig_to_b64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight')
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img

def calcular_gini(x):
    x = np.array(x, dtype=float)
    x = x[~np.isnan(x) & (x > 0)]
    if len(x) == 0: return 0.0
    x = np.sort(x)
    n = len(x)
    return (n + 1 - 2 * np.sum(np.cumsum(x)) / x.sum()) / n

def generar_reporte():
    if not CONSOLIDADO.exists():
        print("ERROR: No existe " + str(CONSOLIDADO)); return

    df = pd.read_parquet(CONSOLIDADO)
    df['pagos']            = pd.to_numeric(df['pagos'],            errors='coerce')
    df['compromisos']      = pd.to_numeric(df['compromisos'],      errors='coerce')
    df['obligaciones']     = pd.to_numeric(df['obligaciones'],     errors='coerce')
    df['apropiacionvigente'] = pd.to_numeric(df['apropiacionvigente'], errors='coerce')
    df['anio_proceso']     = pd.to_numeric(df['anio_proceso'],     errors='coerce')

    anios    = sorted(df['anio_proceso'].dropna().unique().astype(int).tolist())
    fuentes  = df['fuente_ingesta'].value_counts().to_dict() if 'fuente_ingesta' in df.columns else {}
    total_pagos_b = df['pagos'].sum() / 1e12

    contraste = None
    if CONTRASTE_CSV.exists():
        try:
            contraste = pd.read_csv(CONTRASTE_CSV)
            if 'anio_proceso' in contraste.columns:
                contraste['anio_proceso'] = pd.to_numeric(contraste['anio_proceso'], errors='coerce')
                contraste = contraste.dropna(subset=['anio_proceso'])
                contraste['anio_proceso'] = contraste['anio_proceso'].astype(int)
                contraste = contraste.sort_values('anio_proceso')
        except Exception:
            contraste = None

    # ── GRAFICO 1: Pagos por año por fuente (barras apiladas) ────────────────
    fig1, ax1 = plt.subplots(figsize=(11, 5), facecolor='#1a1a2e')
    ax1.set_facecolor('#16213e')

    yr_fuente = df.groupby(['anio_proceso', 'fuente_ingesta'])['pagos'].sum().unstack(fill_value=0) / 1e12
    years_sorted = sorted(yr_fuente.index.astype(int).tolist())
    yr_fuente.index = yr_fuente.index.astype(int)

    bottom = np.zeros(len(years_sorted))
    for fuente in ['men_excel', 'interpolado_2018_2020', 'dnp_cuadro7', 'siif_uej', 'desconocida']:
        if fuente not in yr_fuente.columns: continue
        vals = [yr_fuente.loc[y, fuente] if y in yr_fuente.index else 0 for y in years_sorted]
        bars = ax1.bar(years_sorted, vals, bottom=bottom, color=PALETTE.get(fuente, '#888'),
                       label=LABEL.get(fuente, fuente), alpha=0.92, width=0.7)
        # Anotar valor si es significativo
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 0.5:
                ax1.text(years_sorted[i], b + v/2, f'{v:.1f}B', ha='center', va='center',
                         fontsize=7.5, color='white', fontweight='bold')
        bottom += np.array(vals)

    ax1.set_title('Pagos por Universidad/IES 2015-2024 — Por Fuente de Datos (Billones COP)',
                  color='white', fontsize=12, pad=12)
    ax1.set_xlabel('Año', color='#aaa'); ax1.set_ylabel('Billones COP', color='#aaa')
    ax1.tick_params(colors='#ccc'); ax1.set_xticks(years_sorted)
    ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
    for sp in ['bottom','left']: ax1.spines[sp].set_color('#444')
    ax1.yaxis.grid(True, color='#333', linewidth=0.5)
    ax1.legend(loc='upper left', fontsize=8.5, facecolor='#16213e', labelcolor='white', framealpha=0.7)
    img1 = fig_to_b64(fig1)

    # ── GRAFICO 2: Serie nacional de eficiencia (si existe) ──────────────────
    img2 = None
    if SERIE_CSV.exists():
        serie = pd.read_csv(SERIE_CSV)
        serie['anio_proceso'] = pd.to_numeric(serie['anio_proceso'], errors='coerce')
        serie['costo_nacional_millones'] = pd.to_numeric(serie['costo_nacional_millones'], errors='coerce')
        serie = serie.dropna(subset=['anio_proceso','costo_nacional_millones'])
        serie = serie.sort_values('anio_proceso')

        fig2, ax2 = plt.subplots(figsize=(11, 4.5), facecolor='#1a1a2e')
        ax2.set_facecolor('#16213e')

        desg = serie[serie['tipo_dato'] == 'desglosado_por_ies']
        agr  = serie[serie['tipo_dato'] != 'desglosado_por_ies']

        if not desg.empty:
            ax2.plot(desg['anio_proceso'], desg['costo_nacional_millones'],
                     'o-', color='#2ecc71', linewidth=2.5, markersize=8, label='Desglose por IES (MEN)')
        if not agr.empty:
            ax2.plot(agr['anio_proceso'], agr['costo_nacional_millones'],
                     's--', color='#e67e22', linewidth=2.5, markersize=8, label='Dato Agregado/Directo (SIIF/DNP)')

        for _, r in serie.iterrows():
            ax2.annotate(f"${r['costo_nacional_millones']:.1f}M",
                         (r['anio_proceso'], r['costo_nacional_millones']),
                         textcoords='offset points', xytext=(0, 10),
                         ha='center', fontsize=8, color='#ddd')

        ax2.axvline(x=2018.5, color='#e74c3c', linestyle=':', linewidth=1.5, alpha=0.8)
        ax2.text(2018.6, ax2.get_ylim()[1]*0.95 if ax2.get_ylim()[1] > 0 else 10,
                 'Cambio\nde fuente', color='#e74c3c', fontsize=8)

        ax2.set_title('Costo por Graduado — Serie Nacional 2015-2024 (Millones COP)',
                      color='white', fontsize=12, pad=12)
        ax2.set_xlabel('Año', color='#aaa'); ax2.set_ylabel('Millones COP / graduado', color='#aaa')
        ax2.tick_params(colors='#ccc'); ax2.set_xticks(sorted(serie['anio_proceso'].astype(int).tolist()))
        for sp in ['top','right']: ax2.spines[sp].set_visible(False)
        for sp in ['bottom','left']: ax2.spines[sp].set_color('#444')
        ax2.yaxis.grid(True, color='#333', linewidth=0.5)
        ax2.legend(fontsize=9, facecolor='#16213e', labelcolor='white', framealpha=0.7)
        img2 = fig_to_b64(fig2)

    # ── GRAFICO 3: Lorenz / Gini ──────────────────────────────────────────────
    gasto = df[df['pagos'] > 0].groupby('nombre_uej')['pagos'].sum().sort_values()
    gini_val = calcular_gini(gasto.values)
    fig3, ax3 = plt.subplots(figsize=(6, 6), facecolor='#1a1a2e')
    ax3.set_facecolor('#16213e')
    n = len(gasto)
    x = np.arange(1, n+1)/n
    y = np.cumsum(gasto.values)/gasto.sum()
    ax3.plot([0,1],[0,1],'w--', alpha=0.5, label='Igualdad perfecta')
    ax3.fill_between(x, y, alpha=0.35, color='#9b59b6')
    ax3.plot(x, y, color='#9b59b6', linewidth=2.5, label=f'Lorenz (Gini={gini_val:.3f})')
    ax3.set_title('Concentración de Pagos por Entidad', color='white', fontsize=12)
    ax3.set_xlabel('Fracción acumulada de entidades', color='#aaa')
    ax3.set_ylabel('Fracción acumulada de pagos', color='#aaa')
    ax3.tick_params(colors='#ccc')
    for sp in ['top','right']: ax3.spines[sp].set_visible(False)
    for sp in ['bottom','left']: ax3.spines[sp].set_color('#444')
    ax3.legend(fontsize=9, facecolor='#16213e', labelcolor='white', framealpha=0.7)
    img3 = fig_to_b64(fig3)

    # ── GRAFICO 4: Top 15 universidades por pagos totales ────────────────────
    top_uni = df[df['nombre_uej'].str.contains('UNIVERSIDAD', na=False, case=False)] \
                .groupby('nombre_uej')['pagos'].sum().nlargest(15) / 1e12
    top_uni.index = [str(x)[:45]+'…' if len(str(x))>45 else str(x) for x in top_uni.index]
    fig4, ax4 = plt.subplots(figsize=(10, 6), facecolor='#1a1a2e')
    ax4.set_facecolor('#16213e')
    colors = ['#9b59b6' if i < 3 else '#3498db' if i < 7 else '#2ecc71' for i in range(len(top_uni))]
    bars = ax4.barh(range(len(top_uni)), top_uni.values, color=colors, alpha=0.9)
    ax4.set_yticks(range(len(top_uni)))
    ax4.set_yticklabels(top_uni.index, color='#ccc', fontsize=9)
    ax4.set_xlabel('Billones COP (Total 2015-2024)', color='#aaa')
    ax4.set_title('Top 15 Universidades por Pagos Totales (2015-2024)', color='white', fontsize=12, pad=12)
    for i, (bar, v) in enumerate(zip(bars, top_uni.values)):
        ax4.text(v + 0.01, bar.get_y() + bar.get_height()/2,
                 f'{v:.2f}B', va='center', color='white', fontsize=8)
    ax4.tick_params(colors='#ccc')
    for sp in ['top','right']: ax4.spines[sp].set_visible(False)
    for sp in ['bottom','left']: ax4.spines[sp].set_color('#444')
    ax4.xaxis.grid(True, color='#333', linewidth=0.5)
    img4 = fig_to_b64(fig4)

    # ── GRAFICO 5: Contraste MEN reportado vs serie actual (2019-2024) ─────────
    img5 = None
    contraste_table = ''
    if contraste is not None and not contraste.empty:
        for c in [
            'pagos_pipeline_B',
            'pagos_men_total_reportado_B',
            'pagos_men_filtro_ies_vig_actual_B',
            'pct_pipeline_vs_men_total',
            'men_rows_total',
            'men_rows_filtro_ies',
        ]:
            if c in contraste.columns:
                contraste[c] = pd.to_numeric(contraste[c], errors='coerce')

        fig5, ax5 = plt.subplots(figsize=(11, 5), facecolor='#1a1a2e')
        ax5.set_facecolor('#16213e')

        x = contraste['anio_proceso']
        y_pipe = contraste.get('pagos_pipeline_B', pd.Series(index=contraste.index, dtype=float)).fillna(0)
        y_men_total = contraste.get('pagos_men_total_reportado_B', pd.Series(index=contraste.index, dtype=float)).fillna(0)
        y_men_ies = contraste.get('pagos_men_filtro_ies_vig_actual_B', pd.Series(index=contraste.index, dtype=float)).fillna(0)

        ax5.plot(x, y_pipe, 'o-', color='#2ecc71', linewidth=2.5, markersize=7,
                 label='Serie actual pipeline (DNP/SIIF/interpolado, universo parcial)')
        ax5.plot(x, y_men_total, 's--', color='#e74c3c', linewidth=2.5, markersize=7,
                 label='MEN/API reportado total (sin desglose por IES)')

        if (y_men_ies > 0).any():
            ax5.plot(x, y_men_ies, '^:', color='#f1c40f', linewidth=2.2, markersize=7,
                     label='MEN filtro texto IES (vigencia actual)')

        for xi, yi in zip(x, y_pipe):
            ax5.annotate(f'{yi:.2f}B', (xi, yi), textcoords='offset points', xytext=(0, 8),
                         ha='center', fontsize=7.5, color='#9be7b2')
        for xi, yi in zip(x, y_men_total):
            ax5.annotate(f'{yi:.0f}B', (xi, yi), textcoords='offset points', xytext=(0, -13),
                         ha='center', fontsize=7, color='#ffb3ab')

        ax5.set_title('Contraste 2019–2024: MEN reportado total vs transferencias IES del pipeline (Billones COP)',
                      color='white', fontsize=12, pad=12)
        ax5.set_xlabel('Año', color='#aaa')
        ax5.set_ylabel('Billones COP', color='#aaa')
        ax5.set_xticks(sorted(x.unique().tolist()))
        ax5.tick_params(colors='#ccc')
        for sp in ['top', 'right']:
            ax5.spines[sp].set_visible(False)
        for sp in ['bottom', 'left']:
            ax5.spines[sp].set_color('#444')
        ax5.yaxis.grid(True, color='#333', linewidth=0.5)
        ax5.legend(fontsize=8.5, facecolor='#16213e', labelcolor='white', framealpha=0.7, loc='upper left')
        img5 = fig_to_b64(fig5)

        show_cols = [
            'anio_proceso',
            'pagos_pipeline_B',
            'pagos_men_total_reportado_B',
            'pagos_men_filtro_ies_vig_actual_B',
            'pct_pipeline_vs_men_total',
            'men_rows_total',
            'men_rows_filtro_ies',
        ]
        show_cols = [c for c in show_cols if c in contraste.columns]
        if show_cols:
            tab = contraste[show_cols].copy()
            tab = tab.rename(columns={
                'anio_proceso': 'Año',
                'pagos_pipeline_B': 'Pipeline IES (B COP)',
                'pagos_men_total_reportado_B': 'MEN reportado total (B COP)',
                'pagos_men_filtro_ies_vig_actual_B': 'MEN filtro IES vigencia actual (B COP)',
                'pct_pipeline_vs_men_total': 'Pipeline / MEN total (%)',
                'men_rows_total': 'Filas MEN/API',
                'men_rows_filtro_ies': 'Filas filtro IES',
            })
            contraste_table = tab.to_html(index=False, border=0, classes='table',
                                          float_format=lambda v: f'{v:,.2f}')

    # ── Tabla de cobertura por año ────────────────────────────────────────────
    cov = df.groupby('anio_proceso').agg(
        registros=('pagos','count'),
        universidades=('nombre_uej','nunique'),
        pagos_B=('pagos', lambda x: round(x.sum()/1e12, 2))
    ).reset_index()
    cov['fuente'] = cov['anio_proceso'].apply(lambda y: LABEL.get(
        df[df['anio_proceso']==y]['fuente_ingesta'].iloc[0] if not df[df['anio_proceso']==y].empty else 'desconocida',
        'desconocida'))
    cov_rows = ''.join(
        f'<tr><td>{int(r.anio_proceso)}</td><td>{int(r.registros)}</td>'
        f'<td>{int(r.universidades)}</td><td>{r.pagos_B} B COP</td><td>{r.fuente}</td></tr>'
        for _, r in cov.iterrows())

    # Nulos
    nulls = (df.isnull().sum() / len(df) * 100).round(1)
    nulls = nulls[nulls > 0].sort_values(ascending=False)
    null_rows = ''.join(f'<tr><td>{c}</td><td>{v}%</td></tr>' for c, v in nulls.items())

    fuente_badges = ''.join(
        f'<span style="background:{PALETTE.get(k,"#888")};color:#fff;padding:3px 10px;border-radius:12px;margin:3px;display:inline-block;font-size:0.85rem">'
        f'{LABEL.get(k,k)}: {v} filas</span>'
        for k, v in fuentes.items())

    serie_table = ''
    if SERIE_CSV.exists():
        serie_df = pd.read_csv(SERIE_CSV)
        serie_table = serie_df.to_html(index=False, border=0, classes='table',
                                       float_format=lambda x: f'{x:,.2f}')

    img2_html = f'<div class="chart"><img src="data:image/png;base64,{img2}"></div>' if img2 else ''
    img5_html = f'<div class="chart"><img src="data:image/png;base64,{img5}"></div>' if img5 else ''

    contraste_section = f'''
      <div class="section">
        <h2>🧭 Contraste metodológico 2019–2024: MEN reportado vs universo parcial IES</h2>
        <p class="note">⚠️ Esta comparación usa dos universos diferentes: (1) la serie actual del pipeline
        con transferencias directas identificables por IES y (2) el total reportado en los archivos MEN/API
        (pte_limpio_consolidado), que incluye rubros agregados, reservas y cuentas por pagar sin desglose
        institucional completo. Por eso la brecha es esperada y no implica error del pipeline.</p>
        <p class="info">La línea roja muestra cómo <strong>debería verse</strong> el presupuesto si se toma el
        total reportado por MEN/API. La línea verde muestra lo que hoy es trazable por IES en las fuentes
        nuevas DNP/SIIF/interpolado. La línea amarilla aproxima el subtotal con filtro textual de rubros IES.</p>
        {img5_html}
        {contraste_table}
      </div>''' if img5 else ''

    serie_section = f'''
      <div class="section">
        <h2>📈 Serie Nacional de Eficiencia (Costo / Graduado)</h2>
        <p class="note">⚠️ Los datos 2015–2018 provienen del MEN y representan transferencias desglosadas por IES.
        Los datos 2019–2022 son transferencias parciales (DNP/interpolado). Los datos 2023–2024 representan
        el presupuesto total de cada universidad como ente autónomo (SIIF). La serie no es directamente
        comparable entre segmentos, por eso se diferencia visualmente.</p>
        {img2_html}
        {serie_table}
      </div>''' if img2 else ''

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reporte PTE Consolidado 2015-2024 | Observatorio Educación Colombia</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', sans-serif; background: #0f0f1a; color: #e0e0e0; }}
  .hero {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 3rem 2rem; text-align: center;
    border-bottom: 2px solid #e74c3c;
  }}
  .hero h1 {{ font-size: 2.2rem; color: #fff; font-weight: 700; letter-spacing: -0.5px; }}
  .hero h1 span {{ color: #e74c3c; }}
  .hero p {{ color: #aaa; margin-top: 0.6rem; font-size: 1rem; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .kpi {{
    background: linear-gradient(135deg, #1e3a5f, #0d2137);
    border: 1px solid #2c4a6e;
    border-radius: 12px; padding: 1.4rem; text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
  }}
  .kpi .val {{ font-size: 2rem; font-weight: 700; color: #3498db; }}
  .kpi .lbl {{ font-size: 0.82rem; color: #888; margin-top: 0.3rem; }}
  .section {{
    background: #1a1a2e; border: 1px solid #2a2a4e;
    border-radius: 14px; padding: 1.8rem; margin-bottom: 1.8rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
  }}
  h2 {{ font-size: 1.3rem; color: #fff; font-weight: 600; margin-bottom: 1.2rem;
       padding-bottom: 0.6rem; border-bottom: 1px solid #2a2a4e; }}
  .chart {{ text-align: center; margin: 1rem 0; }}
  .chart img {{ max-width: 100%; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ background: #0f3460; color: #fff; padding: 0.7rem 1rem; text-align: left; font-weight: 600; }}
  td {{ padding: 0.6rem 1rem; border-bottom: 1px solid #2a2a4e; color: #ccc; }}
  tr:hover td {{ background: #1e2a4a; }}
  .note {{
    background: rgba(231,76,60,0.1); border-left: 4px solid #e74c3c;
    padding: 0.8rem 1rem; border-radius: 0 8px 8px 0; color: #e0c0c0;
    font-size: 0.9rem; margin-bottom: 1rem;
  }}
  .info {{
    background: rgba(52,152,219,0.1); border-left: 4px solid #3498db;
    padding: 0.8rem 1rem; border-radius: 0 8px 8px 0; color: #a0c8e8;
    font-size: 0.9rem; margin-bottom: 1rem;
  }}
  .fuentes {{ margin-bottom: 1rem; }}
  footer {{ text-align: center; color: #555; font-size: 0.82rem; padding: 2rem; }}
</style>
</head>
<body>
<div class="hero">
  <h1>Presupuesto del Sector Educación <span>2015–2024</span></h1>
  <p>Consolidado PTE | MEN Excel · DNP Cuadro 7 · SIIF por UEJ · Interpolación 2019</p>
  <p style="color:#666;font-size:0.85rem;margin-top:0.4rem">Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</div>

<div class="container">

  <div class="kpi-grid">
    <div class="kpi"><div class="val">{len(anios)}</div><div class="lbl">Años cubiertos (2015–2024)</div></div>
    <div class="kpi"><div class="val">{len(df):,}</div><div class="lbl">Registros totales</div></div>
    <div class="kpi"><div class="val">{df['nombre_uej'].nunique()}</div><div class="lbl">Entidades únicas</div></div>
    <div class="kpi"><div class="val">{total_pagos_b:.1f}B</div><div class="lbl">Total pagos (COP)</div></div>
    <div class="kpi"><div class="val">4</div><div class="lbl">Fuentes integradas</div></div>
  </div>

  <div class="section">
    <h2>🗂️ Fuentes de Datos Integradas</h2>
    <p class="info">El pipeline integra 4 fuentes con diferentes granularidades. Los datos 2015–2018 incluyen
    <strong>todo el presupuesto del MEN</strong>; los datos 2019–2024 son <strong>solo transferencias directas
    a universidades</strong>. Las cifras no son directamente comparables entre segmentos.</p>
    <div class="fuentes">{fuente_badges}</div>
    <table>
      <tr><th>Año</th><th>Registros</th><th>Entidades</th><th>Pagos</th><th>Fuente</th></tr>
      {cov_rows}
    </table>
  </div>

  <div class="section">
    <h2>📊 Evolución de Pagos por Fuente (2015–2024)</h2>
    <p class="note">⚠️ La escala difiere entre segmentos: 2015–2018 incluye el presupuesto completo del MEN
    (~180–237 B COP/año); 2019–2024 solo transferencias directas a universidades (~0.18–6.1 B COP/año).</p>
    <div class="chart"><img src="data:image/png;base64,{img1}"></div>
  </div>

  {contraste_section}

  {serie_section}

  <div class="section">
    <h2>🏆 Top 15 Universidades por Pagos Totales</h2>
    <div class="chart"><img src="data:image/png;base64,{img4}"></div>
  </div>

  <div class="section">
    <h2>⚖️ Concentración de Recursos — Curva de Lorenz</h2>
    <p>Gini = <strong style="color:#9b59b6">{gini_val:.3f}</strong> —
    {'Alta concentración: pocas entidades concentran la mayoría del presupuesto.' if gini_val > 0.5
     else 'Concentración moderada entre entidades.'}</p>
    <div class="chart"><img src="data:image/png;base64,{img3}"></div>
  </div>

  <div class="section">
    <h2>🔍 Calidad de Datos — Nulos por Columna</h2>
    <p class="info">Los nulos son estructurales: columnas como <code>rubro</code> y <code>tipo_gasto</code>
    no existen en las fuentes SIIF/DNP. <code>sector</code> no existe en Excel MEN. Son esperados.</p>
    <table>
      <tr><th>Columna</th><th>% Nulos</th></tr>
      {null_rows}
    </table>
  </div>

</div>
<footer>Pipeline de Datos — Observatorio de Educación Colombia | {datetime.now().year}</footer>
</body>
</html>"""

    OUT_HTML.write_text(html, encoding='utf-8')
    print("OK Reporte consolidado: " + str(OUT_HTML))

if __name__ == "__main__":
    generar_reporte()
