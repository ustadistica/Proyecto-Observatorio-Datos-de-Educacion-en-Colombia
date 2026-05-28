"""
header_utils_snies.py — Normalización Cross-Bright de headers SNIES
===================================================================
Diccionario exhaustivo que unifica TODAS las variantes de nombres de columna
encontradas en los archivos RAW de SNIES (graduados y matriculados, 2015-2024).

Variantes identificadas: ver _CROSS_BRIGHT_MAP_SNIES
Campos canónicos resultantes: ~30 columnas estandarizadas.
"""

import unicodedata
import pandas as pd
import re


def _slugify(name: str) -> str:
    """Limpieza base: minúsculas, sin tildes, sin puntuación, sin newlines."""
    if not isinstance(name, str):
        return str(name)
    # Quitar newlines y tabs
    name = name.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Quitar sufijo de año (ej: "Matriculados 2015")
    name = re.sub(r'\s+\d{4}$', '', name).strip()
    # Quitar asteriscos (ej: "Año*")
    name = name.replace('*', '')
    # Normalizar Unicode (quitar tildes)
    name = (
        unicodedata.normalize("NFKD", name)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    # Quitar paréntesis y puntuación
    for ch in ['.', ',', ';', ':', '(', ')', '/', '\\', '-']:
        name = name.replace(ch, '')
    # Colapsar espacios, convertir a snake_case
    name = re.sub(r'\s+', '_', name.strip())
    return name.lower()


# ---------------------------------------------------------------------------
# Diccionario Cross-Bright: slug → nombre canónico
# Cubre TODAS las variantes encontradas en los RAW de 2015 a 2024.
# ---------------------------------------------------------------------------
_CROSS_BRIGHT_MAP_SNIES = {
    # ── Institución ──────────────────────────────────────────────────────────
    "codigo_de_la_institucion":                  "codigo_institucion",
    "codigo_institucion":                        "codigo_institucion",
    "ies_padre":                                 "ies_padre",
    "institucion_de_educacion_superior_ies":      "nombre_institucion",
    "ies":                                        "nombre_institucion",
    "principal_o_seccional":                      "principal_o_seccional",
    "tipo_ies":                                   "tipo_ies",

    # Sector
    "id_sector_ies":                              "id_sector",
    "id_sector":                                  "id_sector",
    "sector_ies":                                 "sector_ies",
    "sector":                                     "sector_ies",

    # Carácter
    "id_caracter":                                "id_caracter",
    "id_caracter_ies":                            "id_caracter",
    "caracter_ies":                               "caracter_ies",
    "caracter":                                   "caracter_ies",

    # Acreditación
    "ies_acreditada":                             "ies_acreditada",
    "programa_acreditado":                        "programa_acreditado",

    # ── Ubicación IES ────────────────────────────────────────────────────────
    "codigo_del_departamento_ies":                "codigo_depto_ies",
    "departamento_de_domicilio_de_la_ies":        "depto_ies",
    "codigo_del_municipio_ies":                   "codigo_mcpio_ies",
    "codigo_del_municipio_ies":                   "codigo_mcpio_ies",
    "municipio_de_domicilio_de_la_ies":           "mcpio_ies",
    "municipio_dedomicilio_de_la_ies":            "mcpio_ies",

    # Código del municipio (sin sufijo IES/PROGRAMA — variantes 2018, 2019, 2022)
    "codigo_del_municipio":                       "codigo_del_municipio",
    "cdigo_del_municipio_programa":               "codigo_mcpio_programa",

    # ── Programa ─────────────────────────────────────────────────────────────
    "codigo_snies_delprograma":                   "codigo_snies_programa",
    "codigo_snies_del_programa":                  "codigo_snies_programa",
    "programa_academico":                         "nombre_programa",

    # Nivel
    "id_nivel_academico":                         "id_nivel_academico",
    "id_nivel":                                   "id_nivel_academico",
    "nivel_academico":                            "nivel_academico",
    "id_nivel_de_formacion":                      "id_nivel_formacion",
    "id_nivel_formacion":                         "id_nivel_formacion",
    "nivel_de_formacion":                         "nivel_formacion",

    # Metodología / Modalidad
    "id_metodologia":                             "id_metodologia",
    "metodologia":                                "metodologia",
    "id_modalidad":                               "id_modalidad",
    "modalidad":                                  "modalidad",

    # Área de conocimiento
    "id_area":                                    "id_area_conocimiento",
    "id_area_de_conocimiento":                    "id_area_conocimiento",
    "area_de_conocimiento":                       "area_conocimiento",

    # Núcleo
    "id_nucleo":                                  "id_nucleo",
    "nucleo_basico_del_conocimiento_nbc":         "nucleo_conocimiento",

    # CINE
    "id_cine_campo_amplio":                       "id_cine_campo_amplio",
    "id_cine_campo_amplio_desc":                  "id_cine_campo_amplio",
    "desc_cine_campo_amplio":                     "desc_cine_campo_amplio",
    "cine_campo_amplio":                          "desc_cine_campo_amplio",
    "id_cine_campo_especifico":                   "id_cine_campo_especifico",
    "desc_cine_campo_especifico":                 "desc_cine_campo_especifico",
    "id_cine_codigo_detallado":                   "id_cine_campo_detallado",
    "id_cine_campo_detallado":                    "id_cine_campo_detallado",
    "desc_cine_codigo_detallado":                 "desc_cine_campo_detallado",
    "desc_cine_campo_detallado":                  "desc_cine_campo_detallado",

    # ── Ubicación Programa ───────────────────────────────────────────────────
    "codigo_del_departamento_programa":           "codigo_depto_programa",
    "codigo_del_departamentoprograma":            "codigo_depto_programa",
    "departamento_de_oferta_del_programa":        "depto_programa",
    "codigo_del_municipio_programa":              "codigo_mcpio_programa",
    "codigo_del_municipioprograma":               "codigo_mcpio_programa",
    "municipio_de_oferta_del_programa":           "mcpio_programa",

    # ── Demografía / Estudiante ──────────────────────────────────────────────
    "id_sexo":                                    "id_genero",
    "id_genero":                                  "id_genero",
    "sexo":                                       "genero",
    "genero":                                     "genero",

    # ── Temporalidad ─────────────────────────────────────────────────────────
    "ano":                                        "anio_proceso",
    "anio":                                       "anio_proceso",
    "anio_proceso":                               "anio_proceso",
    "semestre":                                   "semestre",

    # ── Métricas ─────────────────────────────────────────────────────────────
    "graduados":                                  "graduados",
    "total_graduados":                            "graduados",
    "matriculados":                               "matriculados",
    "total_matriculados":                         "matriculados",
}


def normalise_header_snies(name: str) -> str:
    """Normaliza un nombre de columna al estándar cross-bright canónico de SNIES."""
    slug = _slugify(name)
    return _CROSS_BRIGHT_MAP_SNIES.get(slug, slug)


def get_unmapped_columns(df: pd.DataFrame) -> list:
    """
    Retorna una lista de columnas del DataFrame que NO están mapeadas en el
    diccionario CROSS_BRIGHT_MAP_SNIES. Útil para auditoría y detectar cambios
    en la fuente de datos.
    """
    unmapped = []
    for col in df.columns:
        slug = _slugify(col)
        if slug not in _CROSS_BRIGHT_MAP_SNIES:
            unmapped.append(col)
    return unmapped


def normalizar_columnas_snies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica la normalización Cross-Bright al DataFrame completo.
    Reporta columnas no mapeadas (Principio de Preservación).
    """
    import logging
    logger = logging.getLogger(__name__)

    unmapped = get_unmapped_columns(df)
    if unmapped:
        logger.warning(f"Columnas no mapeadas (preservadas): {unmapped}")

    new_cols = {col: normalise_header_snies(col) for col in df.columns}
    return df.rename(columns=new_cols)
