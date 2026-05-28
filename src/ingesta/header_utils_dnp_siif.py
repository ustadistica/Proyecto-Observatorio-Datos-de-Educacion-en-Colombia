"""
header_utils.py — Normalización cross-bright de headers PTE
===========================================================
Unifica nombres de columnas entre:
  • Excel MEN 2015-2018 (latin-1, headers por posición)
  • DNP Cuadro 7 2020-2022 (Ejecución PGN detalle por Sector, entidad y rubro)
  • SIIF por UEJ 2023-2024 (Reporte SIIF Ejecución Agregada por Unidad Ejecutora)

Objetivo: que al concatenar todas las fuentes no queden columnas duplicadas
por diferencias de case, tildes, espacios o variantes históricas.
"""

import unicodedata


def _slugify(name: str) -> str:
    """Limpieza base: minúsculas, sin espacios, sin tildes, sin puntuación."""
    if not isinstance(name, str):
        return str(name)
    name = (
        unicodedata.normalize("NFKD", name)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    # Quitar caracteres de puntuación comunes que a veces aparecen en headers del MEN
    for ch in ['.', ',', ';', ':', '(', ')', '/', '\\', '-']:
        name = name.replace(ch, '')
    return name.strip().lower().replace(" ", "_").replace("\n", "_")


# Mapeo cross-bright: cualquier variante conocida -> nombre canónico
_CROSS_BRIGHT_MAP = {
    # -- Año / Periodo --
    "anio": "anio_proceso",
    "ano": "anio_proceso",
    "year": "anio_proceso",
    "anio_reporte": "anio_proceso",
    "anio_proceso": "anio_proceso",
    "vigencia": "vigencia",

    # -- Mes --
    "mes": "mes_reporte",
    "mes_reporte": "mes_reporte",
    "nombremes": "mes_reporte",
    "nombre_mes": "mes_reporte",

    # -- Entidad / UEJ --
    "uej": "codigo_uej",
    "uej_codigo": "codigo_uej",
    "codigo_uej": "codigo_uej",
    "codigoentidad": "codigo_uej",
    "codigo_entidad": "codigo_uej",
    "codigo_entidad_uej": "codigo_uej",

    "nombre_uej": "nombre_uej",
    "nombreentidad": "nombre_uej",
    "nombre_entidad": "nombre_uej",
    "nombre_uej_entidad": "nombre_uej",

    # -- Rubro / Clasificación presupuestal --
    "rubro": "rubro",
    "codigorubro": "rubro",
    "codigo_rubro": "rubro",
    "codigonivelrubrogasto": "rubro",
    "codigo_nivel_rubro_gasto": "rubro",

    "nombrenivelrubrogasto": "nombre_rubro",
    "nombre_rubro": "nombre_rubro",
    "nombre_nivel_rubro_gasto": "nombre_rubro",

    # -- Tipo de gasto --
    "tipo": "tipo_gasto",
    "tipogasto": "tipo_gasto",
    "tipo_gasto": "tipo_gasto",
    "codigotipogasto": "tipo_gasto",
    "codigo_tipo_gasto": "tipo_gasto",

    "nombretipogasto": "nombre_tipo_gasto",
    "nombre_tipo_gasto": "nombre_tipo_gasto",

    # -- Detalle de gasto --
    "codigodetallegasto": "detalle_gasto",
    "detalle_gasto": "detalle_gasto",
    "codigo_detalle_gasto": "detalle_gasto",
    "nombredetallegasto": "nombre_detalle_gasto",
    "nombre_detalle_gasto": "nombre_detalle_gasto",

    # -- Cuarto y quinto nivel --
    "codigocuartonivel": "codigo_cuarto_nivel",
    "codigo_cuarto_nivel": "codigo_cuarto_nivel",
    "nombrecuartonivel": "nombre_cuarto_nivel",
    "nombre_cuarto_nivel": "nombre_cuarto_nivel",

    "codigoquintonivel": "codigo_quinto_nivel",
    "codigo_quinto_nivel": "codigo_quinto_nivel",
    "nombequintonivel": "nombre_quinto_nivel",
    "nombre_quinto_nivel": "nombre_quinto_nivel",
    "nombrequintonivel": "nombre_quinto_nivel",

    # -- Cuentas presupuestales antiguas (Excel) --
    "cta": "cta",
    "sub_cta": "sub_cta",
    "subcta": "sub_cta",
    "obj": "obj",
    "ord": "ord",
    "sor_ord": "sor_ord",
    "item": "item",
    "sub_item": "sub_item",
    "subitem": "sub_item",

    # -- Fuente / Recursos --
    "fuente": "fuente",
    "fuentefinanciacion": "fuente",
    "fuente_financiacion": "fuente",

    "rec": "recursos_presupuestales",
    "recursos": "recursos_presupuestales",
    "recursospresupuestales": "recursos_presupuestales",
    "recursos_presupuestales": "recursos_presupuestales",

    # -- Situación --
    "sit": "situacion",
    "situacion": "situacion",
    "situacion_fondo": "situacion",

    # -- Sector --
    "sector": "sector",

    # -- Cuentas presupuestales (Excel MEN antiguo) --
    "uej": "codigo_uej",
    "nombre_uej": "nombre_uej",
    "cta": "cta",
    "sub_cta": "sub_cta",
    "subcta": "sub_cta",
    "obj": "obj",
    "ord": "ord",
    "sor_ord": "sor_ord",
    "item": "item",
    "sub_item": "sub_item",
    "subitem": "sub_item",
    "sub_item_2": "sub_item_2",
    "subitem2": "sub_item_2",
    "sub_item2": "sub_item_2",
    "rec": "recursos_presupuestales",
    "sit": "situacion",
    "compromiso": "compromisos",
    "obligacion": "obligaciones",
    "ordenpago": "orden_pago",
    "orden_pago": "orden_pago",

    # -- Descripción / Programas --
    "descripcion": "descripcion",
    "detalleprogramas": "descripcion",
    "detalle_programas": "descripcion",
    "programa": "descripcion",

    # -- Apropiaciones --
    "apropiacioninicial": "apropiacioninicial",
    "apr_inicial": "apropiacioninicial",
    "apr._inicial": "apropiacioninicial",
    "apropiacion_inicial": "apropiacioninicial",

    "adiciones": "adiciones",
    "apropiacionadicionada": "adiciones",
    "apr_adicionada": "adiciones",
    "apr._adicionada": "adiciones",
    "adicion": "adiciones",

    "reducciones": "reducciones",
    "apropiacionreducida": "reducciones",
    "apr_reducida": "reducciones",
    "apr._reducida": "reducciones",
    "reduccion": "reducciones",

    "apropiacionvigente": "apropiacionvigente",
    "apr_vigente": "apropiacionvigente",
    "apr._vigente": "apropiacionvigente",
    "apropiacion_vigente": "apropiacionvigente",

    "apropiacionbloqueada": "apropiacionbloqueada",
    "apr_bloqueada": "apropiacionbloqueada",
    "apr._bloqueada": "apropiacionbloqueada",
    "apropiacion_bloqueada": "apropiacionbloqueada",

    "apropiaciondisponible": "apropiaciondisponible",
    "apr_disponible": "apropiaciondisponible",
    "apr._disponible": "apropiaciondisponible",
    "apropiacion_disponible": "apropiaciondisponible",

    "cdp": "cdp",
    "certificadodisponibilidadpresupuestal": "cdp",

    # -- Ejecución --
    "compromisos": "compromisos",
    "compromiso": "compromisos",

    "obligaciones": "obligaciones",
    "obligacion": "obligaciones",

    "ordenpago": "orden_pago",
    "orden_pago": "orden_pago",
    "ordenes_pago": "orden_pago",

    "pagos": "pagos",
    "pago": "pagos",

    # -- DNP Cuadro 7 (2020-2022): Entidad/Detalle jerárquica --
    "entidaddetalle": "descripcion",          # columna principal del Cuadro 7
    "entidad_detalle": "descripcion",
    "entidaddetallerubro": "descripcion",

    # Apropiaciones DNP Cuadro 7
    "apropiacionvigente": "apropiacionvigente",
    "apropiacionvigente_1": "apropiacionvigente",
    "aprvigente": "apropiacionvigente",

    # Porcentajes de ejecución (DNP Cuadro 7 - se descartan)
    "compaprop": "_pct_comp",
    "obligaprop": "_pct_oblig",
    "pagoaprop": "_pct_pago",
    "porcent": "_pct_comp",
    "porcentajedeejecucion": "_pct_comp",

    # Pérdidas de apropiación (DNP Cuadro 7)
    "perdidasdeapropiacion": "apropiacionbloqueada",
    "sincomprometer": "apropiaciondisponible",

    # -- SIIF por UEJ (2023-2024) --
    "nombre_uej": "nombre_uej",
    "nombreuej": "nombre_uej",
    "uej": "codigo_uej",
    "rubro": "rubro",
    "apr_inicial": "apropiacioninicial",
    "apr_adicionada": "adiciones",
    "apr_reducida": "reducciones",
    "apr_vigente": "apropiacionvigente",
    "aprbloqueada": "apropiacionbloqueada",
    "aprdisponible": "apropiaciondisponible",
    "ordenpago": "orden_pago",
    "ordenpago_1": "orden_pago",
}


def normalise_header(name: str) -> str:
    """
    Normaliza un nombre de columna al estándar cross-bright canónico.
    Si no existe en el mapa, devuelve el slug original (sin cambios).
    """
    slug = _slugify(name)
    return _CROSS_BRIGHT_MAP.get(slug, slug)


def get_unmapped_columns(df: pd.DataFrame) -> list:
    """
    Retorna una lista de columnas del DataFrame que NO están mapeadas en el
    diccionario CROSS_BRIGHT_MAP. Útil para auditoría y detectar cambios en las fuentes.
    """
    unmapped = []
    for col in df.columns:
        slug = _slugify(col)
        if slug not in _CROSS_BRIGHT_MAP:
            unmapped.append(col)
    return unmapped


def normalizar_columnas_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica la normalización Cross-Bright a todo un DataFrame.
    Imprime advertencias si encuentra columnas nuevas no mapeadas.
    """
    import logging
    logger = logging.getLogger(__name__)

    unmapped = get_unmapped_columns(df)
    if unmapped:
        logger.warning(f"⚠️ Columnas no mapeadas detectadas: {unmapped}")
        logger.warning("Estas columnas se mantendrán con su nombre original (Principio de Preservación).")

    # Renombrar usando el mapa canónico
    new_cols = {col: normalise_header(col) for col in df.columns}
    return df.rename(columns=new_cols)
