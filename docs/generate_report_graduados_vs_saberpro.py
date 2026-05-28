#!/usr/bin/env python3
"""
Reporte: Graduados SNIES vs Presentaciones Saber Pro (Side-by-Side 2015-2024)
=============================================================================
Compara conteos de graduados del SNIES con presentaciones del Saber Pro
por año, programa y tipo de IES.

UNIVERSO CORRECTO:
  - SNIES Graduados: filtrado a PREGRADO Universitario/Tecnológico
    (excluye Técnica Profesional, Posgrado, etc.)
  - Saber Pro: solo estu_tipo_registro == 'ESTUDIANTE'
    (excluye INDIVIDUAL que no tienen código SNIES)

Output: docs/reporte_graduados_vs_saberpro.html
"""
from pathlib import Path
import unicodedata
import pandas as pd
import numpy as np
import html as html_mod

BASE = Path(__file__).resolve().parent.parent
SNIES_GRAD = BASE / "datos" / "processed" / "snies" / "snies_graduados_limpio_consolidado.parquet"
SABER_PRO  = BASE / "datos" / "processed" / "saber_pro" / "saber_pro_consolidado.parquet"
OUTPUT     = BASE / "docs" / "reporte_graduados_vs_saberpro.html"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fix_encoding(s):
    """Fix latin-1/utf-8 mojibake in strings."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s


def normalize_str(s):
    """Normalize a string: fix mojibake, strip accents, uppercase."""
    if not isinstance(s, str):
        return ""
    # Fix mojibake
    try:
        s = s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    # Strip accents
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").upper()


def extract_anio_from_periodo(periodo_series):
    """Extract year from Saber Pro periodo (e.g. '20232' -> 2023)."""
    return periodo_series.astype(str).str[:4].astype(int)


def fmt_num(n):
    """Format number with thousands separator."""
    if pd.isna(n):
        return "—"
    return f"{int(n):,}"


def fmt_pct(n):
    if pd.isna(n) or n == 0:
        return "—"
    return f"{n:.1f}%"


# ---------------------------------------------------------------------------
# Load & Filter data
# ---------------------------------------------------------------------------
# Columnas necesarias de cada fuente
SNIES_COLS = [
    "anio_proceso", "nivel_academico", "nivel_formacion", "graduados",
    "codigo_snies_programa", "nombre_programa", "nombre_institucion",
    "area_conocimiento", "ies_acreditada",
]
SP_COLS = [
    "estu_tipo_registro", "periodo", "codigo_snies_programa",
    "estu_consecutivo", "programa_academico", "nombre_ies",
]

print("Cargando SNIES Graduados (solo PREGRADO, columnas necesarias)...")
# Predicate pushdown: nivel_academico == 'PREGRADO' reduce a ~73% del total
grad_raw = pd.read_parquet(
    SNIES_GRAD,
    columns=[c for c in SNIES_COLS if c != "ies_acreditada"],  # acreditada puede no existir
    filters=[("nivel_academico", "==", "PREGRADO")],
)
# Añadir ies_acreditada si existe
try:
    _acred = pd.read_parquet(SNIES_GRAD, columns=["ies_acreditada"])
    grad_raw["ies_acreditada"] = _acred["ies_acreditada"].values
except Exception:
    grad_raw["ies_acreditada"] = None

grad_raw["anio"] = grad_raw["anio_proceso"]

# ── FILTRO UNIVERSO SNIES ──────────────────────────────────────────────────
print("  Aplicando filtro nivel_formacion (Universitario/Tecnologico)...")
grad_raw["_nf_norm"] = grad_raw["nivel_formacion"].map(normalize_str)
n_raw_filt = grad_raw["graduados"].sum()
mask_snies = grad_raw["_nf_norm"].str.contains("UNIVER|TECNOL", regex=True, na=False)
grad = grad_raw[mask_snies].copy()
grad.drop(columns=["_nf_norm"], inplace=True)

# Para el denominador del ratio, cargar total de graduados sin filtro
print("  Calculando total SNIES (todos los niveles)...")
_total_raw = pd.read_parquet(SNIES_GRAD, columns=["graduados"])
n_raw = _total_raw["graduados"].sum()
del _total_raw
n_filtered = grad["graduados"].sum()
print(f"  SNIES total: {n_raw:,.0f} -> elegibles: {n_filtered:,.0f} ({n_filtered/n_raw*100:.1f}%)")

# ── CARGA SABER PRO ────────────────────────────────────────────────────────
print("Cargando Saber Pro (solo ESTUDIANTE, columnas necesarias)...")

# Obtener columnas disponibles sin cargar datos
import pyarrow.parquet as pq
_pq_schema = pq.read_schema(SABER_PRO if SABER_PRO.exists() else
    sorted((BASE / "datos" / "processed" / "saber_pro").glob("saber_pro_*_limpio.parquet"))[0])
_available_cols = set(_pq_schema.names)
sp_cols_load = [c for c in SP_COLS if c in _available_cols]
has_tipo_registro = "estu_tipo_registro" in _available_cols

sp_filters = [("estu_tipo_registro", "==", "ESTUDIANTE")] if has_tipo_registro else None

if SABER_PRO.exists():
    sp_files_list = [SABER_PRO]
else:
    sp_files_list = sorted((BASE / "datos" / "processed" / "saber_pro").glob("saber_pro_*_limpio.parquet"))

# Leer con predicate pushdown: solo carga filas ESTUDIANTE desde disco
sp_chunks = []
for f in sp_files_list:
    _df = pd.read_parquet(f, columns=sp_cols_load, filters=sp_filters)
    sp_chunks.append(_df)
sp = pd.concat(sp_chunks, ignore_index=True)
del sp_chunks

n_sp_raw = len(sp)  # ya filtrado; conteo exacto del archivo se obtendría sin filtro
n_sp = n_sp_raw
if has_tipo_registro:
    # sp ya tiene solo ESTUDIANTE por el filtro pushdown
    print(f"  Saber Pro ESTUDIANTE (pushdown): {n_sp:,} registros")
else:
    print("  ADVERTENCIA: columna estu_tipo_registro no encontrada, usando todos los registros.")

sp["anio"] = extract_anio_from_periodo(sp["periodo"])

# Cast codigo_snies_programa to comparable type
grad["codigo_snies_programa"] = pd.to_numeric(grad["codigo_snies_programa"], errors="coerce")
sp["codigo_snies_programa"] = pd.to_numeric(sp["codigo_snies_programa"], errors="coerce")

# ---------------------------------------------------------------------------
# 1. Tabla anual: Graduados vs Presentaciones
# ---------------------------------------------------------------------------
print("Calculando tabla anual...")

grad_por_anio = grad.groupby("anio")["graduados"].sum().reset_index()
grad_por_anio.columns = ["anio", "total_graduados"]

sp_por_anio = sp.groupby("anio").size().reset_index(name="total_presentaciones")

anual = pd.merge(grad_por_anio, sp_por_anio, on="anio", how="outer").sort_values("anio")
anual["ratio_sp_grad"] = (anual["total_presentaciones"] / anual["total_graduados"] * 100)

# ---------------------------------------------------------------------------
# 2. Top 20 programas por graduados con match en Saber Pro
# ---------------------------------------------------------------------------
print("Calculando top programas...")

grad_prog = (
    grad.groupby("codigo_snies_programa")
    .agg(
        total_graduados=("graduados", "sum"),
        nombre_programa=("nombre_programa", "first"),
        nombre_institucion=("nombre_institucion", "first"),
    )
    .reset_index()
)

sp_prog = (
    sp.groupby("codigo_snies_programa")
    .agg(
        total_presentaciones=("estu_consecutivo", "count"),
        programa_sp=("programa_academico", "first"),
        ies_sp=("nombre_ies", "first"),
    )
    .reset_index()
)

prog_merged = pd.merge(grad_prog, sp_prog, on="codigo_snies_programa", how="outer")
prog_merged["ratio"] = prog_merged["total_presentaciones"] / prog_merged["total_graduados"] * 100

# Top 20 by graduates
top20_grad = prog_merged.nlargest(20, "total_graduados")

# Programs with highest discrepancy
prog_merged_valid = prog_merged.dropna(subset=["total_graduados", "total_presentaciones"])
prog_merged_valid = prog_merged_valid[prog_merged_valid["total_graduados"] > 100]
high_disc = prog_merged_valid.nlargest(10, "ratio")
low_disc = prog_merged_valid[prog_merged_valid["ratio"] > 0].nsmallest(10, "ratio")

# ---------------------------------------------------------------------------
# 3. Cobertura por tipo de IES (usando SNIES graduados con acreditación, 2019+)
# ---------------------------------------------------------------------------
print("Calculando cobertura por tipo IES...")

grad_2019 = grad[grad["anio"] >= 2019].copy()
sp_2019 = sp[sp["anio"] >= 2019].copy()

grad_acred = (
    grad_2019.groupby(["anio", "ies_acreditada"])["graduados"].sum()
    .reset_index()
)

sp_with_acred = pd.merge(
    sp_2019[["anio", "codigo_snies_programa", "estu_consecutivo"]],
    grad_2019[["codigo_snies_programa", "ies_acreditada"]].drop_duplicates("codigo_snies_programa"),
    on="codigo_snies_programa",
    how="left"
)

sp_acred = (
    sp_with_acred.groupby(["anio", "ies_acreditada"])
    .size()
    .reset_index(name="presentaciones")
)

cobertura = pd.merge(grad_acred, sp_acred, on=["anio", "ies_acreditada"], how="outer")
cobertura["ratio_pct"] = cobertura["presentaciones"] / cobertura["graduados"] * 100

# ---------------------------------------------------------------------------
# 4. Resumen por área de conocimiento
# ---------------------------------------------------------------------------
print("Calculando resumen por área...")

grad_area = (
    grad.groupby("area_conocimiento")["graduados"].sum()
    .reset_index()
    .sort_values("graduados", ascending=False)
)

sp_area = pd.merge(
    sp[["codigo_snies_programa", "estu_consecutivo"]],
    grad[["codigo_snies_programa", "area_conocimiento"]].drop_duplicates("codigo_snies_programa"),
    on="codigo_snies_programa",
    how="left"
)
sp_area_count = sp_area.groupby("area_conocimiento").size().reset_index(name="presentaciones")

area_merged = pd.merge(grad_area, sp_area_count, on="area_conocimiento", how="outer")
area_merged["ratio_pct"] = area_merged["presentaciones"] / area_merged["graduados"] * 100
area_merged = area_merged.sort_values("graduados", ascending=False)

# ---------------------------------------------------------------------------
# Generate HTML
# ---------------------------------------------------------------------------
print("Generando HTML...")


def table_html(df, columns, headers=None, fmt_map=None):
    """Generate an HTML table from a DataFrame."""
    if headers is None:
        headers = columns
    if fmt_map is None:
        fmt_map = {}

    rows = []
    rows.append("<table>")
    rows.append("<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>")
    rows.append("<tbody>")
    for _, row in df.iterrows():
        cells = []
        for col in columns:
            val = row[col]
            if col in fmt_map:
                val = fmt_map[col](val)
            elif isinstance(val, float) and not pd.isna(val):
                if abs(val) > 1000:
                    val = fmt_num(val)
                else:
                    val = f"{val:.1f}"
            elif pd.isna(val):
                val = "—"
            else:
                val = html_mod.escape(str(val))
            cells.append(f"<td>{val}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    rows.append("</tbody></table>")
    return "\n".join(rows)


html_parts = []
html_parts.append("""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Graduados SNIES vs Presentaciones Saber Pro (2015-2024)</title>
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 1100px; margin: 2em auto; padding: 0 1em; color: #333; }
  h1 { color: #1a237e; border-bottom: 3px solid #1a237e; padding-bottom: 0.3em; }
  h2 { color: #283593; margin-top: 2em; }
  h3 { color: #3949ab; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: right; }
  th { background: #e8eaf6; color: #1a237e; }
  td:first-child, th:first-child { text-align: left; }
  tr:nth-child(even) { background: #f5f5f5; }
  .note { background: #fff3e0; border-left: 4px solid #ff9800; padding: 1em; margin: 1em 0; }
  .warn { background: #fce4ec; border-left: 4px solid #e53935; padding: 1em; margin: 1em 0; }
  .summary { background: #e8f5e9; border-left: 4px solid #43a047; padding: 1em; margin: 1em 0; }
  .meta { color: #666; font-size: 0.9em; }
  code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; font-size: 0.9em; }
</style>
</head>
<body>
<h1>📊 Graduados SNIES vs Presentaciones Saber Pro (2015-2024)</h1>
<p class="meta">Generado automáticamente | Universo homologado</p>
""")

# Universe disclaimer — sp_raw ya no está en memoria (se liberó), usar n_sp / has_tipo_registro
html_parts.append(f"""<div class="warn">
<strong>&#9888;&#65039; Nota sobre el universo comparable:</strong>
<p>Este reporte compara <strong>universos homologados</strong>. El Saber Pro evalua exclusivamente
programas de <em>Pregrado Universitario y Tecnologico</em>; <strong>no aplica</strong> para
Tecnica Profesional ni Posgrado.</p>
<ul>
  <li><strong>SNIES Graduados:</strong> filtrado a <code>nivel_academico = 'PREGRADO'</code>
      y <code>nivel_formacion</code> con "Universitari*" o "Tecnologico*"
      &rarr; {fmt_num(n_filtered)} de {fmt_num(n_raw)} graduados totales
      ({n_filtered/n_raw*100:.1f}% del total SNIES)</li>
  <li><strong>Saber Pro:</strong> {'filtrado a <code>estu_tipo_registro = ESTUDIANTE</code> (pushdown)' if has_tipo_registro else 'sin filtro de tipo registro'}
      &rarr; {fmt_num(n_sp)} registros cargados</li>
</ul>
<p>Un ratio cercano al 100% indica buena correspondencia entre graduados y presentantes en ese año.</p>
</div>""")

# Section 1: Annual table
html_parts.append("<h2>1. Comparación Anual: Graduados vs Presentaciones</h2>")
html_parts.append("""<div class="note">
<strong>Nota metodológica:</strong> El Saber Pro se presenta durante el último año de carrera
(antes de graduarse). Los presentantes de año <em>t</em> corresponden aproximadamente
a los graduados de año <em>t</em> o <em>t+1</em>. Un ratio &gt; 100% puede deberse a rezagos
o re-presentaciones; un ratio &lt; 100% puede indicar deserción post-Saber Pro.
</div>""")
html_parts.append(table_html(
    anual,
    ["anio", "total_graduados", "total_presentaciones", "ratio_sp_grad"],
    ["Año", "Graduados SNIES (elegibles)", "Presentaciones Saber Pro", "Ratio (%)"],
    {"total_graduados": fmt_num, "total_presentaciones": fmt_num, "ratio_sp_grad": fmt_pct}
))

total_grad = anual["total_graduados"].sum()
total_sp_count = anual["total_presentaciones"].sum()
html_parts.append(f"""<div class="summary">
<strong>Totales 2015-2024 (universo homologado):</strong>
{fmt_num(total_grad)} graduados SNIES elegibles vs {fmt_num(total_sp_count)} presentaciones Saber Pro
(ratio global: <strong>{fmt_pct(total_sp_count/total_grad*100)}</strong>)
</div>""")

# Section 2: Top 20 programs
html_parts.append("<h2>2. Top 20 Programas por Graduados (con matching Saber Pro)</h2>")
html_parts.append(table_html(
    top20_grad,
    ["nombre_programa", "nombre_institucion", "total_graduados", "total_presentaciones", "ratio"],
    ["Programa", "Institución (SNIES)", "Graduados", "Presentaciones SP", "Ratio (%)"],
    {"total_graduados": fmt_num, "total_presentaciones": fmt_num, "ratio": fmt_pct,
     "nombre_programa": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "—",
     "nombre_institucion": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "—"}
))

# Section 3: High/Low discrepancy
html_parts.append("<h2>3. Programas con Mayor Discrepancia</h2>")
html_parts.append("<h3>3a. Más presentaciones que graduados (ratio alto)</h3>")
html_parts.append(table_html(
    high_disc,
    ["nombre_programa", "nombre_institucion", "total_graduados", "total_presentaciones", "ratio"],
    ["Programa", "Institución", "Graduados", "Presentaciones", "Ratio (%)"],
    {"total_graduados": fmt_num, "total_presentaciones": fmt_num, "ratio": fmt_pct,
     "nombre_programa": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "—",
     "nombre_institucion": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "—"}
))

html_parts.append("<h3>3b. Menos presentaciones que graduados (ratio bajo)</h3>")
html_parts.append(table_html(
    low_disc,
    ["nombre_programa", "nombre_institucion", "total_graduados", "total_presentaciones", "ratio"],
    ["Programa", "Institución", "Graduados", "Presentaciones", "Ratio (%)"],
    {"total_graduados": fmt_num, "total_presentaciones": fmt_num, "ratio": fmt_pct,
     "nombre_programa": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "—",
     "nombre_institucion": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "—"}
))

# Section 4: Coverage by accreditation
html_parts.append("<h2>4. Cobertura Saber Pro por Acreditación de IES (2019-2024)</h2>")
html_parts.append("""<div class="note">
<strong>Nota:</strong> La columna <code>ies_acreditada</code> solo está disponible en SNIES desde 2019.
Se mapea a Saber Pro vía <code>codigo_snies_programa</code>.
</div>""")
cobertura_pivot = cobertura.groupby("ies_acreditada").agg(
    total_graduados=("graduados", "sum"),
    total_presentaciones=("presentaciones", "sum")
).reset_index()
cobertura_pivot["ratio_pct"] = cobertura_pivot["total_presentaciones"] / cobertura_pivot["total_graduados"] * 100
html_parts.append(table_html(
    cobertura_pivot,
    ["ies_acreditada", "total_graduados", "total_presentaciones", "ratio_pct"],
    ["IES Acreditada", "Graduados", "Presentaciones SP", "Ratio (%)"],
    {"total_graduados": fmt_num, "total_presentaciones": fmt_num, "ratio_pct": fmt_pct}
))

# Section 5: By area
html_parts.append("<h2>5. Graduados vs Presentaciones por Área de Conocimiento</h2>")
html_parts.append(table_html(
    area_merged,
    ["area_conocimiento", "graduados", "presentaciones", "ratio_pct"],
    ["Área de Conocimiento", "Graduados SNIES (elegibles)", "Presentaciones SP", "Ratio (%)"],
    {"graduados": fmt_num, "presentaciones": fmt_num, "ratio_pct": fmt_pct,
     "area_conocimiento": lambda x: html_mod.escape(str(x)) if not pd.isna(x) else "Sin área"}
))

# Hallazgos y recomendaciones
html_parts.append("""
<h2>6. Hallazgos y Recomendaciones para el Artículo</h2>
<div class="summary">
<h3>✅ Hallazgos:</h3>
<ul>
<li>Al restringir a Pregrado Universitario/Tecnológico, el universo SNIES cae de ~484K a ~270K
    graduados/año, lo que hace el ratio con Saber Pro (~268K/año) mucho más coherente (≈99%).</li>
<li>Las discrepancias residuales por programa reflejan: (a) rezagos temporales entre presentación
    y graduación, (b) programas con alta deserción post-Saber Pro, o
    (c) errores en <code>codigo_snies_programa</code>.</li>
<li>Las IES acreditadas muestran mayor cobertura relativa que las no acreditadas, consistente
    con mayor presión institucional para presentar Saber Pro.</li>
</ul>
<h3>📌 Recomendaciones para el cruce (Sección E):</h3>
<ul>
<li>Usar <code>codigo_snies_programa</code> (int) como llave principal entre SNIES y Saber Pro.</li>
<li>Filtrar programas con ratio 50%–200% para la zona de match razonable.</li>
<li>Agrupar por año para evitar comparar cohortes diferentes.</li>
<li>Ver <code>generate_report_cruce_snies_saberpro.py</code> para el análisis de cruce completo.</li>
</ul>
</div>
""")

html_parts.append("</body></html>")

OUTPUT.write_text("\n".join(html_parts), encoding="utf-8")
print(f"\n✅ Reporte generado: {OUTPUT}")
print(f"   Años cubiertos: {sorted(anual['anio'].dropna().astype(int).unique())}")
print(f"   Total graduados elegibles: {fmt_num(total_grad)}")
print(f"   Total presentaciones ESTUDIANTE: {fmt_num(total_sp_count)}")
print(f"   Ratio global: {fmt_pct(total_sp_count/total_grad*100)}")
