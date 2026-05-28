import json
import copy
from pathlib import Path


SRC = Path("notebooks/sprint_7_acp_cluster.ipynb")
OUT = Path("notebooks/sprint_7_acp_cluster_corregido.ipynb")
BACKUP_DIR = Path("notebooks/backup")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def lines(text: str):
    return [line + ("\n" if not line.endswith("\n") else "") for line in text.split("\n")]


def cell_text(cell):
    return "".join(cell.get("source", []))


nb = json.loads(SRC.read_text(encoding="utf-8"))
nb_out = copy.deepcopy(nb)

# Guardar copia exacta del origen para trazabilidad.
backup_path = BACKUP_DIR / "sprint_7_acp_cluster_original_before_corregido.ipynb"
backup_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")

modified = 0

# Actualizar titulo para que quede claro que es una version corregida.
for cell in nb_out["cells"]:
    if cell.get("cell_type") == "markdown" and "# Sprint 7: Analisis de Componentes Principales" in cell_text(cell):
        txt = cell_text(cell)
        txt = txt.replace(
            "# Sprint 7: Analisis de Componentes Principales (ACP) y Clustering de IES (Issue 7.2)",
            "# Sprint 7: ACP y Clustering de IES — versión corregida de perfiles (Issue 7.2)",
        )
        txt += "\n\n> **Corrección incorporada:** la sección 8 separa desempeño académico, escala institucional y acreditación para evitar interpretaciones engañosas por escalas, imputación y variables binarias.\n"
        cell["source"] = lines(txt)
        modified += 1
        break

section8_md = """## 8. Análisis corregido de perfiles por cluster

La versión original mezclaba en un mismo gráfico variables con escalas y naturalezas distintas: puntajes de Saber Pro, conteos institucionales, matrícula/graduados y acreditación binaria. Esa mezcla hacía que algunas lecturas fueran confusas.

En esta versión corregida se separan tres dimensiones:

1. **Desempeño académico:** puntajes y proporción P75+ se comparan con **z-score** y mediana por cluster para tener una escala común.
2. **Escala institucional:** `n_presentaciones`, `total_matriculados` y `total_graduados` se resumen principalmente por **media** —como indicador de volumen promedio del cluster— y se visualizan también con transformación `log1p` para reducir el efecto de IES extremadamente grandes.
3. **Acreditación:** al ser una variable binaria, no se interpreta con mediana. Se reporta como **proporción de IES acreditadas** por cluster.

> Nota: cuando matrícula/graduados se imputan con la mediana global, la mediana por cluster puede empatar artificialmente. Por eso aquí se reportan media, mediana, suma y distribución logarítmica, y la interpretación de escala se apoya especialmente en la media y los boxplots log.
"""

profiles_code = """# ============================================================
# 8A. Perfiles corregidos por cluster
# ============================================================
# Separar variables por naturaleza evita comparar peras con manzanas.
# - Academicas: z-score + mediana por cluster.
# - Escala institucional: media/mediana/suma, con graficos log1p.
# - Acreditacion: proporcion de IES acreditadas.

academic_vars = [
    'puntaje_global', 'punt_razona_cuantitativa',
    'punt_lectura_critica', 'punt_ingles', 'prop_p75_plus'
]

scale_vars = ['n_presentaciones', 'total_matriculados', 'total_graduados']

# ---------- Desempeño académico en z-score ----------
features_numeric = features_ies.drop(columns=['cluster'], errors='ignore').copy()
stds = features_numeric.std().replace(0, np.nan)
z_scores = (features_numeric - features_numeric.mean()) / stds
z_scores['cluster'] = features_ies['cluster']

cluster_z_profiles = z_scores.groupby('cluster')[academic_vars].median().round(3)

print("\\n8A. Perfil académico por cluster (medianas de z-score):")
display(cluster_z_profiles)

# ---------- Escala institucional: media, mediana y suma ----------
scale_profiles = features_ies.groupby('cluster')[scale_vars].agg(['sum', 'mean', 'median', 'std', 'count']).round(2)
scale_profiles.columns = ['_'.join(col).strip() for col in scale_profiles.columns]

print("\\n8B. Perfil de escala institucional por cluster (matrícula/graduados por media, más mediana/suma):")
display(scale_profiles)

# ---------- Acreditación: proporción ----------
acred_profiles = features_ies.groupby('cluster')['es_acreditada'].agg(
    n_ies='count',
    n_acreditadas='sum',
    prop_acreditadas='mean'
).round(3)
acred_profiles['porc_acreditadas'] = (acred_profiles['prop_acreditadas'] * 100).round(1)

print("\\n8C. Acreditación por cluster (proporción, no mediana):")
display(acred_profiles)

# ---------- Tabla integrada para exportación ----------
perfiles_corregidos = pd.concat(
    [
        cluster_z_profiles.add_prefix('z_median_'),
        scale_profiles,
        acreditacion_profiles if False else acred_profiles
    ],
    axis=1
)

fecha = datetime.now().strftime("%Y%m%d")
perfiles_corregidos.to_csv(ARTIFACTS_DIR / 'metricas' / f'perfiles_clusters_corregidos_{fecha}.csv')
cluster_z_profiles.to_csv(ARTIFACTS_DIR / 'metricas' / f'perfiles_clusters_zscore_academico_{fecha}.csv')
scale_profiles.to_csv(ARTIFACTS_DIR / 'metricas' / f'perfiles_clusters_escala_media_{fecha}.csv')
acred_profiles.to_csv(ARTIFACTS_DIR / 'metricas' / f'perfiles_clusters_acreditacion_{fecha}.csv')

print("\\nArchivos de perfiles corregidos exportados en artifacts/metricas/")
"""

plots_code = """# ============================================================
# 8B. Visualizaciones corregidas de perfiles
# ============================================================
cluster_colors = sns.color_palette('Set2', n_colors=int(K_OPTIMO))
fecha = datetime.now().strftime("%Y%m%d")

# ---------- 1) Desempeño académico: z-score ----------
fig, axes = plt.subplots(1, len(academic_vars), figsize=(5 * len(academic_vars), 5), sharey=True)
if len(academic_vars) == 1:
    axes = [axes]

for idx, feat in enumerate(academic_vars):
    vals = cluster_z_profiles[feat]
    axes[idx].bar(vals.index.astype(str), vals.values, color=cluster_colors, edgecolor='black')
    axes[idx].axhline(0, color='gray', linestyle='--', linewidth=1)
    axes[idx].set_title(feat.replace('_', ' ').title(), fontsize=11, fontweight='bold')
    axes[idx].set_xlabel('Cluster')
    axes[idx].set_ylabel('Mediana z-score' if idx == 0 else '')
    axes[idx].grid(axis='y', alpha=0.3)

plt.suptitle('Perfil académico por cluster (medianas de z-score)', fontsize=15, fontweight='bold', y=1.05)
plt.tight_layout()
plt.savefig(ARTIFACTS_DIR / 'visualizaciones' / f'perfiles_clusters_zscore_desempeno_{fecha}.png', dpi=150, bbox_inches='tight')
plt.show()

# ---------- 2) Escala institucional: medias ----------
scale_means = features_ies.groupby('cluster')[scale_vars].mean()

fig, axes = plt.subplots(1, len(scale_vars), figsize=(5 * len(scale_vars), 5))
if len(scale_vars) == 1:
    axes = [axes]

for idx, feat in enumerate(scale_vars):
    vals = scale_means[feat]
    axes[idx].bar(vals.index.astype(str), vals.values, color=cluster_colors, edgecolor='black')
    axes[idx].set_title(f'Media de {feat}'.replace('_', ' ').title(), fontsize=11, fontweight='bold')
    axes[idx].set_xlabel('Cluster')
    axes[idx].set_ylabel('Media')
    axes[idx].grid(axis='y', alpha=0.3)

plt.suptitle('Escala institucional por cluster (matrícula/graduados por media)', fontsize=15, fontweight='bold', y=1.05)
plt.tight_layout()
plt.savefig(ARTIFACTS_DIR / 'visualizaciones' / f'perfiles_clusters_escala_media_{fecha}.png', dpi=150, bbox_inches='tight')
plt.show()

# ---------- 3) Escala institucional: distribución log1p ----------
scale_long = features_ies.reset_index()[['cluster'] + scale_vars].melt(
    id_vars='cluster', var_name='variable', value_name='valor'
)
scale_long['log1p_valor'] = np.log1p(scale_long['valor'])

plt.figure(figsize=(12, 6))
sns.boxplot(data=scale_long, x='variable', y='log1p_valor', hue='cluster', palette='Set2')
plt.title('Distribución de escala institucional por cluster (log1p)', fontsize=14, fontweight='bold')
plt.xlabel('Variable')
plt.ylabel('log1p(valor)')
plt.grid(axis='y', alpha=0.3)
plt.legend(title='Cluster')
plt.tight_layout()
plt.savefig(ARTIFACTS_DIR / 'visualizaciones' / f'perfiles_clusters_escala_boxplot_log_{fecha}.png', dpi=150, bbox_inches='tight')
plt.show()

# ---------- 4) Acreditación: proporción ----------
plt.figure(figsize=(7, 5))
vals = acred_profiles['porc_acreditadas']
bars = plt.bar(vals.index.astype(str), vals.values, color=cluster_colors, edgecolor='black')
plt.title('Porcentaje de IES acreditadas por cluster', fontsize=14, fontweight='bold')
plt.xlabel('Cluster')
plt.ylabel('% IES acreditadas')
plt.ylim(0, max(100, vals.max() + 10))
plt.grid(axis='y', alpha=0.3)
for bar, val in zip(bars, vals.values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.1f}%', ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig(ARTIFACTS_DIR / 'visualizaciones' / f'perfiles_clusters_acreditacion_prop_{fecha}.png', dpi=150, bbox_inches='tight')
plt.show()
"""

interpretation_md = """### Interpretación corregida de perfiles

- **Desempeño académico:** el perfil en z-score permite comparar puntajes y P75+ en una escala común. Valores positivos indican desempeño por encima del promedio general de IES; valores negativos indican desempeño por debajo.
- **Escala institucional:** matrícula y graduados se interpretan mejor con la **media por cluster** y con el boxplot `log1p`, porque la mediana puede quedar empatada cuando hay imputación con mediana global o distribuciones muy asimétricas.
- **Acreditación:** no debe leerse con mediana porque es binaria. La lectura correcta es la **proporción de IES acreditadas** en cada cluster.
- Si un cluster muestra bajo desempeño académico pero mayor matrícula/graduados promedio, la conclusión no es que “sea mejor”, sino que agrupa IES de mayor escala con resultados Saber Pro relativamente más críticos.
"""

audit_code = """# Identificar el cluster con peor desempeño académico robusto
# Usamos la mediana del z-score de puntaje_global, no el promedio crudo.
cluster_worst = cluster_z_profiles['puntaje_global'].idxmin()
cluster_worst_df = features_ies[features_ies['cluster'] == cluster_worst].copy()

print('='*70)
print(f'AUDITORIA DETALLADA: CLUSTER {cluster_worst} (DESEMPENO CRITICO)')
print('='*70)
print(f'Total de IES en Cluster {cluster_worst}: {len(cluster_worst_df)}')
print(f'Estadisticas del puntaje global en el Cluster {cluster_worst}:')
print(cluster_worst_df['puntaje_global'].describe())

print(f'\\n--- IES con puntaje MAS BAJO (Top 10) ---')
display(cluster_worst_df.nsmallest(10, 'puntaje_global')[
    ['puntaje_global', 'punt_lectura_critica', 'punt_ingles', 'n_presentaciones', 'total_matriculados', 'total_graduados', 'es_acreditada']])

print(f'\\n--- IES con puntaje MAS ALTO del Cluster {cluster_worst} (Top 5) ---')
display(cluster_worst_df.nlargest(5, 'puntaje_global')[
    ['puntaje_global', 'punt_lectura_critica', 'punt_ingles', 'n_presentaciones', 'total_matriculados', 'total_graduados', 'es_acreditada']])
"""

cells = nb_out["cells"]
for i, cell in enumerate(cells):
    txt = cell_text(cell)
    if cell.get("cell_type") == "markdown" and "## 8. Analisis de Perfiles por Cluster" in txt:
        cell["source"] = lines(section8_md)
        modified += 1
        # Reemplazar las dos celdas de código inmediatamente siguientes.
        cells[i + 1]["source"] = lines(profiles_code)
        cells[i + 1]["execution_count"] = None
        cells[i + 1]["outputs"] = []
        cells[i + 2]["source"] = lines(plots_code)
        cells[i + 2]["execution_count"] = None
        cells[i + 2]["outputs"] = []
        # Insertar interpretación después del bloque de plots si no existe.
        cells.insert(i + 3, {
            "cell_type": "markdown",
            "metadata": {},
            "source": lines(interpretation_md),
        })
        modified += 3
        break

for cell in cells:
    txt = cell_text(cell)
    if cell.get("cell_type") == "code" and "cluster_worst = features_ies.groupby('cluster')['puntaje_global'].mean().idxmin()" in txt:
        cell["source"] = lines(audit_code)
        cell["execution_count"] = None
        cell["outputs"] = []
        modified += 1
        break

# Limpiar outputs del notebook completo para que la versión corregida se ejecute limpia.
for cell in cells:
    if cell.get("cell_type") == "code":
        cell["execution_count"] = None
        cell["outputs"] = []

OUT.write_text(json.dumps(nb_out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Notebook corregido creado: {OUT}")
print(f"Backup del original: {backup_path}")
print(f"Celdas/secciones modificadas: {modified}")