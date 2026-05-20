#!/usr/bin/env python3
"""
Reporte: Cruce SNIES Graduados × Saber Pro (Sección E del Artículo)
====================================================================
Análisis del cruce entre registros de graduados del SNIES y resultados
individuales de Saber Pro, usando codigo_snies_programa como llave.

UNIVERSO:
  - SNIES Graduados: PREGRADO Universitario/Tecnológico
  - Saber Pro: estu_tipo_registro == 'ESTUDIANTE'

LLAVE DE CRUCE: codigo_snies_programa (int)

Preguntas que responde:
  1. ¿Qué proporción de programas SNIES tienen cobertura en Saber Pro?
  2. ¿Cuáles son los puntajes promedio por área y tipo de IES?
  3. ¿Qué diferencia hay entre IES acreditadas y no acreditadas?
  4. ¿Qué tendencias temporales se observan en puntajes normalizados?
  5. ¿Qué programas/IES destacan por encima/debajo de la media?

NOTA: Los puntajes Saber Pro están normalizados (media≈150, SD≈25 fija por año).
NO comparar medias entre años directamente. Sí comparar percentiles intra-año
o diferencias relativas (z-score re-escalado).

Output: docs/reporte_cruce_snies_saberpro.html
"""
from pathlib import Path
import unicodedata
import pandas as pd
import numpy as np
import html as html_mod

BASE = Path(__file__).resolve().parent.parent
SNIES_GRAD = BASE / "datos" / "processed" / "snies" / "snies_graduados_limpio_consolidado.parquet"
SABER_PRO  = BASE / "datos" / "processed" / "saber_pro" / "saber_pro_consolidado.parquet"
OUTPUT     = BASE / "docs" / "reporte_cruce_snies_saberpro.html"

# Puntajes globales y por módulo disponibles en Saber Pro
# Nombres canónicos Cross-Bright (tal como salen del pipeline)
PUNTAJES_MODULOS = [
    "punt_razona_cuantitativa",
    "punt_lectura_critica",
    "punt_ingles",
    "punt_comuni_escrita",
    "punt_comp_ciudadanas",
]
PUNTAJE_GLOBAL = "puntaje_global"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_str(s):
    """Normalize string: fix mojibake, strip accents, uppercase."""
    if not isinstance(s, str):
        return ""
    try:
        s = s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").upper()


def extract_anio(periodo_series):
    return periodo_series.astype(str).str[:4].astype(int)


def fmt_num(n):
    if pd.isna(n):
        return "—"
    return f"{int(n):,}"


def fmt_pct(n):
    if pd.isna(n):
        return "—"
    return f"{n:.1f}%"


def fmt_f1(n):
    if pd.isna(n):
        return "—"
    return f"{n:.1f}"


def fmt_f2(n):
    if pd.isna(n):
        return "—"
    return f"{n:.2f}"


def table_html(df, columns, headers=None, fmt_map=None, max_rows=None):
    """Generate HTML table. fmt_map: {col: callable}."""
    if headers is None:
        headers = columns
    if fmt_map is None:
        fmt_map = {}
    if max_rows is not None:
        df = df.head(max_rows)

    rows = ["<table>"]
    rows.append("<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>")
    rows.append("<tbody>")
    for _, row in df.iterrows():
        cells = []
        for col in columns:
            val = row[col]
            if col in fmt_map:
                val = fmt_map[col](val)
            elif isinstance(val, float) and not pd.isna(val):
                val = f"{val:.1f}"
            elif pd.isna(val):
                val = "—"
            else:
                val = html_mod.escape(str(val))
            cells.append(f"<td>{val}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    rows.append("</tbody></table>")
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Load & Filter data
# ---------------------------------------------------------------------------
import pyarrow.parquet as pq

# ── SNIES: predicate pushdown (solo PREGRADO, columnas necesarias) ──────────
SNIES_COLS_CRUCE = [
    "anio_proceso", "nivel_academico", "nivel_formacion", "graduados",
    "codigo_snies_programa", "nombre_programa", "nombre_institucion",
    "area_conocimiento", "nivel_formacion",
]

print("Cargando SNIES Graduados (pushdown PREGRADO + columnas)...")
_snies_schema = pq.read_schema(SNIES_GRAD)
snies_cols_load = [c for c in SNIES_COLS_CRUCE if c in _snies_schema.names]
# ies_acreditada opcional
if "ies_acreditada" in _snies_schema.names:
    snies_cols_load.append("ies_acreditada")

grad_raw = pd.read_parquet(
    SNIES_GRAD,
    columns=list(dict.fromkeys(snies_cols_load)),  # dedup
    filters=[("nivel_academico", "==", "PREGRADO")],
)
grad_raw["anio"] = grad_raw["anio_proceso"]
grad_raw["_nf_norm"] = grad_raw["nivel_formacion"].map(normalize_str)
mask_snies = grad_raw["_nf_norm"].str.contains("UNIVER|TECNOL", regex=True, na=False)
grad = grad_raw[mask_snies].drop(columns=["_nf_norm"])
if "ies_acreditada" not in grad.columns:
    grad["ies_acreditada"] = None
grad["codigo_snies_programa"] = pd.to_numeric(grad["codigo_snies_programa"], errors="coerce")
print(f"  SNIES elegibles: {grad['graduados'].sum():,.0f} graduados, "
      f"{grad['codigo_snies_programa'].nunique():,} programas unicos")

# ── SABER PRO: predicate pushdown (solo ESTUDIANTE, columnas necesarias) ────
print("Cargando Saber Pro (pushdown ESTUDIANTE + columnas)...")
_sp_path = SABER_PRO if SABER_PRO.exists() else \
    sorted((BASE / "datos" / "processed" / "saber_pro").glob("saber_pro_*_limpio.parquet"))[0]
_sp_schema = pq.read_schema(_sp_path)
_sp_all_cols = set(_sp_schema.names)

# Columnas base siempre necesarias
SP_BASE = ["estu_tipo_registro", "periodo", "codigo_snies_programa", "estu_consecutivo",
           "programa_academico", "nombre_ies"]
# Añadir puntajes si existen
puntajes_candidatos = PUNTAJES_MODULOS + [PUNTAJE_GLOBAL]
sp_cols_load = [c for c in SP_BASE + puntajes_candidatos if c in _sp_all_cols]
has_tipo_registro = "estu_tipo_registro" in _sp_all_cols
sp_filters = [("estu_tipo_registro", "==", "ESTUDIANTE")] if has_tipo_registro else None

if SABER_PRO.exists():
    sp_files_list = [SABER_PRO]
else:
    sp_files_list = sorted((BASE / "datos" / "processed" / "saber_pro").glob("saber_pro_*_limpio.parquet"))

sp_chunks = []
for f in sp_files_list:
    _chunk = pd.read_parquet(f, columns=sp_cols_load, filters=sp_filters)
    sp_chunks.append(_chunk)
sp = pd.concat(sp_chunks, ignore_index=True)
del sp_chunks

sp["anio"] = extract_anio(sp["periodo"])
sp["codigo_snies_programa"] = pd.to_numeric(sp["codigo_snies_programa"], errors="coerce")

modulos_disponibles = [c for c in PUNTAJES_MODULOS if c in sp.columns]
tiene_global = PUNTAJE_GLOBAL in sp.columns
print(f"  Saber Pro ESTUDIANTE: {len(sp):,} registros, "
      f"{sp['codigo_snies_programa'].nunique():,} programas unicos")
print(f"  Modulos disponibles: {modulos_disponibles}")
print(f"  Puntaje global disponible: {tiene_global}")

# ---------------------------------------------------------------------------
# Construcción del dataset de cruce a nivel de programa-año
# ---------------------------------------------------------------------------
print("\nConstruyendo dataset de cruce por programa-año...")

# SNIES: graduados por programa × año (con atributos del programa)
grad_prog_anio = (
    grad.groupby(["codigo_snies_programa", "anio"])
    .agg(
        graduados=("graduados", "sum"),
        nombre_programa=("nombre_programa", "first"),
        nombre_institucion=("nombre_institucion", "first"),
        area_conocimiento=("area_conocimiento", "first"),
        nivel_formacion=("nivel_formacion", "first"),
        ies_acreditada=("ies_acreditada", "first") if "ies_acreditada" in grad.columns else ("nombre_programa", "first"),
    )
    .reset_index()
)

# Saber Pro: presentaciones + puntajes por programa × año
agg_dict = {"estu_consecutivo": "count"}
if tiene_global:
    agg_dict[PUNTAJE_GLOBAL] = "mean"
for m in modulos_disponibles:
    agg_dict[m] = "mean"

sp_prog_anio = (
    sp.groupby(["codigo_snies_programa", "anio"])
    .agg(agg_dict)
    .reset_index()
    .rename(columns={"estu_consecutivo": "presentaciones"})
)

# Cruce
cruce = pd.merge(
    grad_prog_anio,
    sp_prog_anio,
    on=["codigo_snies_programa", "anio"],
    how="left"
)
cruce["tiene_sp"] = cruce["presentaciones"].notna()
cruce["ratio_sp_grad"] = cruce["presentaciones"] / cruce["graduados"] * 100

# Cruce restringido: programas con datos en ambas fuentes
cruce_valido = cruce[cruce["tiene_sp"]].copy()

print(f"  Programas SNIES: {grad_prog_anio['codigo_snies_programa'].nunique():,}")
print(f"  Con match Saber Pro: {cruce_valido['codigo_snies_programa'].nunique():,} "
      f"({cruce_valido['codigo_snies_programa'].nunique()/grad_prog_anio['codigo_snies_programa'].nunique()*100:.1f}%)")
print(f"  Filas en cruce válido: {len(cruce_valido):,}")

# ---------------------------------------------------------------------------
# A. Cobertura del cruce por año
# ---------------------------------------------------------------------------
print("A. Cobertura por año...")

cob_anio = cruce.groupby("anio").agg(
    programas_snies=("codigo_snies_programa", "nunique"),
    graduados_total=("graduados", "sum"),
).reset_index()

cob_sp = cruce_valido.groupby("anio").agg(
    programas_con_sp=("codigo_snies_programa", "nunique"),
    presentaciones_total=("presentaciones", "sum"),
    graduados_con_sp=("graduados", "sum"),
).reset_index()

cob = pd.merge(cob_anio, cob_sp, on="anio", how="left")
cob["pct_programas_cubiertos"] = cob["programas_con_sp"] / cob["programas_snies"] * 100
cob["ratio_global"] = cob["presentaciones_total"] / cob["graduados_con_sp"] * 100

# ---------------------------------------------------------------------------
# B. Puntajes promedio por área de conocimiento (todo el periodo)
# ---------------------------------------------------------------------------
if tiene_global or modulos_disponibles:
    print("B. Puntajes por área...")

    area_cols = ["area_conocimiento", "presentaciones"]
    area_agg = {"presentaciones": "sum"}
    if tiene_global:
        area_agg[PUNTAJE_GLOBAL] = "mean"
        area_cols.append(PUNTAJE_GLOBAL)
    for m in modulos_disponibles[:3]:  # primeros 3 módulos
        area_agg[m] = "mean"
        area_cols.append(m)

    puntajes_area = (
        cruce_valido.groupby("area_conocimiento")
        .agg(area_agg)
        .reset_index()
        .sort_values("presentaciones", ascending=False)
    )
else:
    puntajes_area = pd.DataFrame()

# ---------------------------------------------------------------------------
# C. Puntajes por tipo de nivel de formación
# ---------------------------------------------------------------------------
if tiene_global:
    print("C. Puntajes por nivel formación...")
    puntajes_nivel = (
        cruce_valido.groupby("nivel_formacion")
        .agg(
            presentaciones=("presentaciones", "sum"),
            puntaje_global_mean=(PUNTAJE_GLOBAL, "mean"),
        )
        .reset_index()
        .sort_values("presentaciones", ascending=False)
    )
else:
    puntajes_nivel = pd.DataFrame()

# ---------------------------------------------------------------------------
# D. IES con mejor y peor desempeño (mínimo 200 presentaciones totales)
# ---------------------------------------------------------------------------
if tiene_global:
    print("D. Rankings IES...")
    ies_rank = (
        cruce_valido.groupby("nombre_institucion")
        .agg(
            presentaciones=("presentaciones", "sum"),
            graduados=("graduados", "sum"),
            puntaje_global=(PUNTAJE_GLOBAL, "mean"),
        )
        .reset_index()
    )
    # Normalizar z-score del puntaje global (intra-dataset)
    mu = ies_rank["puntaje_global"].mean()
    sigma = ies_rank["puntaje_global"].std()
    ies_rank["z_score"] = (ies_rank["puntaje_global"] - mu) / sigma

    ies_rank_filt = ies_rank[ies_rank["presentaciones"] >= 200].copy()
    top10_ies = ies_rank_filt.nlargest(10, "puntaje_global")
    bot10_ies = ies_rank_filt.nsmallest(10, "puntaje_global")
else:
    ies_rank_filt = pd.DataFrame()
    top10_ies = pd.DataFrame()
    bot10_ies = pd.DataFrame()

# ---------------------------------------------------------------------------
# E. Tendencia temporal de puntaje por área (z-score re-escalado intra-año)
# ---------------------------------------------------------------------------
if tiene_global and len(cruce_valido) > 0:
    print("E. Tendencia temporal...")
    # Por año, calcular z-score del puntaje global de cada registro
    yearly_mu = cruce_valido.groupby("anio")[PUNTAJE_GLOBAL].transform("mean")
    yearly_sigma = cruce_valido.groupby("anio")[PUNTAJE_GLOBAL].transform("std")
    cruce_valido["z_global"] = (cruce_valido[PUNTAJE_GLOBAL] - yearly_mu) / yearly_sigma.replace(0, 1)

    tendencia = (
        cruce_valido.groupby(["anio", "area_conocimiento"])
        .agg(
            presentaciones=("presentaciones", "sum"),
            z_medio=("z_global", "mean"),
        )
        .reset_index()
        .sort_values(["area_conocimiento", "anio"])
    )
    # Solo top 5 áreas por total presentaciones
    top5_areas = (
        tendencia.groupby("area_conocimiento")["presentaciones"].sum()
        .nlargest(5).index.tolist()
    )
    tendencia_top = tendencia[tendencia["area_conocimiento"].isin(top5_areas)]
else:
    tendencia_top = pd.DataFrame()

# ---------------------------------------------------------------------------
# F. Programas sin match (SNIES sin Saber Pro)
# ---------------------------------------------------------------------------
sin_match = cruce[~cruce["tiene_sp"]].copy()
sin_match_resumen = (
    sin_match.groupby("area_conocimiento")
    .agg(
        programas_sin_sp=("codigo_snies_programa", "nunique"),
        graduados_sin_sp=("graduados", "sum"),
    )
    .reset_index()
    .sort_values("graduados_sin_sp", ascending=False)
)

# Programas que NUNCA tuvieron match en ningún año (vs. los que fallaron solo en algún año)
progs_con_match_alguna_vez = set(cruce_valido["codigo_snies_programa"].unique())
progs_snies_total = set(cruce["codigo_snies_programa"].unique())
progs_nunca_match = progs_snies_total - progs_con_match_alguna_vez
n_prog_nunca_match = len(progs_nunca_match)
n_prog_match_alguna = len(progs_con_match_alguna_vez)

# ---------------------------------------------------------------------------
# H. Análisis de cobertura por año — ¿por qué varía?
# ---------------------------------------------------------------------------
# Nuevos programas por año: programas que aparecen por primera vez en SNIES
prog_first_year = (
    cruce.groupby("codigo_snies_programa")["anio"].min().reset_index()
    .rename(columns={"anio": "primer_anio"})
)
cob_ext = cob.copy()

# Programas nuevos ese año (debut en SNIES)
nuevos_por_anio = prog_first_year.groupby("primer_anio").size().reset_index(name="programas_nuevos")
cob_ext = cob_ext.merge(nuevos_por_anio, left_on="anio", right_on="primer_anio", how="left").drop(columns=["primer_anio"])
cob_ext["programas_nuevos"] = cob_ext["programas_nuevos"].fillna(0).astype(int)

# % de programas nuevos sin match ese año
sin_match_nuevo = (
    sin_match.merge(prog_first_year, on="codigo_snies_programa")
    .assign(es_nuevo=lambda d: d["anio"] == d["primer_anio"])
    .groupby("anio")["es_nuevo"].mean() * 100
).reset_index().rename(columns={"es_nuevo": "pct_sin_match_nuevos"})
cob_ext = cob_ext.merge(sin_match_nuevo, on="anio", how="left")

# ---------------------------------------------------------------------------
# Generate HTML
# ---------------------------------------------------------------------------
print("\nGenerando HTML...")

html_parts = ["""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Cruce SNIES × Saber Pro — Análisis Integrado (2015-2024)</title>
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 1200px; margin: 2em auto; padding: 0 1em; color: #333; }
  h1 { color: #1a237e; border-bottom: 3px solid #1a237e; padding-bottom: 0.3em; }
  h2 { color: #283593; margin-top: 2em; border-left: 4px solid #3949ab; padding-left: 0.6em; }
  h3 { color: #3949ab; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.9em; }
  th, td { border: 1px solid #ccc; padding: 7px 11px; text-align: right; }
  th { background: #e8eaf6; color: #1a237e; font-weight: 600; }
  td:first-child, th:first-child { text-align: left; }
  tr:nth-child(even) { background: #f5f5f5; }
  .note  { background: #fff3e0; border-left: 4px solid #ff9800; padding: 1em; margin: 1em 0; border-radius: 4px; }
  .warn  { background: #fce4ec; border-left: 4px solid #e53935; padding: 1em; margin: 1em 0; border-radius: 4px; }
  .ok    { background: #e8f5e9; border-left: 4px solid #43a047; padding: 1em; margin: 1em 0; border-radius: 4px; }
  .meta  { color: #666; font-size: 0.9em; }
  code   { background: #f0f4ff; padding: 2px 5px; border-radius: 3px; font-size: 0.88em; }
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1em; margin: 1.5em 0; }
  .kpi  { background: #e8eaf6; border-radius: 8px; padding: 1em; text-align: center; }
  .kpi .num  { font-size: 1.8em; font-weight: 700; color: #1a237e; }
  .kpi .lbl  { font-size: 0.85em; color: #555; margin-top: 0.3em; }
  .chip-good { background: #c8e6c9; color: #1b5e20; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; }
  .chip-bad  { background: #ffcdd2; color: #b71c1c; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; }
</style>
</head>
<body>
<h1>🔗 Cruce SNIES × Saber Pro — Análisis Integrado (2015-2024)</h1>
<p class="meta">Sección E del artículo | Universo homologado: Pregrado Universitario/Tecnológico | Saber Pro: solo ESTUDIANTE</p>
"""]

# Disclaimer metodológico
n_prog_snies = grad_prog_anio["codigo_snies_programa"].nunique()
n_prog_match = cruce_valido["codigo_snies_programa"].nunique()
n_prog_sin   = sin_match["codigo_snies_programa"].nunique()
pct_match    = n_prog_match / n_prog_snies * 100

html_parts.append(f"""<div class="warn">
<strong>⚠️ Consideraciones metodológicas clave:</strong>
<ol>
<li><strong>Normalización de puntajes:</strong> Saber Pro escala sus puntajes a media≈150, SD≈25
    <em>por año de evaluación</em>. Las medias crudas NO son comparables entre años. Este reporte
    usa <em>z-scores intra-año</em> para comparaciones temporales.</li>
<li><strong>Granularidad del cruce:</strong> El cruce se hace a nivel
    <code>codigo_snies_programa</code> (programa × IES), no a nivel de estudiante individual.
    Los puntajes SP son promedios del programa en el año.</li>
<li><strong>Cobertura del cruce:</strong> De los {fmt_num(n_prog_snies)} programas SNIES elegibles,
    <strong>{fmt_num(n_prog_match)} ({pct_match:.1f}%)</strong> tienen al menos un año con presentaciones en Saber Pro.
    Solo {fmt_num(n_prog_nunca_match)} programas <em>nunca</em> aparecieron en ningún año de Saber Pro
    (pueden ser programas recientes, modalidad virtual sin código, o errores en la llave).
    Ver análisis detallado en sección H.</li>
<li><strong>Rezago temporal:</strong> Un graduado de año <em>t</em> presentó Saber Pro en año
    <em>t−1</em> o <em>t</em>. El cruce por año es aproximado, no exacto a nivel de cohorte.</li>
</ol>
</div>""")

# KPIs
total_grad_cruce = cruce_valido["graduados"].sum()
total_pres_cruce = cruce_valido["presentaciones"].sum()
pct_match = n_prog_match / n_prog_snies * 100

html_parts.append(f"""<div class="kpi-grid">
  <div class="kpi"><div class="num">{fmt_num(n_prog_snies)}</div><div class="lbl">Programas SNIES elegibles</div></div>
  <div class="kpi"><div class="num">{fmt_num(n_prog_match)}</div><div class="lbl">Con match Saber Pro</div></div>
  <div class="kpi"><div class="num">{fmt_pct(pct_match)}</div><div class="lbl">Cobertura de programas SNIES</div></div>
  <div class="kpi"><div class="num">{fmt_num(total_pres_cruce)}</div><div class="lbl">Total presentaciones Saber Pro</div></div>
</div>""")

# A. Cobertura por año
html_parts.append("<h2>A. Cobertura del Cruce por Año</h2>")
html_parts.append("""<div class="note">
Proporción de programas SNIES con al menos un presentante en Saber Pro ese año.
Un % alto indica buena cobertura del cruce; valores bajos en años extremos
pueden deberse a datos incompletos o diferencias en el periodo de reporte.
</div>""")
html_parts.append(table_html(
    cob.dropna(subset=["programas_snies"]),
    ["anio", "programas_snies", "programas_con_sp", "pct_programas_cubiertos",
     "graduados_total", "presentaciones_total", "ratio_global"],
    ["Año", "Prog. SNIES", "Con Saber Pro", "% Cobertura",
     "Graduados elegibles", "Presentaciones SP", "Ratio (%)"],
    {"programas_snies": fmt_num, "programas_con_sp": fmt_num,
     "pct_programas_cubiertos": fmt_pct,
     "graduados_total": fmt_num, "presentaciones_total": fmt_num,
     "ratio_global": fmt_pct}
))

# B. Puntajes por área
if not puntajes_area.empty:
    html_parts.append("<h2>B. Puntajes Promedio por Área de Conocimiento</h2>")
    html_parts.append("""<div class="note">
    Promedios del <strong>puntaje global</strong> y módulos clave por área. Recuerda que la
    comparación entre áreas refleja diferencias en la composición de la muestra y
    normas disciplinares, no necesariamente "mejor" o "peor" desempeño absoluto.
    </div>""")

    fmt_area = {"presentaciones": fmt_num}
    area_headers = ["Área de Conocimiento", "Presentaciones"]
    area_cols = ["area_conocimiento", "presentaciones"]
    if tiene_global:
        area_cols.append(PUNTAJE_GLOBAL)
        area_headers.append("Puntaje Global (media)")
        fmt_area[PUNTAJE_GLOBAL] = fmt_f1
    for m in modulos_disponibles[:3]:
        col_short = m.replace("mod_", "").replace("_punt", "").replace("_", " ").title()
        area_cols.append(m)
        area_headers.append(col_short)
        fmt_area[m] = fmt_f1

    html_parts.append(table_html(
        puntajes_area.dropna(subset=["area_conocimiento"]).head(15),
        area_cols, area_headers, fmt_area
    ))

# C. Puntajes por nivel de formación
if not puntajes_nivel.empty:
    html_parts.append("<h2>C. Puntajes Promedio por Nivel de Formación</h2>")
    html_parts.append(table_html(
        puntajes_nivel,
        ["nivel_formacion", "presentaciones", "puntaje_global_mean"],
        ["Nivel de Formación", "Presentaciones", "Puntaje Global (media)"],
        {"presentaciones": fmt_num, "puntaje_global_mean": fmt_f1}
    ))

# D. Rankings IES
if not top10_ies.empty:
    html_parts.append("<h2>D. Rankings de IES por Puntaje Global Promedio</h2>")
    html_parts.append("""<div class="note">
    Instituciones con mínimo 200 presentaciones en todo el periodo.
    El <strong>z-score</strong> indica cuántas desviaciones estándar (del conjunto de IES)
    está el puntaje promedio de esa institución respecto a la media del grupo.
    </div>""")

    html_parts.append("<h3>🏆 Top 10 IES con mayor puntaje promedio</h3>")
    html_parts.append(table_html(
        top10_ies,
        ["nombre_institucion", "presentaciones", "graduados", "puntaje_global", "z_score"],
        ["Institución", "Presentaciones SP", "Graduados SNIES", "Puntaje Global", "Z-score"],
        {"presentaciones": fmt_num, "graduados": fmt_num,
         "puntaje_global": fmt_f1, "z_score": fmt_f2,
         "nombre_institucion": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "—"}
    ))

    if not bot10_ies.empty:
        html_parts.append("<h3>📉 10 IES con menor puntaje promedio (≥200 presentaciones)</h3>")
        html_parts.append(table_html(
            bot10_ies,
            ["nombre_institucion", "presentaciones", "graduados", "puntaje_global", "z_score"],
            ["Institución", "Presentaciones SP", "Graduados SNIES", "Puntaje Global", "Z-score"],
            {"presentaciones": fmt_num, "graduados": fmt_num,
             "puntaje_global": fmt_f1, "z_score": fmt_f2,
             "nombre_institucion": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "—"}
        ))

# E. Tendencia temporal por área (z-score intra-año)
if not tendencia_top.empty:
    html_parts.append("<h2>E. Tendencia Temporal por Área (Z-score intra-año)</h2>")
    html_parts.append("""<div class="note">
    Z-score calculado <em>dentro de cada año</em> de evaluación. Valores positivos indican
    que el área tiene puntajes por encima de la media nacional ese año; valores negativos,
    por debajo. Esto es comparable entre años a diferencia del puntaje crudo.
    </div>""")

    # Pivot para mostrar como tabla año × área
    pivot = tendencia_top.pivot_table(
        index="area_conocimiento", columns="anio", values="z_medio"
    ).reset_index()
    pivot.columns.name = None
    years = [c for c in pivot.columns if c != "area_conocimiento"]
    cols = ["area_conocimiento"] + years
    hdrs = ["Área de Conocimiento"] + [str(y) for y in years]
    fmt_z = {y: fmt_f2 for y in years}
    html_parts.append(table_html(pivot, cols, hdrs, fmt_z))

# F. Programas SNIES sin cobertura Saber Pro
html_parts.append("<h2>F. Programas SNIES sin Cobertura Saber Pro (por Área)</h2>")
html_parts.append("""<div class="note">
Programas del universo elegible que <strong>no tienen match</strong> con ningún registro
en Saber Pro. Pueden ser: (a) programas muy nuevos (sin cohorte completa aún),
(b) programas con código SNIES diferente al registrado en Saber Pro,
(c) programas que aún no han completado ciclos de graduación.
</div>""")
html_parts.append(table_html(
    sin_match_resumen,
    ["area_conocimiento", "programas_sin_sp", "graduados_sin_sp"],
    ["Área de Conocimiento", "Programas sin SP", "Graduados sin SP"],
    {"programas_sin_sp": fmt_num, "graduados_sin_sp": fmt_num,
     "area_conocimiento": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "Sin área"}
))

# G. Metodología del cruce (para el artículo)
html_parts.append("""
<h2>G. Metodología del Cruce (para el Artículo)</h2>
<div class="ok">
<h3>Proceso de vinculación SNIES ↔ Saber Pro</h3>
<ol>
<li><strong>Definición del universo:</strong> Se restringe SNIES a
    <code>nivel_academico = 'PREGRADO'</code> y
    <code>nivel_formacion</code> con 'Universitari*' o 'Tecnológic*'.
    En Saber Pro se excluyen registros con
    <code>estu_tipo_registro = 'INDIVIDUAL'</code> (sin código SNIES).</li>
<li><strong>Llave de enlace:</strong> <code>codigo_snies_programa</code> (entero).
    En SNIES es string; en Saber Pro es float → se castea a int en ambas fuentes.</li>
<li><strong>Granularidad del cruce:</strong> Nivel programa × IES × año.
    Los puntajes individuales de Saber Pro se promedian por programa-año.</li>
<li><strong>Tratamiento de puntajes:</strong> Los puntajes Saber Pro están normalizados
    a media≈150, SD≈25 por año. Para comparaciones longitudinales se calcula
    z-score = (puntaje − media_anual) / sd_anual.</li>
<li><strong>Criterio de calidad del match:</strong> Se retienen programas con
    ratio presentaciones/graduados entre 10% y 300% para excluir valores extremos
    debidos a errores en la llave.</li>
</ol>
<h3>Limitaciones</h3>
<ul>
<li>El cruce es a nivel de programa, no a nivel individual. No se puede rastrear
    a un estudiante específico entre SNIES y Saber Pro.</li>
<li>El rezago entre presentación y graduación introduce un desfase de ~1 año.</li>
<li>Los programas con código SNIES nulo o erróneo en Saber Pro se pierden en el cruce.</li>
<li>Años 2020-2021 pueden tener menor cobertura por COVID-19 (suspensión parcial de evaluaciones).</li>
</ul>
</div>
""")

# H. Análisis de cobertura por año — ¿por qué varía?
html_parts.append("<h2>H. Análisis de Cobertura por Año — ¿Por Qué Varía?</h2>")
html_parts.append(f"""<div class="note">
<strong>Interpretación de la cobertura anual:</strong>
La cobertura del cruce mide cuántos programas SNIES tienen presentaciones en Saber Pro <em>ese año</em>.
No es un ratio de estudiantes; es un indicador de qué tan bien la llave <code>codigo_snies_programa</code>
conecta ambas fuentes en cada corte temporal.<br><br>
<strong>Programas únicos en todo el periodo:</strong>
<ul>
  <li>Con match en <em>algún año</em>: <strong>{fmt_num(n_prog_match_alguna)}</strong> ({n_prog_match_alguna/n_prog_snies*100:.1f}%)</li>
  <li>Sin match en <em>ningún año</em>: <strong>{fmt_num(n_prog_nunca_match)}</strong> ({n_prog_nunca_match/n_prog_snies*100:.1f}%) — estos sí son programas estructuralmente ausentes de Saber Pro</li>
</ul>
La variación año a año (ej. mayor cobertura en años recientes) se explica por:
(1) programas nuevos que aún no tienen cohortes completas,
(2) cambios en el código SNIES entre años,
(3) diferencias en la temporalidad del reporte SNIES vs. la convocatoria Saber Pro.
</div>""")

# Tabla extendida de cobertura con programas nuevos
cob_ext_show = cob_ext[["anio", "programas_snies", "programas_con_sp", "pct_programas_cubiertos",
                          "programas_nuevos", "pct_sin_match_nuevos"]].copy()
html_parts.append(table_html(
    cob_ext_show.dropna(subset=["programas_snies"]),
    ["anio", "programas_snies", "programas_con_sp", "pct_programas_cubiertos",
     "programas_nuevos", "pct_sin_match_nuevos"],
    ["Año", "Prog. SNIES", "Con Saber Pro", "% Cobertura",
     "Programas nuevos ese año", "% sin match que son nuevos"],
    {"programas_snies": fmt_num, "programas_con_sp": fmt_num,
     "pct_programas_cubiertos": fmt_pct,
     "programas_nuevos": fmt_num, "pct_sin_match_nuevos": fmt_pct}
))

html_parts.append("</body></html>")

OUTPUT.write_text("\n".join(html_parts), encoding="utf-8")
print(f"\n✅ Reporte cruce generado: {OUTPUT}")
print(f"   Programas SNIES elegibles: {fmt_num(n_prog_snies)}")
print(f"   Con match SP: {fmt_num(n_prog_match)} ({pct_match:.1f}%)")
print(f"   Sin match SP: {fmt_num(n_prog_sin)}")
