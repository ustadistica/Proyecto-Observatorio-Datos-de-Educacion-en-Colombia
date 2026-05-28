import sys
import pandas as pd
import re
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.ingesta.header_utils import normalise_header

RAW_PTE = Path('datos/raw/pte')
OUTPUT  = Path('datos/processed/pte/pte_consolidado_full.parquet')

def extract_year_from_path(p: Path) -> int | None:
    try:
        year = int(p.parent.name)
        if 2015 <= year <= 2025: return year
    except (ValueError, TypeError): pass
    m = re.search(r'(201[5-9]|202[0-5])', p.name)
    return int(m.group(1)) if m else None

def _ascii_norm(s) -> str:
    if not isinstance(s, str): return ''
    return unicodedata.normalize('NFKD', s).encode('ASCII','ignore').decode('utf-8').strip().upper()

def main():
    frames = []

    for p in sorted(RAW_PTE.rglob('*.parquet')):
        if 'pte_manual_' not in p.name:
            continue
        print('Leyendo ' + str(p) + ' ...')
        df = pd.read_parquet(p)

        # Cross-bright: normalizar headers
        df.columns = [normalise_header(col) for col in df.columns]

        # Asegurar año
        anio = extract_year_from_path(p)
        df['anio_proceso'] = anio

        # Detectar fuente por columna 'fuente_ingesta' si existe, si no inferir por año
        if 'fuente_ingesta' not in df.columns:
            df['fuente_ingesta'] = 'men_excel' if anio and anio <= 2018 else 'desconocida'

        frames.append(df)
        print('  -> ' + str(len(df)) + ' filas, anio=' + str(anio) + ', fuente=' + df['fuente_ingesta'].iloc[0])

    if not frames:
        print('[ERROR] No se encontraron archivos parquet en ' + str(RAW_PTE))
        return

    full_df = pd.concat(frames, ignore_index=True, sort=False)

    # ── Limpieza de floats ────────────────────────────────────────────────────
    numeric_cols = [
        'apropiacioninicial', 'apropiacionvigente', 'compromisos', 'obligaciones', 'pagos',
        'adiciones', 'reducciones', 'apropiacionbloqueada', 'apropiaciondisponible',
        'cdp', 'orden_pago', 'anio_proceso'
    ]
    for col in numeric_cols:
        if col in full_df.columns:
            full_df[col] = pd.to_numeric(full_df[col], errors='coerce')

    # Limpiar strings: reemplazar 'nan' por None
    for col in full_df.select_dtypes(include='object').columns:
        full_df[col] = full_df[col].where(
            full_df[col].notna() & (full_df[col].astype(str) != 'nan'), other=None)

    # ── Filtro por fuente ─────────────────────────────────────────────────────
    # Para 2015-2018 (MEN Excel): filtrar solo filas del MEN Gestión General
    if 'nombre_uej' in full_df.columns:
        full_df['_uej_key'] = full_df['nombre_uej'].apply(_ascii_norm)

        # Fuentes MEN: solo filas del Ministerio
        mask_men  = (full_df['fuente_ingesta'] == 'men_excel') & \
                    (full_df['_uej_key'] == 'MINISTERIO EDUCACION NACIONAL - GESTION GENERAL')
        # Fuentes SIIF/DNP/interpolado: ya son filas de universidades, conservar todas
        mask_siif = full_df['fuente_ingesta'].isin(['dnp_cuadro7','siif_uej','interpolado_2018_2020','desconocida']) & \
                    full_df['_uej_key'].str.contains('UNIVERSIDAD', na=False)

        full_df = full_df[mask_men | mask_siif].copy()
        full_df.drop(columns=['_uej_key'], inplace=True)

    # Eliminar columnas granulares no necesarias
    cols_to_drop = [
        'cdp','orden_pago','apropiacionbloqueada','apropiaciondisponible',
        'cta','sub_cta','obj','ord','sor_ord','item','sub_item','sub_item_2',
        'codigo_cuarto_nivel','codigo_quinto_nivel','nombre_cuarto_nivel','nombre_quinto_nivel',
        '_pct_comp','_pct_oblig','_pct_pago'
    ]
    full_df.drop(columns=[c for c in cols_to_drop if c in full_df.columns], errors='ignore', inplace=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    full_df.to_parquet(OUTPUT, index=False)

    print('[OK] Consolidado creado -> ' + OUTPUT.name + ' (' + str(len(full_df)) + ' filas)')
    print('   Anios presentes: ' + str(sorted(full_df['anio_proceso'].dropna().unique().tolist())))
    fuentes = full_df['fuente_ingesta'].value_counts().to_dict() if 'fuente_ingesta' in full_df.columns else {}
    print('   Fuentes: ' + str(fuentes))

if __name__ == '__main__':
    main()
