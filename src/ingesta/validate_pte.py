"""
validate_pte.py -- Validador integral del pipeline PTE (Cross-Bright)
====================================================================
Genera un reporte JSON en tests/validate_pte.json con las siguientes validaciones:

1. Cross-Bright Mapper   -> columnas no mapeadas por año
2. Duplicados            -> filas exactamente iguales por año
3. Integridad numerica   -> valores nulos en columnas financieras clave
4. Filtro MEN            -> que todos los registros sean del MEN correcto
5. Cobertura de años     -> que los 10 años esten presentes en el consolidado
6. Resumen por año       -> filas, pagos totales y columnas disponibles
7. Variants audit        -> que variantes del diccionario fueron encontradas en cada año
8. Dictionary unit test  -> que cada llave del diccionario apunta correctamente a su canonico
9. Core headers presence -> que las columnas clave estén presentes en todas las bases de datos
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import unicodedata

# -- Rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ingesta.header_utils import get_unmapped_columns, _slugify, _CROSS_BRIGHT_MAP, normalise_header

RAW_PTE   = BASE_DIR / "datos" / "raw" / "pte"
PROCESSED = BASE_DIR / "datos" / "processed" / "pte" / "pte_consolidado_full.parquet"
OUTPUT    = BASE_DIR / "tests" / "validate_pte.json"

YEARS_EXPECTED = list(range(2015, 2025))
FINANCIAL_COLS = ["apropiacioninicial", "apropiacionvigente", "compromisos",
                  "obligaciones", "pagos"]
CORE_CANONICALS = ["anio_proceso", "mes_reporte", "codigo_uej", "nombre_uej", "pagos"]
MEN_CANONICAL  = "MINISTERIO EDUCACION NACIONAL - GESTION GENERAL"


def ascii_norm(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return (
        unicodedata.normalize("NFKD", s)
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .strip()
        .upper()
    )


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
        "financial_nulls": {},
        "men_filter": {},
        "core_headers_presence": {},
        "years_coverage": {},
        "per_year_stats": {}
    },
    "errors": []
}

# ============================================================
# VALIDACION 0: Unit test del diccionario header_utils
# ============================================================
print("[>>] Validando diccionario Cross-Bright (header_utils)...")

# Agrupar variantes por canonico
canonicals = {}
for variant, canonical in _CROSS_BRIGHT_MAP.items():
    canonicals.setdefault(canonical, []).append(variant)

dict_results = {}
all_dict_ok  = True
for canonical, variants in sorted(canonicals.items()):
    variant_checks = {}
    all_ok = True
    for v in variants:
        # Slugify + lookup debe devolver el canonico
        mapped = normalise_header(v)
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
    "total_variants": len(_CROSS_BRIGHT_MAP),
    "details": dict_results
}
print(f"  [OK] Diccionario: {len(canonicals)} campos canonicos | {len(_CROSS_BRIGHT_MAP)} variantes registradas")

# ============================================================
# VALIDACION 1: Por año en raw + audit de variantes reales
# ============================================================
print("[>>] Validando parquets raw por año...")
for year in YEARS_EXPECTED:
    parquet = RAW_PTE / str(year) / f"pte_manual_{year}.parquet"
    if not parquet.exists():
        for key in ["cross_bright_mapper", "variants_audit", "duplicates",
                    "financial_nulls", "men_filter", "core_headers_presence"]:
            results["validations"][key][str(year)] = "MISSING"
        results["errors"].append(f"Anno {year}: parquet no encontrado en {parquet}")
        continue

    df = pd.read_parquet(parquet)

    # -- 1a. Cross-Bright: columnas no mapeadas
    unmapped = get_unmapped_columns(df)
    results["validations"]["cross_bright_mapper"][str(year)] = {
        "status": "OK" if not unmapped else "WARNING",
        "unmapped_columns": unmapped
    }

    # -- 1b. Variants audit: que variantes del diccionario aparecieron realmente
    variants_found   = {}
    variants_missing = []
    for col in df.columns:
        slug    = _slugify(col)
        canonical = _CROSS_BRIGHT_MAP.get(slug)
        if canonical:
            variants_found[col] = canonical
        else:
            variants_missing.append(col)

    results["validations"]["variants_audit"][str(year)] = {
        "status": "OK" if not variants_missing else "INFO",
        "columns_in_file": list(df.columns),
        "mapped_variants": variants_found,
        "unmapped_raw_columns": variants_missing,
        "note": f"Solo {len(variants_found)} de {len(df.columns)} columnas tienen entrada en Cross-Bright"
    }

    # -- 1c. Duplicados
    total_rows = len(df)
    deduped    = df.drop_duplicates()
    dupes      = total_rows - len(deduped)
    results["validations"]["duplicates"][str(year)] = {
        "status": "OK" if dupes == 0 else "WARNING",
        "total_rows": total_rows,
        "duplicate_rows": dupes
    }

    # -- 1d. Nulos en columnas financieras
    null_report = {}
    for col in FINANCIAL_COLS:
        if col in df.columns:
            n = int(pd.to_numeric(df[col], errors="coerce").isna().sum())
            null_report[col] = n
    results["validations"]["financial_nulls"][str(year)] = {
        "status": "OK" if all(v == 0 for v in null_report.values()) else "WARNING",
        "null_counts": null_report
    }

    # -- 1e. Filtro MEN
    if "nombre_uej" in df.columns:
        matches_men = df["nombre_uej"].apply(ascii_norm) == MEN_CANONICAL
        non_men = int((~matches_men & df["nombre_uej"].notna()).sum())
        results["validations"]["men_filter"][str(year)] = {
            "status": "OK" if non_men == 0 else "INFO",
            "men_rows": int(matches_men.sum()),
            "non_men_rows": non_men
        }
    else:
        results["validations"]["men_filter"][str(year)] = {
            "status": "WARNING",
            "detail": "Columna nombre_uej no encontrada"
        }

    # -- 1f. Core canonical headers
    missing_core = [c for c in CORE_CANONICALS if c not in df.columns]
    results["validations"]["core_headers_presence"][str(year)] = {
        "status": "OK" if not missing_core else "ERROR",
        "missing_headers": missing_core,
        "present_headers": [c for c in CORE_CANONICALS if c in df.columns]
    }

    print(f"  [OK] {year}: {total_rows} filas | {dupes} duplicados | "
          f"{len(variants_found)} variantes cruzadas | {len(unmapped)} no mapeadas")

# ============================================================
# VALIDACION 2: Consolidado final
# ============================================================
print("\n[>>] Validando consolidado final...")
if not PROCESSED.exists():
    results["errors"].append(f"Consolidado no encontrado: {PROCESSED}")
    results["pipeline_status"] = "ERROR"
else:
    df_full = pd.read_parquet(PROCESSED)

    years_present = sorted(df_full["anio_proceso"].dropna().unique().astype(int).tolist())
    years_missing = [y for y in YEARS_EXPECTED if y not in years_present]
    results["validations"]["years_coverage"] = {
        "status": "OK" if not years_missing else "WARNING",
        "expected": YEARS_EXPECTED,
        "present":  years_present,
        "missing":  years_missing,
        "note": {
            "2015-2018": "Multiple meses (ingesta completa anual)",
            "2019-2024": "Solo diciembre (Excel de cierre anual - totales acumulados)"
        }
    }

    for year in years_present:
        sub   = df_full[df_full["anio_proceso"] == year]
        pagos = float(pd.to_numeric(sub["pagos"], errors="coerce").sum())
        results["validations"]["per_year_stats"][str(year)] = {
            "rows":                  len(sub),
            "total_pagos_cop":       pagos,
            "total_pagos_billones":  round(pagos / 1e12, 2),
            "columns_available":     sub.dropna(axis=1, how="all").columns.tolist()
        }

    dupes_full = len(df_full) - len(df_full.drop_duplicates())
    results["summary"] = {
        "total_rows_consolidado":    len(df_full),
        "duplicate_rows_consolidado": dupes_full,
        "years_present":             years_present,
        "total_pagos_billones":      round(
            pd.to_numeric(df_full["pagos"], errors="coerce").sum() / 1e12, 2
        )
    }

    print(f"  [OK] Consolidado: {len(df_full)} filas | {years_present}")
    if years_missing:
        print(f"  [!!] Annos faltantes: {years_missing}")

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

print(f"\n[{'OK' if results['pipeline_status'] == 'OK' else '!!'}] Pipeline status: {results['pipeline_status']}")
print(f"[JSON] Reporte guardado en: {OUTPUT}")

