"""
Modulo de Ingesta Final: PTE (Presupuesto de Educación)
-----------------------------------------------------
Fuentes:
1. 2019-2024: API Socrata (MinHacienda - https://www.datos.gov.co/resource/5phs-yqfw)
2. 2015-2018: Reportes MinEducacion
   (https://www.mineducacion.gov.co/portal/micrositios-institucionales/
    Presupuesto/Reportes-de-ejecucion-presupuestal/)
"""
import os
import re
import logging
import unicodedata
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sodapy import Socrata

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Detectar directorio base (funciona tanto en local como en Colab)
if Path("/content/drive/MyDrive").exists():
    BASE_DIR = Path(
        "/content/drive/MyDrive/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia"
    )
else:
    BASE_DIR = Path(__file__).parent.parent.parent

RAW_PTE = BASE_DIR / "datos" / "raw" / "pte"
SOCRATA_DOMAIN = "www.datos.gov.co"
DATASET_HACIENDA = "5phs-yqfw"


def _limpiar_texto(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = "".join(
        c for c in unicodedata.normalize("NFKD", t)
        if not unicodedata.combining(c)
    )
    return re.sub(r"[^a-z0-9_]", "", t.lower().strip().replace(" ", "_")).strip("_")


def fetch_pte_api(year: int, token: str = None) -> pd.DataFrame:
    client = Socrata(
        SOCRATA_DOMAIN,
        token or os.getenv("SOCRATA_APP_TOKEN"),
        timeout=60
    )
    where = f"anio = '{year}' AND upper(sector) like '%EDUCACION%'"
    logger.info(f"📡 Descargando API Socrata {year}...")

    results = []
    offset = 0
    limit = 50000
    while True:
        chunk = client.get(
            DATASET_HACIENDA,
            where=where,
            limit=limit,
            offset=offset
        )
        if not chunk:
            break
        results.extend(chunk)
        offset += limit

    logger.info(f"  > Registros obtenidos: {len(results)}")
    client.close()
    return pd.DataFrame.from_records(results)


def procesar_excel_manual(ruta: Path):
    try:
        is_xlsx = ruta.suffix.lower() == '.xlsx'
        engine = "openpyxl" if is_xlsx else "xlrd"
        engine_kwargs = {'data_only': True} if is_xlsx else None

        if engine_kwargs:
            df_check = pd.read_excel(ruta, engine=engine, engine_kwargs=engine_kwargs, header=None, nrows=100)
        else:
            df_check = pd.read_excel(ruta, engine=engine, header=None, nrows=100)

        # Regex flexible: ya no requiere la palabra "informe"
        patron = re.compile(
            r"ejecucion.*gastos.*(20\d{2})",
            re.IGNORECASE
        )
        anio = None

        # 1. Buscar en el contenido
        for val in df_check.values.flatten():
            match = patron.search(_limpiar_texto(str(val)))
            if match:
                anio = match.group(1)
                break

        # 2. Fallback: Buscar en el nombre del archivo
        if not anio:
            match_name = re.search(r"(20\d{2})", ruta.name)
            if match_name:
                anio = match_name.group(1)

        if anio:
            if engine_kwargs:
                df_full = pd.read_excel(ruta, engine=engine, engine_kwargs=engine_kwargs)
            else:
                df_full = pd.read_excel(ruta, engine=engine)
            df_full['anio_reporte'] = anio
            return df_full, anio
    except Exception as e:
        logger.error(f"Error en {ruta.name}: {e}")
    return None, None


def ejecutar_ingesta_total(years: List[int]):
    RAW_PTE.mkdir(parents=True, exist_ok=True)

    for year in years:
        logger.info(f"\n🚀 PROCESANDO AÑO: {year}")
        year_path = RAW_PTE / str(year)
        year_path.mkdir(parents=True, exist_ok=True)

        if year >= 2019:
            df = fetch_pte_api(year)
            if not df.empty:
                df = df.astype(str)
                df.to_parquet(
                    year_path / f"pte_api_{year}.parquet",
                    index=False
                )
                logger.info(f"✅ API {year} exitosa.")
        else:
            for excel in RAW_PTE.glob("*.xls*"):
                df_exc, anio_exc = procesar_excel_manual(excel)
                if anio_exc == str(year):
                    out_name = (
                        f"pte_manual_{year}_{_limpiar_texto(excel.stem)}.parquet"
                    )
                    df_exc = df_exc.astype(str)
                    df_exc.to_parquet(
                        year_path / out_name,
                        index=False
                    )
                    logger.info(f"✅ Excel {year} convertido (MinEducacion).")


if __name__ == "__main__":
    ejecutar_ingesta_total(list(range(2015, 2025)))