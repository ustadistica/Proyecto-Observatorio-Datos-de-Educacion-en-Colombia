# ============================================================
# ANÁLISIS DESCRIPTIVO SNIES
# ============================================================

# ============================================================
# IMPORTAR LIBRERÍAS
# ============================================================

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

import plotly.express as px
import plotly.graph_objects as go

import warnings
warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

sns.set_theme(style="whitegrid")

plt.rcParams["figure.figsize"] = (12, 6)

# ============================================================
# CARGAR DATASET
# ============================================================

print("\nCargando dataset...\n")

df = pd.read_parquet("datos/processed/snies/graduados_final.parquet")

print("Dataset cargado correctamente")
print(f"Filas: {len(df):,}")
print(f"Columnas: {len(df.columns):,}")

# ============================================================
# LIMPIEZA BÁSICA EXTRA
# ============================================================

df["graduados"] = (
    pd.to_numeric(df["graduados"], errors="coerce")
    .fillna(0)
    .astype("Int64")
)

# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

print("\n" + "="*60)
print("INFORMACIÓN GENERAL")
print("="*60)

print(df.info())

# ============================================================
# MATRÍCULA TOTAL
# ============================================================

print("\n" + "="*60)
print("graduados TOTALES")
print("="*60)

print(f"\nTotal graduados: {df['graduados'].sum():,}")

# ============================================================
# 1. TENDENCIA TEMPORAL
# ============================================================

print("\nGenerando tendencia temporal...")

anio_df = (
    df.groupby("anio")["graduados"]
    .sum()
    .reset_index()
    .sort_values("anio")
)

fig = px.line(
    anio_df,
    x="anio",
    y="graduados",
    markers=True,
    text="graduados",
    title="Evolución temporal de los graduados en educación superior en Colombia (2015–2024)"
)

fig.update_traces(
    texttemplate='%{text:,.0f}',
    textposition='top center',
    line=dict(width=4),
    marker=dict(size=10)
)

fig.update_layout(
    title_x=0.5,
    xaxis_title="Año",
    yaxis_title="graduados",
    template="plotly_white",
    hovermode="x unified",
    font=dict(size=14)
)

fig.update_yaxes(
    tickformat=","
)

fig.show(renderer="browser")

plt.figure(figsize=(14,7))

sns.lineplot(
    data=anio_df,
    x="anio",
    y="graduados",
    marker="o",
    linewidth=3
)

for x, y in zip(
    anio_df["anio"],
    anio_df["graduados"]
):

    plt.text(
        x,
        y + 15000,
        f"{y:,.0f}",
        ha="center",
        fontsize=10,
        fontweight="bold"
    )

plt.title(
    "Evolución de graduados por año",
    fontsize=20,
    fontweight="bold"
)

plt.xlabel(
    "Año",
    fontsize=14
)

plt.ylabel(
    "graduados",
    fontsize=14
)

plt.ticklabel_format(
    style='plain',
    axis='y'
)

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(
        lambda x, _: f'{int(x):,}'
    )
)

plt.grid(
    alpha=0.3,
    linestyle="--"
)

plt.tight_layout()

plt.savefig("artifacts/visualizaciones/Tendencia_temporal_graduados.png", dpi=300, bbox_inches="tight")
plt.show()

# ============================================================
# 2. MATRÍCULA POR GÉNERO
# ============================================================

print("\nGenerando análisis por género...")

# Filtrar categorías pequeñas
genero_df = (
    df[
        ~df["genero"].isin([
            "no binario",
            "trans"
        ])
    ]
    .groupby("genero")["graduados"]
    .sum()
    .reset_index()
    .sort_values(by="graduados", ascending=False)
)

# ============================================================
# PLOTLY
# ============================================================

fig = px.bar(
    genero_df,
    x="genero",
    y="graduados",
    title="Distribución de los graduados por género en educación superior en Colombia (2015–2024)",
    text="graduados",
    color="genero"
)

# Formato bonito de etiquetas
fig.update_traces(
    texttemplate='%{text:,}',
    textposition='outside'
)

# Mejorar diseño
fig.update_layout(
    xaxis_title="Género",
    yaxis_title="graduados",
    title_x=0.5,
    showlegend=False
)

fig.show(renderer="browser")
fig.show()

# ============================================================
# SEABORN / MATPLOTLIB
# ============================================================

plt.figure(figsize=(10,6))

ax = sns.barplot(
    data=genero_df,
    x="genero",
    y="graduados"
)

# Agregar etiquetas encima de las barras
for p in ax.patches:

    valor = int(p.get_height())

    ax.annotate(
        f'{valor:,}',
        (
            p.get_x() + p.get_width() / 2,
            p.get_height()
        ),
        ha='center',
        va='bottom',
        fontsize=11,
        fontweight='bold'
    )

# Quitar notación científica
plt.ticklabel_format(style='plain', axis='y')

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, _: f'{int(x):,}')
)

# Títulos y estilo
plt.title(
    "Distribución de los graduados por género en educación superior en Colombia (2015–2024)",
    fontsize=16,
    fontweight='bold'
)

plt.xlabel("Género", fontsize=12)
plt.ylabel("graduados", fontsize=12)

plt.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()

plt.savefig("artifacts/visualizaciones/graduados_genero.png", dpi=300, bbox_inches="tight")
plt.show()


# ============================================================
# 3. MATRÍCULA POR SECTOR
# ============================================================

print("\nGenerando análisis por sector...")

sector_df = (
    df.groupby("sector")["graduados"]
    .sum()
    .reset_index()
    .sort_values(by="graduados", ascending=False)
)

# ============================================================
# PLOTLY
# ============================================================

fig = px.pie(
    sector_df,
    names="sector",
    values="graduados",
    title="Participación de los graduados según sector en Colombia (2015–2024)",
    hole=0.4
)

# Mostrar porcentaje y valor
fig.update_traces(
    textinfo='percent+label',
    hovertemplate=
    "<b>%{label}</b><br>" +
    "graduados: %{value:,}<br>" +
    "Porcentaje: %{percent}"
)

fig.update_layout(
    title_x=0.5
)

fig.show(renderer="browser")
fig.show()

# ============================================================
# SEABORN / MATPLOTLIB
# ============================================================

plt.figure(figsize=(8,6))

ax = sns.barplot(
    data=sector_df,
    x="sector",
    y="graduados"
)

# Etiquetas encima
for p in ax.patches:

    valor = int(p.get_height())

    ax.annotate(
        f'{valor:,}',
        (
            p.get_x() + p.get_width()/2,
            p.get_height()
        ),
        ha='center',
        va='bottom',
        fontsize=11,
        fontweight='bold'
    )

# Formato números reales
plt.ticklabel_format(style='plain', axis='y')

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, _: f'{int(x):,}')
)

plt.title(
    "graduados por sector",
    fontsize=16,
    fontweight='bold'
)

plt.xlabel("Sector", fontsize=12)
plt.ylabel("graduados", fontsize=12)

plt.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()

plt.savefig("artifacts/visualizaciones/graduados_sector.png", dpi=300, bbox_inches="tight")
plt.show()

# ============================================================
# 4. MATRÍCULA POR ÁREA DE CONOCIMIENTO
# ============================================================

print("\nGenerando análisis por áreas...")

# Eliminar categorías pequeñas o raras
area_df = (
    df[
        ~df["area_conocimiento"].isin([
            "sin informacion",
            "sin clasificar"
        ])
    ]
    .groupby("area_conocimiento")["graduados"]
    .sum()
    .reset_index()
    .sort_values(by="graduados", ascending=False)
)

# ============================================================
# PLOTLY
# ============================================================

fig = px.bar(
    area_df,
    x="graduados",
    y="area_conocimiento",
    orientation="h",
    title="Distribución de los graduados por área de conocimiento en Colombia (2015–2024)",
    text="graduados",
    color="graduados",
)

# Etiquetas bonitas
fig.update_traces(
    texttemplate='%{text:,}',
    textposition='outside'
)

# Mejorar diseño
fig.update_layout(
    title_x=0.5,
    xaxis_title="graduados",
    yaxis_title="Área de conocimiento",
    showlegend=False
)

fig.show(renderer="browser")
fig.show()

# ============================================================
# SEABORN / MATPLOTLIB
# ============================================================

plt.figure(figsize=(14,8))

ax = sns.barplot(
    data=area_df,
    y="area_conocimiento",
    x="graduados"
)

# Agregar etiquetas
for p in ax.patches:

    valor = int(p.get_width())

    ax.annotate(
        f'{valor:,}',
        (
            p.get_width(),
            p.get_y() + p.get_height()/2
        ),
        ha='left',
        va='center',
        fontsize=10,
        fontweight='bold'
    )

# Quitar notación científica
plt.ticklabel_format(style='plain', axis='x')

plt.gca().xaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, _: f'{int(x):,}')
)

# Diseño
plt.title(
    "Distribución de los graduados por área de conocimiento en Colombia (2015–2024)",
    fontsize=16,
    fontweight='bold'
)

plt.xlabel("graduados", fontsize=12)
plt.ylabel("Área de conocimiento", fontsize=12)

plt.grid(axis='x', linestyle='--', alpha=0.4)

plt.tight_layout()

plt.savefig("artifacts/visualizaciones/graduados_area_conocimiento.png", dpi=300, bbox_inches="tight")
plt.show()

# ============================================================
# 5.MATRÍCULA POR DEPARTAMENTO
# ============================================================

print("\nGenerando análisis por departamento...")

# Top departamentos
depto_df = (
    df.groupby("depto_programa")["graduados"]
    .sum()
    .reset_index()
    .sort_values(by="graduados", ascending=False)
    .head(15)
)

# ============================================================
# PLOTLY
# ============================================================

fig = px.funnel(
    depto_df,
    x="graduados",
    y="depto_programa",
    title="Distribución territorial de los graduados por departamento en Colombia (2015–2024)"
)

# Etiquetas bonitas
fig.update_traces(
    texttemplate="%{x:,}",
    textposition="inside"
)

# Mejorar diseño
fig.update_layout(
    title_x=0.5,
    xaxis_title="graduados",
    yaxis_title="Departamento"
)

fig.show(renderer="browser")
fig.show()

# ============================================================
# SEABORN / MATPLOTLIB
# ============================================================

plt.figure(figsize=(14,8))

ax = sns.barplot(
    data=depto_df,
    y="depto_programa",
    x="graduados"
)

# Etiquetas con valores reales
for p in ax.patches:

    valor = int(p.get_width())

    ax.annotate(
        f'{valor:,}',
        (
            p.get_width(),
            p.get_y() + p.get_height()/2
        ),
        ha='left',
        va='center',
        fontsize=10,
        fontweight='bold'
    )

# Quitar notación científica
plt.ticklabel_format(style='plain', axis='x')

plt.gca().xaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, _: f'{int(x):,}')
)

# Diseño
plt.title(
    "Top departamentos por graduados",
    fontsize=16,
    fontweight='bold'
)

plt.xlabel("graduados", fontsize=12)
plt.ylabel("Departamento", fontsize=12)

plt.grid(axis='x', linestyle='--', alpha=0.4)

plt.tight_layout()

plt.savefig("artifacts/visualizaciones/graduados_genero.png", dpi=300, bbox_inches="tight")
plt.show()


# ============================================================
# 6. TOP PROGRAMAS ACADÉMICOS
# ============================================================

print("\nGenerando análisis de programas académicos...")

# Top 15 programas
programas_df = (
    df.groupby("nombre_programa")["graduados"]
    .sum()
    .reset_index()
    .sort_values(by="graduados", ascending=False)
    .head(15)
)

# ============================================================
# PLOTLY FUNNEL
# ============================================================

# Mucho más elegante y diferente a barras normales
fig = px.funnel(
    programas_df,
    x="graduados",
    y="nombre_programa",
    title="Programas con mayor número de graduados en Colombia (2015–2024)"
)

# Etiquetas bonitas
fig.update_traces(
    texttemplate="%{x:,}",
    textposition="inside"
)

# Mejorar diseño
fig.update_layout(
    title_x=0.5,
    xaxis_title="graduados",
    yaxis_title="Programa académico",
    font=dict(size=13)
)

fig.show(renderer="browser")
fig.show()

# ============================================================
# SEABORN / MATPLOTLIB ESTILO LOLLIPOP
# ============================================================

# Este gráfico se ve MUY moderno y distinto
plt.figure(figsize=(14,8))

# Ordenar de menor a mayor para estética
programas_plot = programas_df.sort_values(
    by="graduados"
)

# Líneas
plt.hlines(
    y=programas_plot["nombre_programa"],
    xmin=0,
    xmax=programas_plot["graduados"],
    linewidth=3,
    alpha=0.7
)

# Puntos
plt.plot(
    programas_plot["graduados"],
    programas_plot["nombre_programa"],
    "o",
    markersize=12
)

# Etiquetas
for i, row in programas_plot.iterrows():

    plt.text(
        row["graduados"] + 20000,
        row["nombre_programa"],
        f'{int(row["graduados"]):,}',
        va='center',
        fontsize=10,
        fontweight='bold'
    )

# Quitar notación científica
plt.ticklabel_format(style='plain', axis='x')

plt.gca().xaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, _: f'{int(x):,}')
)

# Diseño
plt.title(
    "Programas con mayor número de graduados en Colombia (2015–2024)",
    fontsize=18,
    fontweight='bold'
)

plt.xlabel("graduados", fontsize=12)
plt.ylabel("Programa académico", fontsize=12)

plt.grid(axis='x', linestyle='--', alpha=0.4)

plt.tight_layout()

plt.savefig("artifacts/visualizaciones/graduados_programa.png", dpi=300, bbox_inches="tight")
plt.show()


# ============================================================
# 7. TOP INSTITUCIONES
# ============================================================

print("\nGenerando análisis por institución...")

# Top 15 instituciones
inst_df = (
    df.groupby("nombre_institucion")["graduados"]
    .sum()
    .reset_index()
    .sort_values(by="graduados", ascending=False)
    .head(15)
)

# ============================================================
# PLOTLY SUNBURST
# ============================================================

# Este gráfico queda MUY elegante visualmente
fig = px.sunburst(
    inst_df,
    path=["nombre_institucion"],
    values="graduados",
    title="Instituciones con mayor número de graduados en Colombia (2015–2024)"
)

# Etiquetas bonitas
fig.update_traces(
    textinfo="label+percent entry"
)

# Hover personalizado
fig.update_traces(
    hovertemplate=
    "<b>%{label}</b><br>" +
    "graduados: %{value:,}<br>" +
    "Participación: %{percentEntry}"
)

# Diseño
fig.update_layout(
    title_x=0.5
)

fig.show(renderer="browser")
fig.show()

# ============================================================
# MATPLOTLIB ESTILO DOT PLOT
# ============================================================

plt.figure(figsize=(13,8))

# Ordenar para estética
inst_plot = inst_df.sort_values(
    by="graduados"
)

# Crear gráfico tipo dot plot
plt.scatter(
    inst_plot["graduados"],
    inst_plot["nombre_institucion"],
    s=350,
    alpha=0.7
)

# Líneas suaves
for i in range(len(inst_plot)):

    plt.hlines(
        y=inst_plot.iloc[i]["nombre_institucion"],
        xmin=0,
        xmax=inst_plot.iloc[i]["graduados"],
        alpha=0.3,
        linewidth=2
    )

# Etiquetas
for i, row in inst_plot.iterrows():

    plt.text(
        row["graduados"] + 20000,
        row["nombre_institucion"],
        f'{int(row["graduados"]):,}',
        va='center',
        fontsize=10,
        fontweight='bold'
    )

# Quitar notación científica
plt.ticklabel_format(style='plain', axis='x')

plt.gca().xaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, _: f'{int(x):,}')
)

# Diseño
plt.title(
    "Graduados por institución en Colombia (2015–2024)",
    fontsize=18,
    fontweight='bold'
)

plt.xlabel("graduados", fontsize=12)
plt.ylabel("Institución", fontsize=12)

plt.grid(axis='x', linestyle='--', alpha=0.4)

plt.tight_layout()

plt.savefig("artifacts/visualizaciones/graduados_instituciones.png", dpi=300, bbox_inches="tight")
plt.show()


# ============================================================
# 8. EVOLUCIÓN TEMPORAL POR ÁREA DE CONOCIMIENTO
# ============================================================

print("\nGenerando evolución temporal por área...")

# Filtrar áreas poco útiles
areas_temp = df[
    ~df["area_conocimiento"].isin([
        "sin informacion",
        "sin clasificar"
    ])
]

# Agrupar
area_year = (
    areas_temp
    .groupby(
        ["anio", "area_conocimiento"]
    )["graduados"]
    .sum()
    .reset_index()
)

# Top áreas
top_areas = (
    area_year
    .groupby("area_conocimiento")["graduados"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index
)

area_year = area_year[
    area_year["area_conocimiento"]
    .isin(top_areas)
]

# ============================================================
# GRÁFICO MEJORADO
# ============================================================

plt.figure(figsize=(16,9))

sns.set_style("whitegrid")

ax = sns.lineplot(
    data=area_year,
    x="anio",
    y="graduados",
    hue="area_conocimiento",
    marker="o",
    linewidth=3.5,
    markersize=9
)

# ============================================================
# ETIQUETAS INTELIGENTES
# ============================================================

for _, row in area_year.iterrows():

    # Ajustes manuales para evitar choques
    offset = 12000

    # Educación
    if row["area_conocimiento"] == "ciencias de la educacion":
        offset = 18000

    # Salud
    elif row["area_conocimiento"] == "ciencias de la salud":
        offset = -18000

    # Sociales
    elif row["area_conocimiento"] == "ciencias sociales y humanas":
        offset = 15000

    # Ingeniería
    elif row["area_conocimiento"] == "ingenieria, arquitectura, urbanismo y afines":
        offset = 10000

    # Economía
    elif row["area_conocimiento"] == "economia, administracion, contaduria y afines":
        offset = 16000

    plt.text(
        row["anio"],
        row["graduados"] + offset,
        f'{int(row["graduados"]):,}',
        fontsize=8,
        fontweight='bold',
        ha='center'
    )

# ============================================================
# FORMATO DE EJES
# ============================================================

plt.ticklabel_format(style='plain', axis='y')

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(
        lambda x, _: f'{int(x):,}'
    )
)

# ============================================================
# DISEÑO
# ============================================================

plt.title(
    "Evolución temporal de los graduados por área de conocimiento en Colombia (2015–2024)",
    fontsize=20,
    fontweight='bold',
    pad=20
)

plt.xlabel(
    "Año",
    fontsize=13,
    fontweight='bold'
)

plt.ylabel(
    "graduados",
    fontsize=13,
    fontweight='bold'
)

# Leyenda más limpia
plt.legend(
    title="Área de conocimiento",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    frameon=True
)

# Grid suave
plt.grid(
    linestyle='--',
    alpha=0.3
)

# Quitar bordes feos
sns.despine()

plt.tight_layout()

plt.savefig("artifacts/visualizaciones/evolucion_temporal.png", dpi=300, bbox_inches="tight")
plt.show()



# ============================================================
# BRECHA DE GÉNERO POR ÁREA DE CONOCIMIENTO
# ============================================================

print("\nGenerando brecha de género por área...")

# ============================================================
# FILTRAR SOLO HOMBRE Y MUJER
# ============================================================

brecha_df = df[
    df["genero"].isin([
        "femenino",
        "masculino"
    ])
]

# Quitar categorías basura
brecha_df = brecha_df[
    ~brecha_df["area_conocimiento"].isin([
        "sin informacion",
        "sin clasificar"
    ])
]

# ============================================================
# AGRUPAR
# ============================================================

brecha_df = (
    brecha_df
    .groupby(
        ["area_conocimiento", "genero"]
    )["graduados"]
    .sum()
    .reset_index()
)

# ============================================================
# TOP ÁREAS
# ============================================================

top_areas = (
    brecha_df
    .groupby("area_conocimiento")["graduados"]
    .sum()
    .sort_values(ascending=False)
    .head(8)
    .index
)

brecha_df = brecha_df[
    brecha_df["area_conocimiento"]
    .isin(top_areas)
]

# ============================================================
# ORDENAR
# ============================================================

orden = (
    brecha_df
    .groupby("area_conocimiento")["graduados"]
    .sum()
    .sort_values()
    .index
)

# ============================================================
# FIGURA
# ============================================================

fig, ax = plt.subplots(figsize=(16, 9))

# ============================================================
# SEPARAR HOMBRES Y MUJERES
# ============================================================

fem = brecha_df[
    brecha_df["genero"] == "femenino"
].copy()

mas = brecha_df[
    brecha_df["genero"] == "masculino"
].copy()

# negativos para espejo
mas["graduados"] = -mas["graduados"]

# ============================================================
# ORDENAR
# ============================================================

fem["area_conocimiento"] = pd.Categorical(
    fem["area_conocimiento"],
    categories=orden,
    ordered=True
)

mas["area_conocimiento"] = pd.Categorical(
    mas["area_conocimiento"],
    categories=orden,
    ordered=True
)

fem = fem.sort_values("area_conocimiento")
mas = mas.sort_values("area_conocimiento")

# ============================================================
# BARRAS
# ============================================================

ax.barh(
    mas["area_conocimiento"],
    mas["graduados"],
    alpha=0.9,
    height=0.72,
    label="Masculino"
)

ax.barh(
    fem["area_conocimiento"],
    fem["graduados"],
    alpha=0.9,
    height=0.72,
    label="Femenino"
)

# ============================================================
# ETIQUETAS
# ============================================================

max_value = max(
    fem["graduados"].max(),
    abs(mas["graduados"]).max()
)

offset = max_value * 0.015

# etiquetas mujeres
for _, row in fem.iterrows():

    ax.text(
        row["graduados"] + offset,
        row["area_conocimiento"],
        f'{int(row["graduados"]):,}',
        va='center',
        fontsize=10,
        fontweight='bold'
    )

# etiquetas hombres
for _, row in mas.iterrows():

    ax.text(
        row["graduados"] - (offset * 7),
        row["area_conocimiento"],
        f'{abs(int(row["graduados"])):,}',
        va='center',
        fontsize=10,
        fontweight='bold'
    )

# ============================================================
# LÍNEA CENTRAL
# ============================================================

ax.axvline(
    0,
    color='black',
    linewidth=1.5
)

# ============================================================
# FORMATO EJE X
# ============================================================

ax.xaxis.set_major_formatter(
    plt.FuncFormatter(
        lambda x, _: f'{abs(int(x)):,}'
    )
)

# ============================================================
# MÁRGENES MÁS AMPLIOS
# ============================================================

ax.set_xlim(
    -max_value * 1.25,
    max_value * 1.25
)

# ============================================================
# TÍTULOS
# ============================================================

plt.title(
    "Brecha de género en los graduados por área de conocimiento en Colombia (2015–2024)",
    fontsize=18,
    fontweight='bold',
    pad=20
)

plt.xlabel(
    "Número de graduados",
    fontsize=13,
    fontweight='bold'
)

plt.ylabel(
    "Área de conocimiento",
    fontsize=13,
    fontweight='bold'
)

# ============================================================
# LEYENDA
# ============================================================

plt.legend(
    title="Género",
    loc="lower right",
    fontsize=11,
    title_fontsize=12
)

# ============================================================
# CUADRÍCULA
# ============================================================

plt.grid(
    axis='x',
    linestyle='--',
    alpha=0.25
)

sns.despine(
    left=True,
    bottom=True
)

# ============================================================
# AJUSTE FINAL
# ============================================================

plt.tight_layout(
    pad=2
)

plt.savefig("artifacts/visualizaciones/brecha_graduados.png", dpi=300, bbox_inches="tight")
plt.show()