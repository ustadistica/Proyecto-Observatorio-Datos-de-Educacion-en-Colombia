"""
header_utils_icfes.py — Normalización Cross-Bright de headers ICFES Saber Pro
==============================================================================
Diccionario exhaustivo que unifica TODAS las variantes de columnas encontradas
en los archivos de Saber Pro (2015-2024).

Fuentes auditadas:
  - Examen_Saber_Pro_Genericas_2015.txt (91 columnas)
  - Examen_Saber_Pro_Genericas_2020.txt (96 columnas)
  - Examen_Saber_Pro_Genericas_2024.txt (84 columnas)
"""

import unicodedata
import re
import pandas as pd


def _slugify(name: str) -> str:
    """
    Normalización Cross-Bright: minúsculas, sin tildes, sin puntuación,
    colapsa espacios a snake_case. Estándar UTF-8 → ASCII.
    """
    if not isinstance(name, str):
        return str(name)
    # Normalizar Unicode → ASCII (elimina tildes y caracteres especiales)
    name = (
        unicodedata.normalize("NFKD", name)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    # Eliminar caracteres no alfanuméricos (excepto guión bajo)
    for ch in ['.', ',', ';', ':', '(', ')', '*', '/', '\\', '-', '?', '"', "'", '!']:
        name = name.replace(ch, '_')
    # Colapsar múltiples guiones bajos y espacios → snake_case
    name = re.sub(r'[\s_]+', '_', name.strip())
    return name.lower().strip('_')


# ===========================================================================
# Diccionario Cross-Bright: slug → nombre canónico
# Cubre TODAS las variantes encontradas en Saber Pro 2015-2024.
# ===========================================================================
_CROSS_BRIGHT_MAP_ICFES = {

    # ── Temporalidad ─────────────────────────────────────────────────────────
    "periodo":                              "periodo",

    # ── Identificación estudiante ────────────────────────────────────────────
    "estu_consecutivo":                     "estu_consecutivo",
    "estu_estudiante":                      "estu_tipo_registro",
    "estu_tipodocumento":                   "estu_tipo_documento",
    "estu_tipodocumentosb11":               "estu_tipo_documento_sb11",
    "estu_nacionalidad":                    "estu_nacionalidad",
    "estu_privado_libertad":                "estu_privado_libertad",
    "estu_discapacidad":                    "estu_discapacidad",
    "estu_etnia":                           "estu_etnia",
    "estu_tieneetnia":                      "estu_tiene_etnia",
    "estu_exterior":                        "estu_exterior",
    "estu_genero":                          "genero",
    "estu_fechanacimiento":                 "fecha_nacimiento",
    "estu_estadocivil":                     "estu_estado_civil",
    "estu_repite":                          "estu_repite",
    "estu_esvalidante":                     "estu_es_validante",
    "estu_agregado":                        "estu_agregado",

    # ── Residencia ───────────────────────────────────────────────────────────
    "estu_cod_reside_depto":                "cod_depto_residencia",
    "estu_cod_reside_mcpio":                "cod_mcpio_residencia",
    "estu_depto_reside":                    "depto_residencia",
    "estu_mcpio_reside":                    "mcpio_residencia",
    "estu_pais_reside":                     "pais_residencia",
    "estu_areareside":                      "area_residencia",
    "estu_zona_presentacion":               "zona_presentacion",

    # ── Presentación del examen ──────────────────────────────────────────────
    "estu_cod_depto_presentacion":          "cod_depto_presentacion",
    "estu_cod_mcpio_presentacion":          "cod_mcpio_presentacion",
    "estu_depto_presentacion":              "depto_presentacion",
    "estu_mcpio_presentacion":              "mcpio_presentacion",
    "estu_cod_sitio_presentacion":          "cod_sitio_presentacion",
    "estu_simulacrotipoicfes":              "estu_simulacro_tipo_icfes",
    "estu_vecespresentoexamen":             "estu_veces_presento_examen",
    "estu_vecespresentoexamenestado":       "estu_veces_presento_examen_estado",
    "estu_semestre_examenestadosb11":       "estu_semestre_examen_estado_sb11",
    "estu_ano_examenestado_sb11":           "estu_ano_examen_estado_sb11",
    "estu_comocapacitoexamensb11":          "estu_como_capacito_examen_sb11",

    # ── Colegio de egreso ────────────────────────────────────────────────────
    "estu_cod_cole_mcpio_termino":          "cod_mcpio_colegio_termino",
    "estu_coddane_cole_termino":            "cod_dane_colegio_termino",
    "estu_codicfescole_termino":            "cod_icfes_colegio_termino",
    "estu_cole_termino":                    "nombre_colegio_termino",
    "estu_otrocole_termino":                "otro_colegio_termino",
    "estu_anoterminoultimogrado":           "ano_termino_ultimo_grado",
    "estu_ultimogradoaprobo":               "ultimo_grado_aprobo",
    "estu_fechagradobachiller":             "fecha_grado_bachiller",
    "estu_fechaactagrado":                  "fecha_acta_grado",
    "estu_tituloobtenidobachiller":         "titulo_obtenido_bachiller",

    # ── Institución de educación superior ────────────────────────────────────
    "inst_cod_institucion":                 "codigo_ies",
    "inst_nombre_institucion":              "nombre_ies",
    "inst_caracter_academico":              "caracter_ies",
    "inst_origen":                          "origen_ies",

    # ── Programa académico ───────────────────────────────────────────────────
    "estu_prgm_academico":                  "programa_academico",
    "estu_prgm_codmunicipio":               "cod_mcpio_programa",
    "estu_prgm_municipio":                  "mcpio_programa",
    "estu_prgm_departamento":               "depto_programa",
    "estu_prgm_codmunicipio":              "cod_mcpio_programa",
    "estu_nivel_prgm_academico":            "nivel_programa",
    "estu_metodo_prgm":                     "metodologia_programa",
    "estu_nucleo_pregrado":                 "nucleo_pregrado",
    "estu_snies_prgmacademico":             "codigo_snies_programa",
    "estu_semestrecursa":                   "semestre_cursa",
    "estu_porcentajecreditosaprob":         "pct_creditos_aprobados",
    "estu_inst_codmunicipio":               "cod_mcpio_ies",
    "estu_inst_departamento":               "depto_ies",
    "estu_inst_municipio":                  "mcpio_ies",

    # ── Socioeconómico estudiante ────────────────────────────────────────────
    "estu_horassemanatrabaja":              "horas_semana_trabaja",
    "estu_trabaja_actualmente":             "trabaja_actualmente",
    "estu_tomo_cursopreparacion":           "tomo_curso_preparacion",
    "estu_cursodocentesies":                "curso_docente_ies",
    "estu_cursoiesapoyoexterno":            "curso_ies_apoyo_externo",
    "estu_cursoiesexterna":                 "curso_ies_externa",
    "estu_valormatriculauniversidad":       "valor_matricula_universidad",
    "estu_pagomatriculabeca":               "pago_matricula_beca",
    "estu_pagomatriculacredito":            "pago_matricula_credito",
    "estu_pagomatriculapadres":             "pago_matricula_padres",
    "estu_pagomatriculapropio":             "pago_matricula_propio",
    "estu_actividadrefuerzoareas":          "actividad_refuerzo_areas",
    "estu_actividadrefuerzogeneric":        "actividad_refuerzo_generica",
    "estu_inse_individual":                 "inse_individual",
    "estu_nse_individual":                  "nse_individual",
    "estu_nse_ies":                         "nse_ies",

    # ── Familia ──────────────────────────────────────────────────────────────
    "fami_cabezafamilia":                   "fami_cabeza_familia",
    "fami_cuartoshogar":                    "fami_cuartos_hogar",
    "fami_educacionmadre":                  "fami_educacion_madre",
    "fami_educacionpadre":                  "fami_educacion_padre",
    "fami_estratovivienda":                 "fami_estrato_vivienda",
    "fami_hogaractual":                     "fami_hogar_actual",
    "fami_ingreso_fmiliar_mensual":         "fami_ingreso_familiar_mensual",
    "fami_nivel_sisben":                    "fami_nivel_sisben",
    "fami_numpersonasacargo":               "fami_num_personas_acargo",
    "fami_ocupacionmadre":                  "fami_ocupacion_madre",
    "fami_ocupacionpadre":                  "fami_ocupacion_padre",
    "fami_personashogar":                   "fami_personas_hogar",
    "fami_pisos_hogar":                     "fami_pisos_hogar",
    "fami_telefono":                        "fami_telefono",
    "fami_tiene_celular":                   "fami_tiene_celular",
    "fami_tiene_horno":                     "fami_tiene_horno",
    "fami_tiene_microondas":                "fami_tiene_microondas",
    "fami_tiene_nevera":                    "fami_tiene_nevera",
    "fami_tieneautomovil":                  "fami_tiene_automovil",
    "fami_tienecomputador":                 "fami_tiene_computador",
    "fami_tieneinternet":                   "fami_tiene_internet",
    "fami_tienelavadora":                   "fami_tiene_lavadora",
    "fami_tieneconsolavideojuegos":         "fami_tiene_consola",
    "fami_tienehornomicroogas":             "fami_tiene_horno_microondas",
    "fami_tienemotocicleta":                "fami_tiene_motocicleta",
    "fami_tieneserviciotv":                 "fami_tiene_servicio_tv",
    "fami_trabajolabormadre":               "fami_trabajo_labor_madre",
    "fami_trabajolaborpadre":               "fami_trabajo_labor_padre",
    # variante 2020 (encoding roto de tilde en ñ — múltiples variantes según lectura)
    # La ñ en UTF-8 leída como latin-1 produce Ã± → NFKD → "aa" + "o"
    "fami_cuantoscompartebaao":              "fami_cuantos_comparten_bano",   # UTF-8 leído como latin-1
    "fami_cuantoscomparteba_o":              "fami_cuantos_comparten_bano",
    "fami_cuantoscompartebano":              "fami_cuantos_comparten_bano",
    "fami_cuantoscomparteba__o":             "fami_cuantos_comparten_bano",
    "fami_cuantoscompartebao":               "fami_cuantos_comparten_bano",
    "fami_cuantoscompartebaano":             "fami_cuantos_comparten_bano",
    "fami_cuantoscompartebaa_o":             "fami_cuantos_comparten_bano",
    "fami_numlibros":                        "fami_num_libros",


    # ── Apoyo pedagógico (2016-2018) ─────────────────────────────────────────
    # Slugs reales cuando el archivo está en UTF-8 pero se lee como latin-1:
    # 'ñ' (U+00F1) en UTF-8 = 0xC3 0xB1 → leído como latin-1 → "Ã±" → NFKD → "Aa" + "a" → slug "aa"
    "estu_apo_acompaaamiento":              "estu_apo_acompanamiento",   # UTF-8 leído como latin-1
    "estu_apo_acompa_amiento":              "estu_apo_acompanamiento",
    "estu_apo_acompanamiento":              "estu_apo_acompanamiento",
    "estu_apo_desplazasitio":               "estu_apo_desplaza_sitio",
    "estu_apo_interpseaas":                 "estu_apo_interp_senas",     # UTF-8 leído como latin-1
    "estu_apo_interp_seas":                 "estu_apo_interp_senas",
    "estu_apo_interpsenas":                 "estu_apo_interp_senas",
    "estu_apo_interpsordo_ciego":           "estu_apo_interp_sordo_ciego",
    "estu_apo_interpsordociego":            "estu_apo_interp_sordo_ciego",
    "estu_apo_jefesalon":                   "estu_apo_jefe_salon",
    "estu_apo_lectorapoyo":                 "estu_apo_lector_apoyo",
    "estu_apo_maniobrarmat":                "estu_apo_maniobrar_material",
    "estu_apo_norequiere":                  "estu_apo_no_requiere",

    # ── Dedicación y trabajo (2016-2019) ─────────────────────────────────────
    "estu_dedicacioninternet":              "estu_dedicacion_internet",
    "estu_dedicacionlecturadiaria":         "estu_dedicacion_lectura_diaria",
    "estu_tiporemuneracion":                "estu_tipo_remuneracion",
    "estu_pagomatriculaext":                "pago_matricula_exterior",
    "estu_valormatriculauext":              "valor_matricula_exterior",
    "estu_paisdocumentosb11":               "pais_documento_sb11",

    # ── Puntaje de referencia por módulo (pgref, 2016-2019) ──────────────────
    "mod_competen_ciudada_pgref":           "pgref_comp_ciudadanas",
    "mod_comuni_escrita_pgref":             "pgref_comuni_escrita",
    "mod_ingles_pgref":                     "pgref_ingles",
    "mod_lectura_critica_pgref":            "pgref_lectura_critica",
    "mod_razona_cuantitativo_pgref":        "pgref_razona_cuantitativa",

    # ── Módulos de evaluación ─────────────────────────────────────────────────
    # Competencias ciudadanas
    "mod_competen_ciudada_punt":            "punt_comp_ciudadanas",
    "mod_competen_ciudada_desem":           "desem_comp_ciudadanas",
    "mod_competen_ciudada_pnal":            "pnal_comp_ciudadanas",
    "mod_competen_ciudada_pnbc":            "pnbc_comp_ciudadanas",
    # Comunicación escrita
    "mod_comuni_escrita_punt":              "punt_comuni_escrita",
    "mod_comuni_escrita_desem":             "desem_comuni_escrita",
    "mod_comuni_escrita_pnal":              "pnal_comuni_escrita",
    "mod_comuni_escrita_pnbc":              "pnbc_comuni_escrita",
    # Inglés
    "mod_ingles_punt":                      "punt_ingles",
    "mod_ingles_desem":                     "desem_ingles",
    "mod_ingles_pnal":                      "pnal_ingles",
    "mod_ingles_pnbc":                      "pnbc_ingles",
    # Lectura crítica
    "mod_lectura_critica_punt":             "punt_lectura_critica",
    "mod_lectura_critica_desem":            "desem_lectura_critica",
    "mod_lectura_critica_pnal":             "pnal_lectura_critica",
    "mod_lectura_critica_pnbc":             "pnbc_lectura_critica",
    # Razonamiento cuantitativo (variantes 2015 vs 2020+)
    "mod_razona_cuantitat_punt":            "punt_razona_cuantitativa",
    "mod_razona_cuantitat_desem":           "desem_razona_cuantitativa",
    "mod_razona_cuantitativo_pnal":         "pnal_razona_cuantitativa",
    "mod_razona_cuantitativo_pnbc":         "pnbc_razona_cuantitativa",

    # ── Puntaje global ───────────────────────────────────────────────────────
    "punt_global":                          "puntaje_global",
    "percentil_global":                     "percentil_global",
    "percentil_nbc":                        "percentil_nbc",
}

# Columnas numéricas que pueden tener decimales con coma (ej: "5,0" → 5.0)
NUMERIC_COLS_SABER_PRO = [
    "puntaje_global", "percentil_global", "percentil_nbc",
    "punt_comp_ciudadanas", "punt_comuni_escrita", "punt_ingles",
    "punt_lectura_critica", "punt_razona_cuantitativa",
    "pnal_comp_ciudadanas", "pnal_comuni_escrita", "pnal_ingles",
    "pnal_lectura_critica", "pnal_razona_cuantitativa",
    "pnbc_comp_ciudadanas", "pnbc_comuni_escrita", "pnbc_ingles",
    "pnbc_lectura_critica", "pnbc_razona_cuantitativa",
    "cod_depto_residencia", "cod_mcpio_residencia",
    "cod_depto_presentacion", "cod_mcpio_presentacion",
    "cod_mcpio_programa", "codigo_ies", "codigo_snies_programa",
    "fami_estrato_vivienda",
]

# Columnas core que deben estar presentes en TODOS los años (2015-2024).
# Nota: puntaje_global y percentil_global no existen en 2015 (solo puntajes
# por módulo), por lo que no se incluyen en el core universal.
CORE_COLS_SABER_PRO = [
    "periodo", "estu_consecutivo", "genero",
    "codigo_ies", "nombre_ies", "programa_academico",
]


def normalise_header_icfes(name: str) -> str:
    """Normaliza un nombre de columna al estándar Cross-Bright de ICFES."""
    slug = _slugify(name)
    return _CROSS_BRIGHT_MAP_ICFES.get(slug, slug)


def get_unmapped_columns_icfes(df: pd.DataFrame) -> list:
    """
    Retorna columnas del DataFrame que NO están en el diccionario Cross-Bright.
    Útil para auditoría y detectar cambios de la fuente ICFES.
    """
    unmapped = []
    for col in df.columns:
        slug = _slugify(col)
        if slug not in _CROSS_BRIGHT_MAP_ICFES:
            unmapped.append(col)
    return unmapped


def normalizar_columnas_icfes(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica la normalización Cross-Bright al DataFrame completo."""
    import logging
    logger = logging.getLogger(__name__)
    unmapped = get_unmapped_columns_icfes(df)
    if unmapped:
        logger.warning(f"Columnas no mapeadas (preservadas): {unmapped}")
    return df.rename(columns={col: normalise_header_icfes(col) for col in df.columns})
