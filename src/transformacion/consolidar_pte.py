import sys
import pandas as pd
import re
from pathlib import Path

# Ajustar path para imports desde src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.ingesta.header_utils import normalise_header

RAW_PTE = Path('datos/raw/pte')
OUTPUT = Path('datos/processed/pte/pte_consolidado_full.parquet')

def extract_year_from_path(p: Path) -> int | None:
    """Extrae año del nombre de archivo o carpeta contenedora."""
    # Intentar carpeta padre (ej: datos/raw/pte/2019/pte_api_2019.parquet)
    try:
        year = int(p.parent.name)
        if 2015 <= year <= 2025:
            return year
    except (ValueError, TypeError):
        pass
    # Fallback: extraer del nombre
    m = re.search(r'(201[5-9]|202[0-5])', p.name)
    return int(m.group(1)) if m else None

def main():
    frames = []

    # Buscar recursivamente todos los parquets PTE en raw/pte/
    for p in sorted(RAW_PTE.rglob('*.parquet')):
        if 'pte_manual_' in p.name or 'pte_api_' in p.name:
            print(f"Leyendo {p} ...")
            df = pd.read_parquet(p)
            # Cross-bright: normalizar headers
            df.columns = [normalise_header(col) for col in df.columns]
            # Asegurar año de proceso
            anio = extract_year_from_path(p)
            df['anio_proceso'] = anio
            frames.append(df)
            print(f"  -> {len(df):,} filas, anio={anio}")

    if not frames:
        print("[ERROR] No se encontraron archivos parquet en", RAW_PTE)
        return

    # Concatenar con alineación automática de columnas
    full_df = pd.concat(frames, ignore_index=True, sort=False)

    # Castear columnas financieras a numeric (ambas fuentes Excel + API)
    numeric_cols = [
        'apropiacioninicial', 'apropiacionvigente', 'compromisos', 'obligaciones', 'pagos',
        'adiciones', 'reducciones', 'apropiacionbloqueada', 'apropiaciondisponible',
        'cdp', 'orden_pago', 'anio_proceso'
    ]
    for col in numeric_cols:
        if col in full_df.columns:
            full_df[col] = pd.to_numeric(full_df[col], errors='coerce')

    # Limpiar columnas objeto: reemplazar 'nan' string por None real
    for col in full_df.columns:
        if full_df[col].dtype == object or str(full_df[col].dtype) == 'str':
            full_df[col] = full_df[col].where(
                full_df[col].notna() & (full_df[col] != 'nan'), other=None
            )

    # Filtrar solo la entidad MEN según el requerimiento del estudio
    if 'nombre_uej' in full_df.columns:
        full_df = full_df[full_df['nombre_uej'] == 'MINISTERIO EDUCACION NACIONAL - GESTION GENERAL'].copy()

    # Eliminar columnas de contabilidad granular que no se usarán para análisis macro
    cols_to_drop = [
        'cdp', 'orden_pago', 'apropiacionbloqueada', 'apropiaciondisponible',
        'cta', 'sub_cta', 'obj', 'ord', 'sor_ord', 'item', 'sub_item', 'sub_item_2',
        'codigo_cuarto_nivel', 'codigo_quinto_nivel', 'nombre_cuarto_nivel', 'nombre_quinto_nivel'
    ]
    full_df = full_df.drop(columns=[c for c in cols_to_drop if c in full_df.columns], errors='ignore')

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    full_df.to_parquet(OUTPUT, index=False)
    print(f'[OK] Consolidado (Solo MEN) creado -> {OUTPUT.name} ({len(full_df):,} filas)')
    print(f'   Anios presentes: {sorted(full_df["anio_proceso"].dropna().unique())}')

if __name__ == '__main__':
    main()
