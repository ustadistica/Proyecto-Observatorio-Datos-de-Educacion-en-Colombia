"""
validate_snies.py -- Validador integral del pipeline SNIES (Cross-Bright)
=========================================================================
Genera un reporte JSON en tests/validate_snies.json con las siguientes validaciones:

1. Dictionary unit test   -> que cada variante del diccionario mapea a su canónico
2. Cross-Bright mapper    -> columnas no mapeadas por año en los RAW
3. Variants audit         -> qué variantes del diccionario aparecieron realmente
4. Duplicados             -> filas exactamente iguales por año
5. Métricas nulas         -> valores nulos en columnas de métricas (graduados/matriculados)
6. Core headers presence  -> que las columnas clave estén presentes en todos los RAW
7. Cobertura de años      -> que los 10 años estén presentes en cada consolidado
8. Per-year stats         -> filas y totales por año en los consolidados
9. Consolidado final      -> integridad del dataset_snies_consolidado.parquet
10. Cifras oficiales       -> contraste directo contra reporte oficial MEN-SNIES
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

# -- Rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ingesta.header_utils_snies import (
    get_unmapped_columns, _slugify, _CROSS_BRIGHT_MAP_SNIES, normalise_header_snies
)

RAW_SNIES       = BASE_DIR / "datos" / "raw" / "snies"
PROCESSED_SNIES = BASE_DIR / "datos" / "processed" / "snies"
CONSOLIDADO     = PROCESSED_SNIES / "dataset_snies_consolidado.parquet"
OUTPUT          = BASE_DIR / "tests" / "validate_snies.json"

YEARS_EXPECTED  = list(range(2015, 2025))
CATEGORIAS      = ["graduados", "matriculados"]
METRIC_COLS     = {"graduados": "graduados", "matriculados": "matriculados"}

CORE_CANONICALS = [
    "anio_proceso", "semestre", "codigo_institucion", "nombre_institucion",
    "codigo_snies_programa", "nombre_programa"
]

# Cifras oficiales del reporte SNIES (articles-391286_recurso_12.xlsx)
OFICIAL_GRADUADOS = {
    2015: 374738, 2016: 423182, 2017: 462367, 2018: 482122, 2019: 507338,
    2020: 449923, 2021: 524983, 2022: 535963, 2023: 534942, 2024: 547959
}
OFICIAL_MATRICULADOS = {
    2015: 2293550, 2016: 2394434, 2017: 2446314, 2018: 2440367, 2019: 2396250,
    2020: 2355603, 2021: 2448271, 2022: 2466228, 2023: 2475833, 2024: 2553560
}

# -- Resultados acumulados
results = {
    "generated_at": datetime.now().isoformat(),
    "pipeline_status": "OK",
    "summary": {},
    "validations": {
        "dictionary_unit_test": {},
        "cross_bright_mapper": {},
        "variants_audit": {},
        "duplicates": {},
        "metric_nulls": {},
        "core_headers_presence": {},
        "years_coverage": {},
        "per_year_stats": {},
        "consolidado_integrity": {},
        "cifras_oficiales": {}
    },
    "errors": []
}

# ============================================================
# VALIDACION 0: Unit test del diccionario header_utils_snies
# ============================================================
print("[>>] Validando diccionario Cross-Bright (header_utils_snies)...")

canonicals = {}
for variant, canonical in _CROSS_BRIGHT_MAP_SNIES.items():
    canonicals.setdefault(canonical, []).append(variant)

dict_results = {}
all_dict_ok  = True
for canonical, variants in sorted(canonicals.items()):
    variant_checks = {}
    all_ok = True
    for v in variants:
        mapped = normalise_header_snies(v)
        ok = (mapped == canonical)
        variant_checks[v] = {"maps_to": mapped, "expected": canonical, "ok": ok}
        if not ok:
            all_ok = False
            all_dict_ok = False
    dict_results[canonical] = {
        "status": "OK" if all_ok else "ERROR",
        "variant_count": len(variants),
        "variants": variant_checks
    }

results["validations"]["dictionary_unit_test"] = {
    "status": "OK" if all_dict_ok else "ERROR",
    "total_canonicals": len(canonicals),
    "total_variants": len(_CROSS_BRIGHT_MAP_SNIES),
    "details": dict_results
}
print(f"  [OK] Diccionario: {len(canonicals)} campos canonicos | "
      f"{len(_CROSS_BRIGHT_MAP_SNIES)} variantes registradas")

# ============================================================
# VALIDACION 1: Por año en RAW para cada categoría
# ============================================================
for categoria in CATEGORIAS:
    print(f"\n[>>] Validando RAW de {categoria.upper()} por ano...")
    metric_col = METRIC_COLS[categoria]

    for year in YEARS_EXPECTED:
        year_key = f"{categoria}_{year}"
        year_dir = RAW_SNIES / categoria / str(year)
        parquet_files = list(year_dir.glob("*.parquet")) if year_dir.exists() else []

        if not parquet_files:
            for key in ["cross_bright_mapper", "variants_audit", "duplicates",
                        "metric_nulls", "core_headers_presence"]:
                results["validations"][key][year_key] = "MISSING"
            results["errors"].append(f"{categoria} {year}: parquet no encontrado en {year_dir}")
            continue

        df = pd.read_parquet(parquet_files[0])

        # -- 1a. Cross-Bright: columnas no mapeadas
        unmapped = get_unmapped_columns(df)
        results["validations"]["cross_bright_mapper"][year_key] = {
            "status": "OK" if not unmapped else "WARNING",
            "unmapped_columns": unmapped,
            "total_columns": len(df.columns)
        }

        # -- 1b. Variants audit: qué variantes aparecieron
        variants_found = {}
        variants_missing = []
        for col in df.columns:
            slug = _slugify(col)
            canonical = _CROSS_BRIGHT_MAP_SNIES.get(slug)
            if canonical:
                variants_found[col] = canonical
            else:
                variants_missing.append(col)

        results["validations"]["variants_audit"][year_key] = {
            "status": "OK" if not variants_missing else "INFO",
            "columns_in_file": list(df.columns),
            "mapped_variants": variants_found,
            "unmapped_raw_columns": variants_missing,
            "note": f"{len(variants_found)} de {len(df.columns)} columnas mapeadas via Cross-Bright"
        }

        # -- 1c. Duplicados
        total_rows = len(df)
        deduped = df.drop_duplicates()
        dupes = total_rows - len(deduped)
        results["validations"]["duplicates"][year_key] = {
            "status": "OK" if dupes == 0 else "WARNING",
            "total_rows": total_rows,
            "duplicate_rows": dupes
        }

        # -- 1d. Nulos en columna de métrica
        # Buscar la columna de métrica (puede tener variantes como "Matriculados 2015")
        metric_found = None
        for col in df.columns:
            slug = _slugify(col)
            if slug == metric_col or slug.startswith(metric_col):
                metric_found = col
                break

        null_count = 0
        fully_empty_nulls = 0
        if metric_found:
            null_mask = pd.to_numeric(df[metric_found], errors="coerce").isna()
            null_count = int(null_mask.sum())
            # Filas donde la métrica Y el año son nulos = relleno/notas del Excel
            # (incluye filas completamente vacías y notas tipo "FUENTE: SNIES-MEN")
            if null_count > 0:
                anio_col = next((c for c in df.columns if _slugify(c) == "ano"), None)
                if anio_col:
                    anio_null = pd.to_numeric(df[anio_col], errors="coerce").isna()
                    fully_empty_nulls = int((null_mask & anio_null).sum())
                else:
                    fully_empty_nulls = int(df[null_mask].isnull().all(axis=1).sum())

        # Si todos los nulos coinciden con año nulo, son basura del Excel → OK
        real_nulls = null_count - fully_empty_nulls
        results["validations"]["metric_nulls"][year_key] = {
            "status": "OK" if real_nulls == 0 else "WARNING",
            "metric_column": metric_found or "NOT_FOUND",
            "null_count": null_count,
            "excel_padding_rows": fully_empty_nulls,
            "real_null_count": real_nulls,
            "note": "Nulos con año=NaN son relleno/notas del Excel, filtrados en limpieza_snies."
        }



        # -- 1e. Core canonical headers (after normalisation)
        normalised_cols = [normalise_header_snies(c) for c in df.columns]
        missing_core = [c for c in CORE_CANONICALS if c not in normalised_cols]
        # La métrica misma (graduados/matriculados) es core también
        if metric_col not in normalised_cols:
            missing_core.append(metric_col)

        results["validations"]["core_headers_presence"][year_key] = {
            "status": "OK" if not missing_core else "WARNING",
            "missing_headers": missing_core,
            "present_headers": [c for c in CORE_CANONICALS + [metric_col] if c in normalised_cols]
        }

        print(f"  [{year}] {categoria}: {total_rows:,} filas | "
              f"{dupes} dupes | {len(variants_found)} mapeadas | "
              f"{len(unmapped)} no mapeadas | "
              f"core_missing={len(missing_core)}")

# ============================================================
# VALIDACION 2: Consolidados limpios (snies_*_limpio_consolidado)
# ============================================================
print("\n[>>] Validando consolidados limpios...")

for categoria in CATEGORIAS:
    path = PROCESSED_SNIES / f"snies_{categoria}_limpio_consolidado.parquet"
    if not path.exists():
        results["errors"].append(f"Consolidado limpio no encontrado: {path.name}")
        continue

    df = pd.read_parquet(path)
    metric_col = METRIC_COLS[categoria]

    # Asegurar tipo numérico
    if metric_col in df.columns:
        df[metric_col] = pd.to_numeric(df[metric_col], errors='coerce').fillna(0).astype(int)
    df['anio_proceso'] = pd.to_numeric(df['anio_proceso'], errors='coerce').fillna(0).astype(int)

    years_present = sorted(df['anio_proceso'].unique().tolist())
    years_missing = [y for y in YEARS_EXPECTED if y not in years_present]

    results["validations"]["years_coverage"][categoria] = {
        "status": "OK" if not years_missing else "WARNING",
        "expected": YEARS_EXPECTED,
        "present": years_present,
        "missing": years_missing
    }

    # Stats por año
    for year in years_present:
        sub = df[df['anio_proceso'] == year]
        total_metric = int(sub[metric_col].sum()) if metric_col in sub.columns else 0

        results["validations"]["per_year_stats"][f"{categoria}_{year}"] = {
            "rows": len(sub),
            "total": total_metric,
            "columns_available": len(sub.dropna(axis=1, how='all').columns)
        }

    # Duplicados en el consolidado
    dupes = len(df) - len(df.drop_duplicates())
    results["validations"]["per_year_stats"][f"{categoria}_consolidado_summary"] = {
        "total_rows": len(df),
        "duplicate_rows": dupes,
        "total_columns": len(df.columns),
        "dtype_metric": str(df[metric_col].dtype) if metric_col in df.columns else "NOT_FOUND"
    }

    print(f"  [{categoria.upper()}] {len(df):,} filas | {dupes} dupes | "
          f"dtype({metric_col})={df[metric_col].dtype if metric_col in df.columns else '?'}")

# ============================================================
# VALIDACION 3: dataset_snies_consolidado.parquet (cruce final)
# ============================================================
print("\n[>>] Validando consolidado final (dataset_snies_consolidado.parquet)...")

if not CONSOLIDADO.exists():
    results["errors"].append(f"Consolidado final no encontrado: {CONSOLIDADO}")
    results["pipeline_status"] = "ERROR"
else:
    df_final = pd.read_parquet(CONSOLIDADO)
    df_final['anio_proceso'] = pd.to_numeric(df_final['anio_proceso'], errors='coerce').fillna(0).astype(int)
    df_final['total_matriculados'] = pd.to_numeric(df_final['total_matriculados'], errors='coerce').fillna(0).astype(int)
    df_final['total_graduados'] = pd.to_numeric(df_final['total_graduados'], errors='coerce').fillna(0).astype(int)

    dupes_final = len(df_final) - len(df_final.drop_duplicates())
    # Check for duplicate IES per year
    dup_ies_year = df_final.duplicated(subset=['anio_proceso', 'codigo_institucion', 'nombre_institucion'], keep=False)
    dup_ies_count = int(dup_ies_year.sum())

    results["validations"]["consolidado_integrity"] = {
        "status": "OK" if dupes_final == 0 and dup_ies_count == 0 else "WARNING",
        "total_rows": len(df_final),
        "exact_duplicate_rows": dupes_final,
        "duplicate_ies_per_year": dup_ies_count,
        "columns": df_final.columns.tolist(),
        "unique_institutions": int(df_final['nombre_institucion'].nunique()),
        "year_range": f"{df_final['anio_proceso'].min()}-{df_final['anio_proceso'].max()}"
    }

    # ── Contraste contra cifras oficiales ────────────────────────────
    print("\n[>>] Contrastando contra cifras oficiales MEN-SNIES...")

    cifras = {}
    all_match = True
    for year in YEARS_EXPECTED:
        dy = df_final[df_final['anio_proceso'] == year]
        mat_parquet  = int(dy['total_matriculados'].sum())
        grad_parquet = int(dy['total_graduados'].sum())
        mat_oficial  = OFICIAL_MATRICULADOS.get(year, 0)
        grad_oficial = OFICIAL_GRADUADOS.get(year, 0)

        mat_match  = mat_parquet == mat_oficial
        grad_match = grad_parquet == grad_oficial

        if not mat_match or not grad_match:
            all_match = False

        cifras[str(year)] = {
            "matriculados_parquet": mat_parquet,
            "matriculados_oficial": mat_oficial,
            "matriculados_match": mat_match,
            "graduados_parquet": grad_parquet,
            "graduados_oficial": grad_oficial,
            "graduados_match": grad_match
        }

        status_icon = "[OK]" if (mat_match and grad_match) else "[!!]"
        print(f"  {status_icon} {year}: Mat={mat_parquet:>10,} (of={mat_oficial:>10,}) | "
              f"Grad={grad_parquet:>10,} (of={grad_oficial:>10,})")

    results["validations"]["cifras_oficiales"] = {
        "status": "OK" if all_match else "ERROR",
        "fuente": "articles-391286_recurso_12.xlsx (MEN-SNIES)",
        "nota_matriculados": "Regla MEN: Sem1 todas IES (excepto SENA) + Sem2 SENA",
        "nota_graduados": "Suma total de ambos semestres",
        "por_anio": cifras
    }

    results["summary"] = {
        "total_rows_consolidado": len(df_final),
        "duplicate_rows_consolidado": dupes_final,
        "duplicate_ies_per_year": dup_ies_count,
        "unique_institutions": int(df_final['nombre_institucion'].nunique()),
        "total_matriculados_10_anios": int(df_final['total_matriculados'].sum()),
        "total_graduados_10_anios": int(df_final['total_graduados'].sum()),
        "cifras_coinciden_con_oficial": all_match
    }

    print(f"\n  Consolidado: {len(df_final):,} filas | {dupes_final} dupes exactos | "
          f"{dup_ies_count} dupes IES/año | "
          f"{int(df_final['nombre_institucion'].nunique())} IES unicas")

# ============================================================
# Estado final
# ============================================================
any_errors  = bool(results["errors"])
any_warning = any(
    v.get("status") == "WARNING"
    for section in results["validations"].values()
    for v in (section.values() if isinstance(section, dict) else [section])
    if isinstance(v, dict)
)
if any_errors:
    results["pipeline_status"] = "ERROR"
elif any_warning:
    results["pipeline_status"] = "WARNING"
else:
    results["pipeline_status"] = "OK"

# -- Guardar JSON
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n[{'OK' if results['pipeline_status'] == 'OK' else '!!'}] "
      f"Pipeline status: {results['pipeline_status']}")
print(f"[JSON] Reporte guardado en: {OUTPUT}")
