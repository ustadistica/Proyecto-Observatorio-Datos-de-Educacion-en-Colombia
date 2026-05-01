"""
indice_eficiencia.py — Calculo del Indice de Eficiencia Universitaria
======================================================================
Metodologia Cross-Bright:
  - Presupuesto: SOLO rubros de "Transferencias a IES segun Ley 30"
    (Articulos 86 y 87 de la Ley 30/1992 = transferencias directas a universidades publicas)
    Se EXCLUYE: SGP (para colegios), Magisterio, Alimentacion Escolar, etc.
  - Graduados: SNIES (graduados por universidad y anio)
  - Indice: Millones COP pagados por cada graduado
"""

import pandas as pd
import re
import unicodedata
from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent.parent
PTE_PATH   = BASE_DIR / 'datos' / 'processed' / 'pte' / 'pte_consolidado_full.parquet'
SNIES_PATH = BASE_DIR / 'datos' / 'processed' / 'snies' / 'graduados_final.parquet'
OUT_CSV    = BASE_DIR / 'datos' / 'processed' / 'eficiencia_universidades.csv'

# ── Keywords que identifican rubros de transferencias directas a IES Ley 30 ──
# Solo rubros que financian directamente las universidades publicas:
IES_KEYWORDS = [
    'LEY 30',
    'ARTICULO 86',
    'ARTICULO 87',
    'APORTES PARA LA FINANCIACION',
    'APORTES PARA LA FINANCIACI',
    'A UNIVERSIDADES PARA FUNCIONAMIENTO',
    'TRANSFERENCIAS A UNIVERSIDADES',
    'APOYO PARA FOMENTAR EL ACCESO',        # Generacion E y Ser Pilo Paga
    'IES PUBLICAS',
    'IES P',                                # Variante corta
    'INSTITUCIONES DE EDUCACION SUPERIOR',
    'A INSTITUCIONES DE EDUCACI',            # 2024: 'A INSTITUCIONES DE EDUCACION SUPERIOR'
    'RECURSOS PARA TRANSFERIR A INSTITUCIONES',
    'SUPERIOR COMO UN DERECHO',             # 2024: Plan Nacional Petro K20/K30/K40
    'CONCURRENCIA NACION PASIVO PENSIONAL UNIVERSIDAD',  # Pasivo pensional IES 2015
]

# Keywords de lo que se EXCLUYE (para verificacion)
EXCLUYE_KEYWORDS = [
    'SGP', 'SISTEMA GENERAL DE PARTICIPAC', 'PRESTACION DE SERVICIOS',
    'MAGISTERIO', 'ALIMENTACION ESCOLAR', 'PENSIONES', 'PAE',
    'PRIMERA INFANCIA', 'PREESCOLAR',
]


def ascii_slug(s: str) -> str:
    """Normaliza a ASCII mayuscula para comparaciones tolerantes a tildes."""
    if not isinstance(s, str):
        return ''
    return (
        unicodedata.normalize('NFKD', s)
        .encode('ASCII', 'ignore')
        .decode('utf-8')
        .upper()
        .strip()
    )


def es_rubro_ies(desc: str) -> bool:
    """Retorna True si la descripcion corresponde a transferencias IES Ley 30."""
    slug = ascii_slug(str(desc))

    # Exclusiones directas: SGP/magisterio/preescolar (no van a universidades)
    EXCLUYE = [
        'SISTEMA GENERAL DE PARTICIPAC', 'PRESTACION DE SERVICIOS',
        'SGP ', 'MAGISTERIO', 'ALIMENTACION ESCOLAR', 'PRIMERA INFANCIA',
        'PREESCOLAR', 'GRATUIDAD', 'SUBSIDIO TRANSPORTE',
    ]
    if any(ex in slug for ex in EXCLUYE):
        return False

    # Inclusion por keywords de universidades/IES
    if any(kw in slug for kw in IES_KEYWORDS):
        return True

    # Inclusion adicional: rubros 2015 con solo el nombre de la universidad
    # Formato: "UNIVERSIDAD X" sin otro texto (rubro = transferencia directa)
    if re.match(r'^UNIVERSIDAD\s+\w', slug) and len(slug) < 120:
        return True

    return False


def extraer_universidad(desc: str) -> str:
    """Extrae el nombre de la universidad de la descripcion del rubro."""
    if not isinstance(desc, str):
        return None
    slug = ascii_slug(desc)

    # Caso especial: rubros agregados sin universidad especifica
    ignorar = [
        'A UNIVERSIDADES PARA FUNCIONAMIENTO',
        'RECURSOS PARA LAS UNIVERSIDADES PUBLICAS PARA DISTRIBUIR',
        'INSTITUCIONES DE EDUCACION SUPERIOR PUBLICAS',
        'IES PUBLICAS',
        'APOYO PARA FOMENTAR EL ACCESO',
    ]
    if any(ig in slug for ig in ignorar):
        return None  # Rubro agregado, no va a una sola universidad

    if 'UNIVERSIDAD' in slug:
        match = re.search(r'(UNIVERSIDAD[\w\s\-\.]+)', slug)
        if match:
            uni = match.group(1).strip()
            # Limpiar sufijos
            uni = re.sub(r'\s*-\s*NACIONAL$', '', uni)
            uni = re.sub(r'\s*-\s*SEDE\s+.*$', '', uni)
            uni = re.sub(r'\s+LEY\s+.*$', '', uni)
            uni = re.sub(r'\s+ART[\.]*\s+.*$', '', uni)
            uni = re.sub(r'\s+PARA\s+.*$', '', uni)
            return uni.strip()
    return None


# ── 1. Cargar PTE ─────────────────────────────────────────────────────────────
print('Cargando PTE...')
df_pte = pd.read_parquet(PTE_PATH)
df_pte['pagos'] = pd.to_numeric(df_pte['pagos'], errors='coerce')

# Fuentes nuevas (SIIF/DNP/interpolado): ya son filas de universidades, no necesitan filtro de keywords
FUENTES_DIRECTAS = ['dnp_cuadro7', 'siif_uej', 'interpolado_2018_2020']
mask_directa = df_pte.get('fuente_ingesta', pd.Series(dtype=str)).isin(FUENTES_DIRECTAS)

# Fuente MEN (2015-2018): filtrar por keywords Ley 30
df_pte_men  = df_pte[~mask_directa].copy()
df_pte_men['es_ies'] = df_pte_men['descripcion'].apply(es_rubro_ies)
df_ies_men  = df_pte_men[df_pte_men['es_ies']].copy()
df_ies_men['universidad_extraida'] = df_ies_men['descripcion'].apply(extraer_universidad)
df_ies_men  = df_ies_men[df_ies_men['universidad_extraida'].notna()]

# Fuentes directas: usar nombre_uej como universidad
df_ies_direct = df_pte[mask_directa].copy()
df_ies_direct['universidad_extraida'] = df_ies_direct['nombre_uej'].apply(
    lambda s: ascii_slug(str(s)) if pd.notna(s) else None)
df_ies_direct = df_ies_direct[df_ies_direct['universidad_extraida'].notna()]

# Combinar
df_ies = pd.concat([df_ies_men, df_ies_direct], ignore_index=True)

print('Rubros IES totales en el PTE: ' + str(len(df_ies)))
print('Total pagos IES (todos los annos): ' + str(round(df_ies['pagos'].sum() / 1e12, 2)) + ' Billones COP')

# Mostrar breakdown por año
print()
print('Pagos IES por anno (comparables, solo Ley 30):')
by_year = df_ies.groupby('anio_proceso')['pagos'].sum()
for yr, val in by_year.items():
    print('  ' + str(int(yr)) + ': ' + str(round(val / 1e12, 2)) + ' Billones COP')

# Agrupar pagos por universidad y año
pte_grouped = df_ies.groupby(['anio_proceso', 'universidad_extraida'])['pagos'].sum().reset_index()
pte_grouped['pagos_millones'] = pte_grouped['pagos'] / 1e6
pte_grouped['anio_proceso']   = pte_grouped['anio_proceso'].astype(float).astype(int)

print()
print('Universidades con pagos individuales identificados: ' + str(pte_grouped['universidad_extraida'].nunique()))


# ── 2. Cargar SNIES ───────────────────────────────────────────────────────────
print('Cargando SNIES...')
try:
    df_snies = pd.read_parquet(SNIES_PATH, columns=['anio', 'nombre_institucion', 'graduados'])
    df_snies.rename(columns={
        'anio': 'anio_proceso',
        'nombre_institucion': 'institucion',
        'graduados': 'total_graduados'
    }, inplace=True)
    snies_grouped = df_snies.groupby(['anio_proceso', 'institucion'])['total_graduados'].sum().reset_index()
    snies_grouped['anio_proceso'] = snies_grouped['anio_proceso'].astype(float).astype(int)
    print('Instituciones en SNIES: ' + str(snies_grouped['institucion'].nunique()))

    # ── 3. Normalizar para cruce ──────────────────────────────────────────────
    def clean_key(name: str) -> str:
        s = ascii_slug(str(name))
        for token in ['UNIVERSIDAD', 'DE ', 'DEL ', 'LA ', 'EL ', 'LOS ', 'LAS ', '-']:
            s = s.replace(token, ' ')
        return ' '.join(s.split())

    pte_grouped['key'] = pte_grouped['universidad_extraida'].apply(clean_key)
    snies_grouped['key'] = snies_grouped['institucion'].apply(clean_key)

    # ── 4. Cruce ──────────────────────────────────────────────────────────────
    df_cruce = pd.merge(pte_grouped, snies_grouped, on=['anio_proceso', 'key'], how='inner')

    # ── 5. Indice de eficiencia ───────────────────────────────────────────────
    df_cruce['costo_por_graduado_millones'] = df_cruce['pagos_millones'] / df_cruce['total_graduados']

    # Promedio historico por institucion (2015-2024)
    df_avg = (
        df_cruce.groupby('institucion')
        .agg(
            pagos_millones_total=('pagos_millones', 'sum'),
            total_graduados=('total_graduados', 'sum'),
            annos_con_datos=('anio_proceso', 'nunique')
        )
        .reset_index()
    )
    df_avg['costo_promedio'] = df_avg['pagos_millones_total'] / df_avg['total_graduados']

    print()
    print('--- TOP 10 MAS EFICIENTES (menor costo por graduado) 2015-2024 ---')
    top = df_avg.sort_values('costo_promedio').head(10)
    for _, row in top.iterrows():
        print(
            str(row['institucion'])[:45].ljust(47) +
            '| Costo/Grad: $' + str(round(row['costo_promedio'], 1)) + 'M ' +
            '| Annos: ' + str(int(row['annos_con_datos']))
        )

    # Guardar cruce por institucion
    df_cruce.to_csv(OUT_CSV, index=False)
    print()
    print('Dataset guardado en: ' + str(OUT_CSV))

    # ── 6. Serie nacional 2015-2024 (todos los anos, incluyendo agregados) ────
    # Para 2023-2024 no hay desglose por IES, pero si hay total de transferencias
    # y total de graduados en SNIES. Calculamos el costo promedio nacional.
    snies_total_por_anno = df_snies.groupby('anio_proceso')['total_graduados'].sum().reset_index()
    snies_total_por_anno['anio_proceso'] = snies_total_por_anno['anio_proceso'].astype(float).astype(int)

    pte_total_por_anno = df_ies.groupby('anio_proceso')['pagos'].sum().reset_index()
    pte_total_por_anno['anio_proceso'] = pte_total_por_anno['anio_proceso'].astype(float).astype(int)
    pte_total_por_anno['pagos_millones'] = pte_total_por_anno['pagos'] / 1e6

    serie_nacional = pd.merge(pte_total_por_anno, snies_total_por_anno, on='anio_proceso', how='left')
    serie_nacional['costo_nacional_millones'] = serie_nacional['pagos_millones'] / serie_nacional['total_graduados']
    # Marcar que tipo de dato es cada anno
    serie_nacional['tipo_dato'] = serie_nacional['anio_proceso'].apply(
        lambda y: 'desglosado_por_ies' if y <= 2018 else 'agregado_nacional'
    )

    out_serie = OUT_CSV.parent / 'serie_nacional_eficiencia.csv'
    serie_nacional.to_csv(out_serie, index=False)
    print('Serie nacional guardada en: ' + str(out_serie))
    print()
    print('Serie nacional completa 2015-2024:')
    for _, r in serie_nacional.iterrows():
        tag = '[DESGLOSADO]' if r['tipo_dato'] == 'desglosado_por_ies' else '[AGREGADO]  '
        print('  ' + str(int(r['anio_proceso'])) + ' ' + tag +
              ' Pagos IES: ' + str(round(r['pagos_millones']/1e3, 2)) + 'B' +
              ' | Graduados: ' + str(int(r['total_graduados'])) +
              ' | Costo/Grad: $' + str(round(r['costo_nacional_millones'], 2)) + 'M')

except Exception as e:
    print('Error procesando SNIES: ' + str(e))
    import traceback
    traceback.print_exc()
