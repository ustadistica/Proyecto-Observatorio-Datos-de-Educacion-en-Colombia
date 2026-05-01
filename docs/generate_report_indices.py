"""
generate_report_indices.py — Genera el reporte HTML de Eficiencia Universitaria
================================================================================
Fuente de datos: datos/processed/eficiencia_universidades.csv
Presupuesto:     Solo rubros Ley 30 Art 86/87 (Transferencias directas a IES)
Graduados:       SNIES (graduados por universidad y anio)
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
import seaborn as sns

PROJECT_ROOT    = Path(__file__).resolve().parent.parent
CSV_PATH        = PROJECT_ROOT / "datos" / "processed" / "eficiencia_universidades.csv"
SERIE_NAC_PATH  = PROJECT_ROOT / "datos" / "processed" / "serie_nacional_eficiencia.csv"
CONTRASTE_PATH  = PROJECT_ROOT / "datos" / "processed" / "pte" / "contraste_men_vs_fuentes_2019_2024.csv"
OUTPUT_HTML     = PROJECT_ROOT / "docs" / "reporte_eficiencia_universidades.html"


def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def main():
    if not CSV_PATH.exists():
        print("[ERROR] No se encuentra el dataset: " + str(CSV_PATH))
        return

    df = pd.read_csv(CSV_PATH)
    df['anio_proceso'] = df['anio_proceso'].astype(int)

    # ── KPIs globales ────────────────────────────────────────────────────────
    anios             = sorted(df['anio_proceso'].unique())
    # Si existe la serie nacional, usar su rango para los KPIs de periodo
    if SERIE_NAC_PATH.exists():
        _sn = pd.read_csv(SERIE_NAC_PATH)
        anios_range = (int(_sn['anio_proceso'].min()), int(_sn['anio_proceso'].max()))
    else:
        anios_range = (min(anios), max(anios))
    total_inv         = df['pagos_millones'].sum()
    total_grad        = df['total_graduados'].sum()
    costo_prom_nac    = total_inv / total_grad if total_grad > 0 else 0
    total_unis        = df['institucion'].nunique()

    contraste = None
    if CONTRASTE_PATH.exists():
        try:
            contraste = pd.read_csv(CONTRASTE_PATH)
            contraste['anio_proceso'] = pd.to_numeric(contraste['anio_proceso'], errors='coerce').astype('Int64')
        except Exception:
            contraste = None

    # ── Robustez: solo instituciones con >=500 graduados acumulados ──────────
    eficiencia_promedio = df.groupby('institucion', as_index=False).agg(
        costo_promedio=('costo_por_graduado_millones', 'mean'),
        total_graduados=('total_graduados', 'sum'),
        total_pagos=('pagos_millones', 'sum'),
        annos_datos=('anio_proceso', 'nunique')
    )
    eficiencia_robusta = eficiencia_promedio[
        (eficiencia_promedio['total_graduados'] >= 500) &
        (eficiencia_promedio['annos_datos'] >= 2)
    ].copy()

    # ── Grafico 1: Top 10 mas eficientes ────────────────────────────────────
    top_10 = eficiencia_robusta.sort_values('costo_promedio').head(10)
    fig1, ax1 = plt.subplots(figsize=(11, 5))
    colors1 = sns.color_palette("viridis", len(top_10))
    ax1.barh(top_10['institucion'], top_10['costo_promedio'], color=colors1)
    ax1.set_title("Top 10 Instituciones Más Eficientes\n(Menor Costo por Graduado — Ley 30 Art. 86/87)", fontsize=13)
    ax1.set_xlabel("Millones de Pesos por Graduado")
    ax1.invert_yaxis()
    for i, v in enumerate(top_10['costo_promedio']):
        ax1.text(v + 0.5, i, f"${v:.1f}M", va='center', fontsize=9)
    fig1.tight_layout()
    img1 = fig_to_base64(fig1)

    # ── Grafico 2: Top 10 menos eficientes ──────────────────────────────────
    bottom_10 = eficiencia_robusta.sort_values('costo_promedio', ascending=False).head(10)
    fig2, ax2 = plt.subplots(figsize=(11, 5))
    colors2 = sns.color_palette("magma", len(bottom_10))
    ax2.barh(bottom_10['institucion'], bottom_10['costo_promedio'], color=colors2)
    ax2.set_title("Top 10 Instituciones con Mayor Costo por Graduado\n(Ley 30 Art. 86/87 — 2015-2024)", fontsize=13)
    ax2.set_xlabel("Millones de Pesos por Graduado")
    ax2.invert_yaxis()
    for i, v in enumerate(bottom_10['costo_promedio']):
        ax2.text(v + 0.5, i, f"${v:.1f}M", va='center', fontsize=9)
    fig2.tight_layout()
    img2 = fig_to_base64(fig2)

    # ── Grafico 3: Evolucion historica 2015-2024 usando serie nacional ───────
    if SERIE_NAC_PATH.exists():
        evolucion = pd.read_csv(SERIE_NAC_PATH)
        evolucion['anio_proceso'] = evolucion['anio_proceso'].astype(int)
    else:
        evolucion = df.groupby('anio_proceso', as_index=False).agg(
            pagos_millones=('pagos_millones', 'sum'),
            total_graduados=('total_graduados', 'sum')
        )
        evolucion['costo_nacional_millones'] = evolucion['pagos_millones'] / evolucion['total_graduados']
        evolucion['tipo_dato'] = evolucion['anio_proceso'].apply(
            lambda y: 'desglosado_por_ies' if y <= 2018 else 'agregado_nacional')

    ev_desg = evolucion[evolucion['tipo_dato'] == 'desglosado_por_ies']
    ev_agre = evolucion[evolucion['tipo_dato'] == 'agregado_nacional']

    fig3, ax3 = plt.subplots(figsize=(12, 5))
    ax3.plot(ev_desg['anio_proceso'], ev_desg['costo_nacional_millones'],
             marker='o', color='#27ae60', linewidth=2.5, markersize=8,
             label='2015-2018: Desglosado por IES (dato granular)')
    ax3.plot(ev_agre['anio_proceso'], ev_agre['costo_nacional_millones'],
             marker='s', color='#e67e22', linewidth=2.5, linestyle='--', markersize=8,
             label='2019-2024: Agregado nacional (rubros sin desglose individual)')

    # Referencias de contraste: MEN reportado total y MEN filtro IES
    ref = None
    if contraste is not None and not contraste.empty:
        grad = evolucion[['anio_proceso', 'total_graduados']].copy() if 'total_graduados' in evolucion.columns else None
        if grad is None or grad.empty:
            grad = df.groupby('anio_proceso', as_index=False)['total_graduados'].sum()
        grad['anio_proceso'] = pd.to_numeric(grad['anio_proceso'], errors='coerce').astype('Int64')

        use_cols = ['anio_proceso']
        for c in ['pagos_men_total_reportado_B', 'pagos_men_filtro_ies_vig_actual_B']:
            if c in contraste.columns:
                use_cols.append(c)
        ref = contraste[use_cols].copy()
        ref = ref.merge(grad, on='anio_proceso', how='left')
        ref = ref.dropna(subset=['anio_proceso', 'total_graduados'])
        ref = ref[ref['anio_proceso'] >= 2019]
        # [RED LINE OMITTED AS PER USER REQUEST]
        if not ref.empty and 'pagos_men_filtro_ies_vig_actual_B' in ref.columns:
            ref['costo_ref_men_filtro_ies_millones'] = (pd.to_numeric(ref['pagos_men_filtro_ies_vig_actual_B'], errors='coerce') * 1e6) / pd.to_numeric(ref['total_graduados'], errors='coerce')
            ax3.plot(ref['anio_proceso'], ref['costo_ref_men_filtro_ies_millones'],
                     marker='d', color='#8e44ad', linewidth=2.0, linestyle=':', markersize=6,
                     label='2019-2024: Referencia MEN filtro IES (texto + vigencia actual)')
    if not ev_desg.empty and not ev_agre.empty:
        ax3.plot([ev_desg['anio_proceso'].iloc[-1], ev_agre['anio_proceso'].iloc[0]],
                 [ev_desg['costo_nacional_millones'].iloc[-1], ev_agre['costo_nacional_millones'].iloc[0]],
                 color='gray', linewidth=1.2, linestyle=':', alpha=0.6)
    ax3.axvspan(2018.5, 2024.5, alpha=0.06, color='orange')
    # Etiquetas en cada punto
    for _, r in evolucion.iterrows():
        ax3.annotate(f"${r['costo_nacional_millones']:.1f}M",
                     xy=(r['anio_proceso'], r['costo_nacional_millones']),
                     xytext=(0, 10), textcoords='offset points',
                     ha='center', fontsize=8, color='#2c3e50')
    ax3.set_title("Evolucion del Costo Nacional por Graduado — Ley 30 Art. 86/87 (2015–2024)", fontsize=13)
    ax3.set_xlabel("Ano")
    ax3.set_ylabel("Millones de Pesos por Graduado")
    ax3.set_xticks(evolucion['anio_proceso'])
    ax3.legend(fontsize=9, loc='upper left')
    ax3.grid(alpha=0.3)
    fig3.tight_layout()
    img3 = fig_to_base64(fig3)

    # ── Tabla Top 10 ─────────────────────────────────────────────────────────
    tabla_html = top_10[['institucion', 'total_graduados', 'costo_promedio', 'annos_datos']].copy()
    tabla_html['costo_promedio']  = tabla_html['costo_promedio'].apply(lambda x: f"${x:,.1f} M")
    tabla_html['total_graduados'] = tabla_html['total_graduados'].apply(lambda x: f"{int(x):,}")
    tabla_html.columns = ['Institución', 'Graduados Acumulados', 'Costo Prom. por Grad.', 'Años con Datos']
    html_table = tabla_html.to_html(classes="data-table", index=False)

    # ── HTML ─────────────────────────────────────────────────────────────────
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Eficiencia Universitaria — Observatorio Educacion Colombia</title>
    <meta name="description" content="Analisis de eficiencia presupuestal MEN vs graduados SNIES 2015-2024">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; color: #2c3e50; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
        header {{ background: linear-gradient(135deg, #1a252f 0%, #2980b9 100%); color: white; padding: 36px 32px; border-radius: 12px; margin-bottom: 28px; }}
        header h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 8px; }}
        header p {{ opacity: 0.85; font-size: 1rem; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 28px; }}
        .kpi-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.08); border-top: 4px solid #2980b9; }}
        .kpi-label {{ font-size: .8rem; color: #7f8c8d; text-transform: uppercase; letter-spacing: .05em; }}
        .kpi-value {{ font-size: 1.7rem; font-weight: 700; color: #2c3e50; margin-top: 6px; }}
        section {{ background: white; border-radius: 10px; padding: 28px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
        section h2 {{ font-size: 1.2rem; color: #2980b9; margin-bottom: 18px; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
        .chart-wrap {{ text-align: center; }}
        .chart-wrap img {{ max-width: 100%; border-radius: 8px; border: 1px solid #ecf0f1; }}
        .data-table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: .9rem; }}
        .data-table th {{ background: #2980b9; color: white; padding: 12px; text-align: left; }}
        .data-table td {{ padding: 10px 12px; border-bottom: 1px solid #ecf0f1; }}
        .data-table tr:hover td {{ background: #f8f9fa; }}
        .alert {{ border-left: 4px solid #f39c12; background: #fef9e7; padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 16px 0; font-size: .9rem; }}
        .alert-info {{ border-left-color: #3498db; background: #ebf5fb; }}
        .alert strong {{ display: block; margin-bottom: 4px; }}
        .badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: .75rem; font-weight: 600; }}
        .badge-green {{ background: #d5f5e3; color: #1e8449; }}
        .badge-orange {{ background: #fdebd0; color: #b9770e; }}
        footer {{ text-align: center; color: #95a5a6; font-size: .8rem; padding: 24px 0; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>Reporte de Eficiencia: Gasto MEN vs Graduados SNIES</h1>
        <p>Observatorio de Datos de Educacion en Colombia — Transferencias Ley 30 Art. 86/87 (2015–2024)</p>
    </header>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Periodo Analizado</div>
            <div class="kpi-value">{anios_range[0]} – {anios_range[1]}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">IES Identificadas</div>
            <div class="kpi-value">{total_unis}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Graduados Cruzados</div>
            <div class="kpi-value">{int(total_grad):,}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Costo Prom. Nacional</div>
            <div class="kpi-value">${costo_prom_nac:,.1f} M</div>
        </div>
    </div>

    <section>
        <h2>Nota Metodologica Critica — Limitacion de Transparencia</h2>
        <div class="alert">
            <strong>Periodo 2015–2018 <span class="badge badge-green">Dato Desglosado por IES</span></strong>
            Los Excels de ejecucion presupuestal del MEN publicados hasta 2018 incluyen un rubro individual por
            cada universidad publica. Esto permite calcular el presupuesto asignado especificamente a cada
            institucion y cruzarlo con sus graduados SNIES.
        </div>
        <div class="alert" style="border-left-color:#e74c3c; background:#fdedec;">
            <strong>Periodo 2019–2024 <span class="badge badge-orange">Dato Agregado — Sin Desglose</span></strong>
            A partir de 2019 el MEN cambio el formato de sus reportes de ejecucion presupuestal.
            Los rubros de transferencias a IES ya no aparecen por universidad sino como un unico registro
            <em>"A Instituciones de Educacion Superior Publicas"</em>. Esto hace <strong>imposible</strong>
            calcular el presupuesto individual de cada universidad para este periodo con los datos abiertos
            disponibles. Esta es una brecha de transparencia documentada en el sistema de datos abiertos
            del gobierno colombiano. Para el cruce 2019-2024 solo se pudieron identificar las IES cuyos
            rubros aun aparecen de forma individual en el SIIF (transferencias menores y pasivos pensionales).
        </div>
        <div class="alert alert-info">
            <strong>Presupuesto utilizado: Solo Ley 30 Art. 86/87</strong>
            El calculo de eficiencia excluye el SGP (Sistema General de Participaciones, destinado a
            colegios de primaria y bachillerato), el Magisterio, la Alimentacion Escolar y otros programas
            no universitarios. Solo se contabiliza la transferencia directa a IES publicas.
        </div>
    </section>

    <section>
        <h2>Ranking de Eficiencia — Top 10 IES mas Eficientes</h2>
        {html_table}
        <div class="chart-wrap" style="margin-top:20px">
            <img src="data:image/png;base64,{img1}" alt="Top 10 IES eficientes">
        </div>
    </section>

    <section>
        <h2>IES con Mayor Costo por Graduado</h2>
        <div class="chart-wrap">
            <img src="data:image/png;base64,{img2}" alt="Top 10 IES menos eficientes">
        </div>
    </section>

    <section>
        <h2>Evolucion Historica 2015–2024</h2>
        <div class="alert alert-info">
            <strong>Como leer este grafico:</strong>
            La linea <span style="color:#2ecc71; font-weight:600">verde</span> (2015-2018) usa datos desglosados por universidad.
            La linea <span style="color:#e67e22; font-weight:600">naranja punteada</span> (2019-2024) usa solo los rubros individuales
            que aun aparecen en el SIIF — el universo es mas pequeno y el costo por graduado no es directamente
            comparable con el periodo anterior. La linea
            <span style="color:#8e44ad; font-weight:600">morado punteada</span> muestra una aproximacion por
            filtro textual de rubros IES en vigencia actual. Estas lineas sirven para contrastar cobertura,
            no para ranking individual por universidad.
        </div>
        <div class="chart-wrap">
            <img src="data:image/png;base64,{img3}" alt="Evolucion historica costo por graduado">
        </div>
    </section>

    <footer>
        <p>Generado automaticamente — Observatorio de Datos de Educacion en Colombia</p>
        <p>Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Fuentes: PTE-MEN (Ley 30 Art.86/87) + SNIES</p>
    </footer>
</div>
</body>
</html>"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("[OK] Reporte HTML generado con exito en: " + OUTPUT_HTML.name)


if __name__ == '__main__':
    main()
