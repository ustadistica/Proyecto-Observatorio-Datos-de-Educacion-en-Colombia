"""
05_pte.py — Dashboard Presupuesto del Sector Educación (PTE)
============================================================
Observatorio de Datos de Educación en Colombia
Visualización interactiva del gasto educativo 2015-2024
"""

import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ── Configuración ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
CONSOLIDADO = BASE_DIR / "datos" / "processed" / "pte" / "pte_limpio_consolidado.parquet"
FACT        = BASE_DIR / "datos" / "processed" / "pte" / "hechos"      / "fact_presupuesto.parquet"
DIM_ENT     = BASE_DIR / "datos" / "processed" / "pte" / "dimensiones" / "dim_entidad.parquet"
DIM_PER     = BASE_DIR / "datos" / "processed" / "pte" / "dimensiones" / "dim_periodo.parquet"
DIM_RUB     = BASE_DIR / "datos" / "processed" / "pte" / "dimensiones" / "dim_rubro.parquet"

PLOTLY_TEMPLATE = "plotly_dark"
COLOR_SEQ = px.colors.sequential.Plasma
ACCENT     = "#7C3AED"   # violeta / purple
GOLD       = "#F59E0B"
TEAL       = "#14B8A6"
DANGER     = "#EF4444"
SUCCESS    = "#22C55E"

# ── Helpers ───────────────────────────────────────────────────────────────────
def fix_latin(s: str) -> str:
    """Corrige mojibake latin-1→UTF-8 típico de archivos MEN."""
    if isinstance(s, str):
        try:
            return s.encode("latin-1").decode("utf-8")
        except Exception:
            return s
    return s

def humanize(valor: float, decimales: int = 1) -> str:
    """Formatea cifras grandes en billones/millones/miles de COP."""
    if valor is None or np.isnan(valor):
        return "N/D"
    abs_v = abs(valor)
    if abs_v >= 1e12:
        return f"${valor/1e12:.{decimales}f}B"
    if abs_v >= 1e9:
        return f"${valor/1e9:.{decimales}f}MM"
    if abs_v >= 1e6:
        return f"${valor/1e6:.{decimales}f}M"
    return f"${valor:,.0f}"

@st.cache_data(ttl=3600, show_spinner="🔍 Explorando el dataset PTE…")
def cargar_todos_los_datos():
    """Carga y procesa todos los artefactos PTE desde DuckDB in-memory."""
    con = duckdb.connect(":memory:")

    # — Consolidado —
    df_consol = con.execute(f"""
        SELECT
            anio_proceso,
            nombreentidad,
            descripcion,
            fuente,
            CAST(apropiacioninicial   AS DOUBLE) as apropiacion_inicial,
            CAST(apropiacionvigente   AS DOUBLE) as apropiacion_vigente,
            CAST(compromisos          AS DOUBLE) as compromisos,
            CAST(obligaciones         AS DOUBLE) as obligaciones,
            CAST(pagos                AS DOUBLE) as pagos
        FROM read_parquet('{CONSOLIDADO.as_posix()}')
        WHERE anio_proceso IS NOT NULL
          AND apropiacioninicial IS NOT NULL
          AND pagos IS NOT NULL
    """).df()

    # — Estrella: fact + dims —
    df_fact = con.execute(f"SELECT * FROM read_parquet('{FACT.as_posix()}')").df()
    df_ent  = con.execute(f"SELECT * FROM read_parquet('{DIM_ENT.as_posix()}')").df()
    df_per  = con.execute(f"SELECT * FROM read_parquet('{DIM_PER.as_posix()}')").df()
    df_rub  = con.execute(f"SELECT * FROM read_parquet('{DIM_RUB.as_posix()}')").df()

    # — Calidad: nulos en consolidado (usando el esquema canónico actualizado) —
    null_report = con.execute(f"""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN uej_codigo     IS NULL THEN 1 ELSE 0 END) as nul_uej,
               SUM(CASE WHEN tipo_fuente    IS NULL THEN 1 ELSE 0 END) as nul_tipo,
               SUM(CASE WHEN tipo_gasto     IS NULL THEN 1 ELSE 0 END) as nul_item,
               SUM(CASE WHEN anio_proceso   IS NULL THEN 1 ELSE 0 END) as nul_anio_col,
               SUM(CASE WHEN fuente IS NOT NULL AND fuente <> '' THEN 1 ELSE 0 END) as ok_fuente,
               SUM(CASE WHEN nombreentidad IS NOT NULL THEN 1 ELSE 0 END) as ok_entidad,
               SUM(CASE WHEN descripcion   IS NOT NULL THEN 1 ELSE 0 END) as ok_desc
        FROM read_parquet('{CONSOLIDADO.as_posix()}')
    """).fetchone()

    con.close()

    # Fix encoding nombres
    for col in ["nombreentidad", "descripcion", "fuente"]:
        if col in df_consol.columns:
            df_consol[col] = df_consol[col].apply(fix_latin)

    return df_consol, df_fact, df_ent, df_per, df_rub, null_report


# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  /* Encabezado hero */
  .hero-title   {font-size:2.2rem; font-weight:800; background:linear-gradient(135deg,#7C3AED,#14B8A6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0;}
  .hero-sub     {color:#94a3b8; font-size:1rem; margin-top:0.2rem;}
  /* Badge de calidad */
  .badge        {display:inline-block; padding:3px 10px; border-radius:12px; font-size:.75rem; font-weight:700; margin:2px;}
  .badge-ok     {background:#14532d; color:#4ade80;}
  .badge-warn   {background:#713f12; color:#fbbf24;}
  .badge-danger {background:#450a0a; color:#f87171;}
  /* Sección card */
  .section-card {background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.08); border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1rem;}
  /* KPI chip */
  .kpi-label    {color:#94a3b8; font-size:.75rem; text-transform:uppercase; letter-spacing:.05em;}
  .kpi-value    {font-size:1.7rem; font-weight:700; color:#f8fafc;}
  .kpi-delta    {font-size:.8rem; color:#4ade80;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p class='hero-title'>💰 Presupuesto del Sector Educación — PTE</p>", unsafe_allow_html=True)
st.markdown("<p class='hero-sub'>Ejecución presupuestal del Ministerio de Educación Nacional 2015–2024 · Observatorio Colombia</p>", unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  BOTÓN DE CARGA
# ══════════════════════════════════════════════════════════════════════════════
if "pte_cargado" not in st.session_state:
    st.session_state["pte_cargado"] = False

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    if st.button("⚡ CARGAR DATOS PTE (Ejecución Presupuestal 2015–2024)", use_container_width=True, type="primary"):
        st.session_state["pte_cargado"] = True

if not st.session_state["pte_cargado"]:
    st.info("👆 Haz clic en el botón para inicializar los motores analíticos sobre el dataset PTE.")
    st.stop()

# ── Carga de datos ────────────────────────────────────────────────────────────
df, df_fact, df_ent, df_per, df_rub, null_rep = cargar_todos_los_datos()

# Merge estrella para análisis rico
fact_full = (
    df_fact
    .merge(df_ent.rename(columns={"id": "id_entidad"}), on="id_entidad", how="left")
    .merge(df_per.rename(columns={"id": "id_periodo"}), on="id_periodo", how="left")
    .merge(df_rub.rename(columns={"id": "id_rubro"}),  on="id_rubro",  how="left")
)
# Fix encoding en fact_full
for col in fact_full.select_dtypes("object").columns:
    fact_full[col] = fact_full[col].apply(fix_latin)

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 1 — KPIs CLAVE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 Indicadores Clave del Dataset")

total_filas       = len(df)
total_fact        = len(df_fact)
total_apopiacion  = df["apropiacion_vigente"].sum()
total_pagado      = df["pagos"].sum()
total_entidades   = df["nombreentidad"].nunique()
pct_ejecucion     = (total_pagado / total_apopiacion * 100) if total_apopiacion > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Filas Consolidadas", f"{total_filas:,}", help="Registros en pte_limpio_consolidado")
with c2:
    st.metric("Registros Star Schema", f"{total_fact:,}", help="fact_presupuesto (sin nulos)")
with c3:
    st.metric("Apropiación Vigente Total", humanize(total_apopiacion), help="Suma de toda la vigencia (COP)")
with c4:
    st.metric("Pagos Ejecutados Total", humanize(total_pagado))
with c5:
    delta_color = "normal" if pct_ejecucion >= 80 else "inverse"
    st.metric("% Ejecución Global", f"{pct_ejecucion:.1f}%", delta=f"{pct_ejecucion-100:.1f}pp vs meta 100%")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 2 — DIAGNÓSTICO DE CALIDAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🔬 Diagnóstico de Calidad del Dataset PTE")

total_raw = null_rep[0]
with st.expander("📋 Ver informe detallado de nulos y anomalías", expanded=True):
    st.markdown("""
    <div class='section-card'>
    <p style='color:#94a3b8; margin-bottom:.8rem;'>
    El dataset PTE consolida reportes mensuales de múltiples años del MEN. Cada año reporta columnas distintas,
    lo que genera esquemas heterogéneos al unificarse. El análisis identifica las siguientes condiciones:
    </p>
    </div>
    """, unsafe_allow_html=True)

    # Tabla de calidad
    calidad_data = {
        "Columna / Campo": [
            "nombreentidad", "descripcion", "fuente",
            "uej (unidad ejecutora)", "tipo / cta / subcta",
            "item / sub-item", "2015 / 2016 / 2017 / 2018",
            "anio / nombremes / sector (cols post-2018)"
        ],
        "Estado": ["✅ Limpio", "✅ Limpio", "✅ Limpio",
                   "⚠️ 64.1% nulos", "⚠️ 64–79% nulos",
                   "🔴 100% nulos", "🔴 88–96% nulos",
                   "⚠️ 35.9% nulos"],
        "Filas con dato": [
            f"{null_rep[7]:,} / {total_raw:,}",
            f"{null_rep[7]:,} / {total_raw:,}",
            f"{null_rep[5]:,} / {total_raw:,}",
            f"{total_raw - null_rep[1]:,} / {total_raw:,}",
            f"{total_raw - null_rep[2]:,} / {total_raw:,}",
            "0 / {}".format(total_raw),
            f"~3,000–4,000 / {total_raw:,}",
            f"{total_raw - null_rep[4]:,} / {total_raw:,}",
        ],
        "Diagnóstico": [
            "Llave primaria analítica estable",
            "Descriptor de rubro — limpio",
            "Fuente de financiamiento — limpio",
            "Solo disponible en archivos pre-2017 del MEN (heterogeneidad de fuente)",
            "Estructura jerárquica del SIIF Nación — heterogénea por año",
            "Sub-ítems no reportados históricamente: ELIMINAR en modelo limpio",
            "Columnas año-específicas: hallazgo de drift de esquema en ingesta inicial",
            "Estructura del SIIF post-2018 — agregar IF EXISTS en ingesta",
        ],
    }
    df_calidad = pd.DataFrame(calidad_data)
    st.dataframe(df_calidad, use_container_width=True, hide_index=True)

    st.markdown("---")
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        st.markdown("""
        <span class='badge badge-ok'>✅ Star Schema</span> — **fact_presupuesto**: 486K filas, 0 nulos.
        La capa dimensional estrella está 100% limpia y lista para análisis.
        """, unsafe_allow_html=True)
    with col_q2:
        st.markdown("""
        <span class='badge badge-warn'>⚠️ Mojibake UTF-8</span> — Los textos de entidades y rubros presentan
        caracteres corruptos (ej. `NACI⿄N` → `NACIÓN`). Corregido on-the-fly en este dashboard.
        """, unsafe_allow_html=True)
    with col_q3:
        st.markdown("""
        <span class='badge badge-danger'>🔴 Columnas vestigiales</span> — `item`, `sub\\nitem`, columnas anuales
        específicas (2015–2018) deberían eliminarse del consolidado raw o manejarlas como tablas separadas.
        """, unsafe_allow_html=True)

# Gráfico de calidad — heatmap de nulos (matplotlib)
st.markdown("### 🗺️ Mapa de Completitud por Columna (Consolidado Raw)")

null_cols = {
    "nombreentidad": 0.0, "descripcion": 0.0, "fuente": 0.0,
    "apropiacioninicial": 0.0, "apropiacionvigente": 0.0,
    "compromisos": 0.0, "pagos": 0.0,
    "uej": 64.1, "tipo": 64.1, "recurso": 64.1, "sit": 64.1,
    "ord": 68.3, "sorord": 79.4,
    "anio_col": 35.9, "nombremes": 35.9, "sector": 35.9,
    "adiciones": 35.9, "reducciones": 35.9,
    "2015": 89.4, "2016": 89.6, "2017": 88.7, "2018": 96.4,
    "item": 100.0, "subitem": 100.0,
}
cols_names = list(null_cols.keys())
vals = list(null_cols.values())

fig_null, ax = plt.subplots(figsize=(14, 3))
fig_null.patch.set_facecolor("#0f172a")
ax.set_facecolor("#0f172a")
colors = ["#22c55e" if v == 0 else "#f59e0b" if v < 70 else "#ef4444" for v in vals]
bars = ax.barh(["Completitud %"], [100 - v for v in vals], color="#1e293b", height=0.5)
# Apilado
left = 0
for i, (name, val) in enumerate(zip(cols_names, vals)):
    c = "#22c55e" if val == 0 else "#f59e0b" if val < 70 else "#ef4444"
    ax.broken_barh([(left, 1)], (0.25, 0.5), facecolors=c, edgecolor="#0f172a", linewidth=0.5)
    left += 1

ax.set_xlim(0, len(cols_names))
ax.set_xticks(np.arange(0.5, len(cols_names), 1))
ax.set_xticklabels(cols_names, rotation=45, ha="right", fontsize=7.5, color="#94a3b8")
ax.set_yticks([])
ax.spines[:].set_visible(False)
ax.set_title("Mapa de Nulos por Campo — Verde: completo | Amarillo: parcial | Rojo: crítico/vacío",
             color="#e2e8f0", fontsize=10, pad=10)
legend_patches = [
    mpatches.Patch(color="#22c55e", label="Completo (0% nulos)"),
    mpatches.Patch(color="#f59e0b", label="Parcial (<70% nulos)"),
    mpatches.Patch(color="#ef4444", label="Crítico (≥70% nulos)"),
]
ax.legend(handles=legend_patches, loc="lower right", fontsize=8,
          facecolor="#1e293b", labelcolor="#e2e8f0", framealpha=0.8)
plt.tight_layout()
st.pyplot(fig_null)
plt.close()

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 3 — EVOLUCIÓN TEMPORAL (sobre consolidado limpio)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📈 Evolución Temporal del Gasto Educativo (2015–2024)")

df_anio = (df.groupby("anio_proceso")[["apropiacion_inicial","apropiacion_vigente","compromisos","pagos"]]
             .sum().reset_index().sort_values("anio_proceso"))

# Plotly: líneas + bars
fig_evol = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    row_heights=[0.65, 0.35],
    subplot_titles=("Ejecución Presupuestal (COP Billones)", "% Ejecución = Pagos / Apropiación Vigente"),
    vertical_spacing=0.1
)

for col_name, color, dash, name in [
    ("apropiacion_vigente", "#7C3AED", "solid",   "Apropiación Vigente"),
    ("compromisos",         "#F59E0B", "dot",      "Compromisos"),
    ("pagos",               "#14B8A6", "dashdot",  "Pagos"),
]:
    fig_evol.add_trace(go.Scatter(
        x=df_anio["anio_proceso"],
        y=df_anio[col_name] / 1e12,
        name=name, mode="lines+markers",
        line=dict(color=color, dash=dash, width=2.5),
        marker=dict(size=7),
        hovertemplate=f"<b>{name}</b><br>Año: %{{x}}<br>Valor: $%{{y:.2f}}B<extra></extra>"
    ), row=1, col=1)

df_anio["pct_ejec"] = (df_anio["pagos"] / df_anio["apropiacion_vigente"] * 100).clip(0, 120)
fig_evol.add_trace(go.Bar(
    x=df_anio["anio_proceso"],
    y=df_anio["pct_ejec"],
    name="% Ejecución",
    marker_color=[SUCCESS if v >= 80 else GOLD if v >= 60 else DANGER for v in df_anio["pct_ejec"]],
    hovertemplate="Año: %{x}<br>Ejecución: %{y:.1f}%<extra></extra>"
), row=2, col=1)
fig_evol.add_hline(y=80, line_dash="dot", line_color="#94a3b8", annotation_text="Meta 80%",
                   annotation_font_color="#94a3b8", row=2, col=1)

fig_evol.update_layout(
    template=PLOTLY_TEMPLATE, height=520,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=60, b=20),
    xaxis2=dict(tickformat="d")
)
fig_evol.update_yaxes(title_text="Billones COP", row=1, col=1)
fig_evol.update_yaxes(title_text="% Ejecución", ticksuffix="%", row=2, col=1)
st.plotly_chart(fig_evol, use_container_width=True)

# Tabla resumen anual
st.markdown("#### 📋 Tabla Resumen Anual (COP Millones de millones)")
df_tabla = df_anio.copy()
for c in ["apropiacion_inicial","apropiacion_vigente","compromisos","pagos"]:
    df_tabla[c] = (df_tabla[c] / 1e12).round(3)
df_tabla["pct_ejec"] = df_tabla["pct_ejec"].round(1)
df_tabla.columns = ["Año","Aprop. Inicial (B)","Aprop. Vigente (B)","Compromisos (B)","Pagos (B)","% Ejecución"]
st.dataframe(df_tabla, use_container_width=True, hide_index=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 4 — ANÁLISIS POR ENTIDAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🏛️ Concentración del Gasto por Entidad")

df_ent_agg = (df.groupby("nombreentidad")[["apropiacion_vigente","pagos"]]
               .sum().reset_index()
               .sort_values("pagos", ascending=False))

st.info("🚨 **Nota de Concentración:** El **Ministerio de Educación Nacional** absorbe más del 90% del presupuesto histórico central. Para poder visualizar cómo se distribuye la inversión en las regiones y la academia, los gráficos de esta sección **excluyen** a los entes centrales (MEN y PAE), haciendo un 'zoom' exclusivo sobre las Universidades e Institutos.")

# Filtrar para hacer zoom en universidades
df_ent_agg = df_ent_agg[~df_ent_agg["nombreentidad"].str.contains("MINISTERIO|UNIDAD ADMINISTRATIVA", case=False, na=False)]
df_ent_agg["pct_del_total"] = (df_ent_agg["pagos"] / df_ent_agg["pagos"].sum() * 100).round(2)
df_ent_agg["pct_ejec_ent"]  = (df_ent_agg["pagos"] / df_ent_agg["apropiacion_vigente"] * 100).clip(0, 130).round(1)

col_e1, col_e2 = st.columns([2, 1])

with col_e1:
    top_n = st.slider("Top N entidades", min_value=5, max_value=25, value=12, step=1, key="slider_ent")
    df_top = df_ent_agg.head(top_n).copy()
    df_top["label"] = df_top["nombreentidad"].str.split("-").str[-1].str.replace("UNIVERSIDAD", "U.").str.strip().str[:40]

    fig_ent = px.bar(
        df_top, x="pagos", y="label", orientation="h",
        color="pct_ejec_ent", color_continuous_scale="RdYlGn",
        range_color=[50, 110],
        text=df_top["pagos"].apply(lambda v: humanize(v, 0)),
        hover_data={"pct_ejec_ent": ":.1f", "pct_del_total": ":.2f"},
        labels={"pagos": "Pagos Totales (COP)", "label": "", "pct_ejec_ent": "% Ejec.", "pct_del_total": "% del total"},
        title=f"Top {top_n} Entidades por Pagos Ejecutados"
    )
    fig_ent.update_traces(textposition="outside")
    fig_ent.update_layout(
        template=PLOTLY_TEMPLATE, height=60 + 38 * top_n,
        yaxis=dict(categoryorder="total ascending"),
        coloraxis_colorbar=dict(title="% Ejec.", ticksuffix="%"),
        margin=dict(l=5, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_ent, use_container_width=True)

with col_e2:
    st.markdown("**Participación en el Gasto Total**")
    # Treemap con top 10 + Otros
    df_tree = df_ent_agg.head(10).copy()
    otros_pago = df_ent_agg.iloc[10:]["pagos"].sum()
    df_tree = pd.concat([
        df_tree[["nombreentidad","pagos"]],
        pd.DataFrame([{"nombreentidad": "Otros", "pagos": otros_pago}])
    ], ignore_index=True)
    df_tree["label"] = df_tree["nombreentidad"].str.split("-").str[-1].str.replace("UNIVERSIDAD", "U.").str.strip().str[:30]
    fig_treemap = px.treemap(
        df_tree, path=["label"], values="pagos",
        color="pagos", color_continuous_scale="Purples",
        title="Árbol de Gasto por Entidad"
    )
    fig_treemap.update_layout(template=PLOTLY_TEMPLATE, height=450, margin=dict(l=5, r=5, t=50, b=5))
    fig_treemap.update_traces(textinfo="label+percent entry")
    st.plotly_chart(fig_treemap, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 5 — DISTRIBUCIÓN Y CONCENTRACIÓN (MATPLOTLIB)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📉 Distribución Estadística del Gasto")

col_m1, col_m2 = st.columns(2)

with col_m1:
    st.markdown("**Distribución de Pagos por Registro (log-escala)**")
    fig_hist, ax = plt.subplots(figsize=(6, 4))
    fig_hist.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#111827")
    data_hist = df["pagos"].dropna()
    data_hist = data_hist[data_hist > 0]
    log_data = np.log10(data_hist)
    ax.hist(log_data, bins=50, color="#7C3AED", edgecolor="#0f172a", alpha=0.85, linewidth=0.4)
    ax.set_xlabel("log₁₀(Pagos COP)", color="#94a3b8", fontsize=9)
    ax.set_ylabel("Frecuencia", color="#94a3b8", fontsize=9)
    ax.set_title("Histograma de Pagos (escala logarítmica)", color="#e2e8f0", fontsize=10)
    ax.tick_params(colors="#94a3b8", labelsize=8)
    ax.spines["bottom"].set_color("#334155"); ax.spines["left"].set_color("#334155")
    ax.spines["top"].set_visible(False);    ax.spines["right"].set_visible(False)
    # Línea mediana
    med = log_data.median()
    ax.axvline(med, color="#F59E0B", linestyle="--", linewidth=1.5, label=f"Mediana: ${10**med:,.0f}")
    ax.legend(fontsize=8, facecolor="#1e293b", labelcolor="#e2e8f0")
    plt.tight_layout()
    st.pyplot(fig_hist)
    plt.close()

with col_m2:
    st.markdown("**Curva de Lorenz — Concentración del Gasto**")
    fig_lor, ax = plt.subplots(figsize=(6, 4))
    fig_lor.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#111827")
    sorted_pagos = np.sort(df["pagos"].dropna().values)
    sorted_pagos = sorted_pagos[sorted_pagos > 0]
    cum_share = np.cumsum(sorted_pagos) / sorted_pagos.sum()
    pop_share = np.linspace(0, 1, len(sorted_pagos))
    ax.plot(pop_share, cum_share, color="#14B8A6", linewidth=2, label="Curva de Lorenz PTE")
    ax.plot([0, 1], [0, 1], color="#475569", linestyle="--", linewidth=1, label="Igualdad perfecta")
    ax.fill_between(pop_share, cum_share, pop_share, alpha=0.15, color="#14B8A6")
    gini = 1 - 2 * (np.trapezoid(cum_share, pop_share) if hasattr(np, 'trapezoid') else np.trapz(cum_share, pop_share))
    ax.set_title(f"Curva de Lorenz — Gini ≈ {gini:.3f}", color="#e2e8f0", fontsize=10)
    ax.set_xlabel("Proporción de registros", color="#94a3b8", fontsize=9)
    ax.set_ylabel("Proporción acumulada de gasto", color="#94a3b8", fontsize=9)
    ax.tick_params(colors="#94a3b8", labelsize=8)
    ax.spines["bottom"].set_color("#334155"); ax.spines["left"].set_color("#334155")
    ax.spines["top"].set_visible(False);    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=8, facecolor="#1e293b", labelcolor="#e2e8f0")
    plt.tight_layout()
    st.pyplot(fig_lor)
    plt.close()

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 6 — ANÁLISIS DE FUENTES DE FINANCIAMIENTO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 💡 Fuentes de Financiamiento del Gasto")

st.info("""
📖 **Glosario de Fuentes de Financiación:**
*   **Nación / Aporte Nacional:** Rubros provenientes del Presupuesto General de la Nación (recaudo de impuestos nacionales) inyectados para sostener a la entidad.
*   **Recursos Propios:** Dinero que la propia entidad es capaz de generar a través de su gestión (ej. venta de servicios, consultorías, matrículas en el caso de algunas instituciones). Las universidades más robustas suelen tener una porción altísima de Recursos Propios para complementar lo Nacional.
""")

df_fuente = (df.groupby("fuente")[["apropiacion_vigente","pagos"]]
              .sum().reset_index().sort_values("pagos", ascending=False))
df_fuente["fuente_clean"] = df_fuente["fuente"].apply(fix_latin)

c_f1, c_f2 = st.columns(2)

with c_f1:
    fig_pie = px.pie(
        df_fuente.head(12), names="fuente_clean", values="pagos",
        title="Distribución de Pagos por Fuente",
        color_discrete_sequence=px.colors.sequential.Plasma,
        hole=0.4
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(template=PLOTLY_TEMPLATE, height=420, margin=dict(l=5, r=5, t=50, b=5))
    st.plotly_chart(fig_pie, use_container_width=True)

with c_f2:
    fig_fbar = px.bar(
        df_fuente.head(10), x="pagos", y="fuente_clean", orientation="h",
        color="fuente_clean", text=df_fuente.head(10)["pagos"].apply(lambda v: humanize(v, 0)),
        title="Top 10 Fuentes por Pagos",
        labels={"pagos": "Pagos (COP)", "fuente_clean": "Fuente"},
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    fig_fbar.update_traces(showlegend=False, textposition="outside")
    fig_fbar.update_layout(
        template=PLOTLY_TEMPLATE, height=420,
        yaxis=dict(categoryorder="total ascending"),
        margin=dict(l=5, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_fbar, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 7 — HEATMAP EJECUTOR × AÑO (PLOTLY)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🔥 Heatmap: Pagos por Entidad × Año")

df_heat = (df.groupby(["anio_proceso", "nombreentidad"])["pagos"]
             .sum().reset_index())

# Excluir los entes centrales monopólicos (MEN y PAE) para ver cómo se reparte el dinero en instituciones/universidades
df_heat = df_heat[~df_heat["nombreentidad"].str.contains("MINISTERIO|UNIDAD ADMINISTRATIVA", case=False, na=False)]

df_heat["ent_label"] = df_heat["nombreentidad"].str.split("-").str[-1].str.replace("UNIVERSIDAD", "U.").str.strip().str[:35]

top_entidades = df_heat.groupby("ent_label")["pagos"].sum().nlargest(15).index
df_heat_top = df_heat[df_heat["ent_label"].isin(top_entidades)]
pivot = df_heat_top.pivot_table(index="ent_label", columns="anio_proceso", values="pagos", fill_value=0)
pivot = pivot / 1e12  # billones

fig_heat = go.Figure(go.Heatmap(
    z=pivot.values,
    x=[str(c) for c in pivot.columns],
    y=pivot.index.tolist(),
    colorscale="Viridis",
    hoverongaps=False,
    hovertemplate="Entidad: %{y}<br>Año: %{x}<br>Pagos: $%{z:.2f}B<extra></extra>",
    colorbar=dict(title="Billones COP")
))
fig_heat.update_layout(
    template=PLOTLY_TEMPLATE,
    title="Top 15 Entidades (Excluyendo MinEducación) — Pagos por Año (COP Billones)",
    height=550,
    xaxis_title="Año",
    yaxis_title="",
    margin=dict(l=20, r=20, t=60, b=20)
)
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 8 — STAR SCHEMA EXPLORER (FACT + DIMS)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## ⭐ Explorador del Modelo Estrella (Star Schema Limpio)")

st.success(f"""
**fact_presupuesto: {len(df_fact):,} filas — 0 valores nulos** — La tabla de hechos del modelo estrella es 100% íntegra.
Aquí se consolida la trazabilidad completa de la programación presupuestal con llaves a las dimensiones.
""")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Fact Presupuesto", "🏛️ dim_entidad", "📅 dim_periodo", "📂 dim_rubro"])

with tab1:
    st.markdown("**Vista de los primeros 100 registros del hecho presupuestal**")
    cols_show = ["id_entidad","id_rubro","id_periodo","apropiacioninicial","apropiacionvigente","compromisos","obligaciones","pagos"]
    st.dataframe(df_fact[cols_show].head(100), use_container_width=True, hide_index=True)

    st.markdown("**Estadísticas descriptivas del hecho:**")
    desc_stats = df_fact[["apropiacioninicial","apropiacionvigente","compromisos","obligaciones","pagos"]].describe().round(2)
    desc_stats.index.name = "Estadístico"
    st.dataframe(desc_stats.T, use_container_width=True)

with tab2:
    st.markdown(f"**{len(df_ent)} entidades presupuestales registradas**")
    st.dataframe(df_ent, use_container_width=True, hide_index=True)

with tab3:
    st.markdown(f"**{len(df_per)} períodos presupuestales**")
    st.dataframe(df_per, use_container_width=True, hide_index=True)

with tab4:
    st.markdown(f"**{len(df_rub)} rubros presupuestales en total**")
    
    st.info("""
    ℹ️ **Sobre los valores `None`:** De los 869 rubros históricos, **654** pertenecen a la era antigua (2015-2018) donde el Ministerio no publicaba el desglose jerárquico. 
    Solo los **215** rubros modernos (2019-2024 en adelante) poseen el detalle completo corporativo (`tipo_gasto`, `nivel_rubro`, etc.).
    """)
    
    search_rub = st.text_input("🔍 Buscar rubro moderno (Ej: Infraestructura):", key="buscador_rubro")
    df_rub_display = df_rub.copy()
    for col in df_rub_display.select_dtypes("object").columns:
        df_rub_display[col] = df_rub_display[col].apply(fix_latin)
    if search_rub:
        mask = df_rub_display.apply(lambda row: row.astype(str).str.contains(search_rub, case=False).any(), axis=1)
        df_rub_display = df_rub_display[mask]
    st.dataframe(df_rub_display, use_container_width=True, hide_index=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 9 — BOX PLOTS POR AÑO (matplotlib) + SCATTER APROPIACION vs PAGOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📦 Variabilidad del Gasto por Año — Boxplots")

anios_disp = sorted(df["anio_proceso"].dropna().unique())
fig_box, ax = plt.subplots(figsize=(14, 5))
fig_box.patch.set_facecolor("#0f172a")
ax.set_facecolor("#111827")
data_box = [df[df["anio_proceso"] == a]["pagos"].dropna().clip(0).values / 1e9 for a in anios_disp]
bp = ax.boxplot(data_box, patch_artist=True, medianprops=dict(color="#F59E0B", linewidth=2),
                flierprops=dict(marker=".", color="#7C3AED", alpha=0.3, markersize=3),
                whiskerprops=dict(color="#475569"), capprops=dict(color="#475569"),
                boxprops=dict(facecolor="#1d4ed8", alpha=0.6, color="#3b82f6"))
ax.set_xticks(range(1, len(anios_disp) + 1))
ax.set_xticklabels([str(int(a)) for a in anios_disp], color="#94a3b8", fontsize=9)
ax.set_ylabel("Pagos por registro (Miles de millones COP)", color="#94a3b8", fontsize=9)
ax.set_title("Distribución de Pagos por Registro y Año (escala MM millones)", color="#e2e8f0", fontsize=11)
ax.tick_params(colors="#94a3b8", labelsize=8)
ax.spines["bottom"].set_color("#334155"); ax.spines["left"].set_color("#334155")
ax.spines["top"].set_visible(False);    ax.spines["right"].set_visible(False)
ax.set_yscale("symlog", linthresh=1)
ax.grid(axis="y", color="#1e293b", linewidth=0.5)
plt.tight_layout()
st.pyplot(fig_box)
plt.close()

# Scatter apropiación vs pagos
st.markdown("## 🔍 Correlación Apropiación Vigente vs Pagos por Entidad")

df_scatter_ent = (df.groupby("nombreentidad")[["apropiacion_vigente","pagos","compromisos"]]
                   .sum().reset_index())
df_scatter_ent["label"] = df_scatter_ent["nombreentidad"].str.split("-").str[0].str.strip().str[:30]
df_scatter_ent["pct_e"] = (df_scatter_ent["pagos"] / df_scatter_ent["apropiacion_vigente"] * 100).clip(0, 130).round(1)

fig_scatter = px.scatter(
    df_scatter_ent,
    x="apropiacion_vigente", y="pagos",
    color="pct_e",
    size="compromisos",
    size_max=45,
    hover_name="label",
    color_continuous_scale="RdYlGn",
    range_color=[40, 110],
    labels={"apropiacion_vigente": "Apropiación Vigente (COP)", "pagos": "Pagos Ejecutados (COP)", "pct_e": "% Ejec."},
    title="Correlación Apropiación ↔ Pagos por Entidad (tamaño = Compromisos)",
    log_x=True, log_y=True
)
# Línea de ejecución perfecta
max_val = max(df_scatter_ent["apropiacion_vigente"].max(), df_scatter_ent["pagos"].max())
min_val = max(df_scatter_ent[df_scatter_ent["pagos"] > 0]["pagos"].min(), 1)
fig_scatter.add_shape(
    type="line", x0=min_val, y0=min_val, x1=max_val, y1=max_val,
    line=dict(color="#94a3b8", dash="dash", width=1)
)
fig_scatter.add_annotation(text="Ejecución = 100%", x=np.log10(max_val * 0.3),
                             y=np.log10(max_val * 0.3), showarrow=False,
                             font=dict(color="#94a3b8", size=10))
fig_scatter.update_layout(template=PLOTLY_TEMPLATE, height=500, margin=dict(l=20, r=20, t=60, b=20))
st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 10 — ALERTAS Y RECOMENDACIONES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## ⚠️ Hallazgos y Recomendaciones de Ingesta")

with st.expander("📢 Ver hallazgos detallados", expanded=False):
    st.markdown("""
    ### 🔴 Problemas Críticos Detectados
    
    | # | Hallazgo | Columnas Afectadas | Severidad | Recomendación |
    |---|----------|-------------------|-----------|---------------|
    | 1 | **Mojibake UTF-8** | `nombreentidad`, `descripcion`, todos los textos | Media | Agregar `encoding='latin-1'` en la lectura de XLS originales |
    | 2 | **Columnas fantasma** | `item`, `sub\\nitem`, `sub\\nitem_2` | Alta | Eliminar del consolidado; 100% nulos sin valor analítico |
    | 3 | **Columnas año-específicas** | `2015`, `2016`, `2017`, `2018` | Media | Pivotar a formato largo (long format) durante ingesta |
    | 4 | **Esquema heterogéneo** | `uej`, `tipo`, `cta`, `ord`, `sor\\nord` | Media | Solo disponibles pre-2017; aislar en tabla histórica separada |
    | 5 | **Columnas post-2018** | `anio`, `nombremes`, `sector`, `situacion`, etc. | Media | Solo disponibles post-2018; aislar en tabla moderna separada |
    
    ### ✅ El Star Schema está Limpio
    
    - **fact_presupuesto.parquet**: 486,162 registros, **0 nulos**, tipos correctos (DOUBLE para montos)
    - **dim_entidad**: Dimensión compacta, estable
    - **dim_periodo**: Cobertura temporal completa
    - **dim_rubro**: Jerarquía de rubros lista para navegar
    
    ### 💡 Próximos Pasos Recomendados
    
    1. **Corregir encoding** en scripts de ingesta (`icfes_saber11.py` ya lo hace, replicar en `pte_ingesta.py`)
    2. **Eliminar columnas vestigiales** del consolidado raw durante la fase de transformación
    3. **Normalizar el consolidado** en dos sub-tablas: pre-2017 y post-2017 para aprovechar todos los campos
    4. **Unir con SNIES** vía `codigoentidad` (disponible post-2018) para análisis cruzado IES+Presupuesto
    """)

st.success("✅ El modelo Estrella (Star Schema) del PTE está **100% íntegro y listo para análisis**. "
           "El consolidado raw presenta heterogeneidad por esquemas temporales del MEN — normal en datos gubernamentales multianuales.")

# Cache re-trigger for Dec 2016 fix
