"""
limpieza_snies.py — Limpieza y normalización Cross-Bright de datos SNIES
Lee los archivos RAW de graduados y matriculados (datos/raw/snies/),
aplica el diccionario Cross-Bright de header_utils_snies.py para
unificar nombres de columnas, castea las métricas a int, y exporta
archivos limpios consolidados a datos/processed/snies/.
"""
import sys
import unicodedata
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.ingesta.header_utils_snies import (
    normalise_header_snies,
    get_unmapped_columns,
    _slugify,
)

RAW_SNIES       = BASE_DIR / "datos" / "raw" / "snies"
PROCESSED_SNIES = BASE_DIR / "datos" / "processed" / "snies"

# Columnas de texto categórico donde se corrige mojibake y se deduplicanvariantes
_COLS_CATEGORICAS = [
    'area_conocimiento', 'nivel_academico', 'nivel_formacion', 'metodologia',
    'nombre_programa', 'nombre_institucion', 'sector_ies', 'caracter_ies',
    'departamento_ies', 'municipio_ies', 'departamento_programa', 'municipio_programa',
]


def _fix_mojibake(s: str) -> str:
    """
    Corrige texto con mojibake latin-1/utf-8 y normaliza acentos a ASCII.
    Ejemplo: 'ECONOM\xcdA' → 'ECONOMIA'
    """
    if not isinstance(s, str):
        return s
    # Intento 1: es latin-1 reinterpretado como utf-8
    try:
        s = s.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    # Quitar acentos para unificar variantes con/sin tilde
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')


# Columnas canónicas que DEBEN existir en el resultado final
CORE_COLUMNS = {
    'graduados':    ['anio_proceso', 'semestre', 'codigo_institucion', 'nombre_institucion',
                     'codigo_snies_programa', 'nombre_programa', 'graduados'],
    'matriculados': ['anio_proceso', 'semestre', 'codigo_institucion', 'nombre_institucion',
                     'codigo_snies_programa', 'nombre_programa', 'matriculados'],
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza las columnas usando el diccionario Cross-Bright de SNIES.
    Pasos:
      1. Limpia newlines, espacios extra del nombre de columna.
      2. Aplica el slug -> canonical del diccionario.
      3. Elimina columnas duplicadas (conserva la primera).
    """
    # Paso 1: Limpiar nombres de columna (newlines, espacios multiples)
    clean_names = {}
    for col in df.columns:
        cleaned = str(col).replace('\n', ' ').replace('\r', ' ')
        # Eliminar sufijos como "Matriculados 2015" → "Matriculados"
        import re
        cleaned = re.sub(r'\s+\d{4}$', '', cleaned).strip()
        clean_names[col] = cleaned
    df = df.rename(columns=clean_names)

    # Paso 2: Aplicar Cross-Bright normalisation
    new_cols = {}
    for col in df.columns:
        canonical = normalise_header_snies(col)
        new_cols[col] = canonical
    df = df.rename(columns=new_cols)

    # Paso 3: Eliminar columnas duplicadas (conservar primera ocurrencia)
    df = df.loc[:, ~df.columns.duplicated()]

    return df


def _cast_metrics(df: pd.DataFrame, categoria: str) -> pd.DataFrame:
    """Castea las columnas de métricas y claves a tipos numéricos."""
    # Métrica principal (graduados o matriculados)
    if categoria in df.columns:
        df[categoria] = pd.to_numeric(df[categoria], errors='coerce').fillna(0).astype(int)
    else:
        logger.warning(f"   Columna '{categoria}' no encontrada tras normalización.")

    # Semestre
    if 'semestre' in df.columns:
        df['semestre'] = pd.to_numeric(df['semestre'], errors='coerce').fillna(1).astype(int)

    # Año
    if 'anio_proceso' in df.columns:
        df['anio_proceso'] = pd.to_numeric(df['anio_proceso'], errors='coerce').fillna(0).astype(int)

    # Códigos numéricos
    for col in ['codigo_institucion', 'codigo_snies_programa', 'codigo_depto_ies',
                'codigo_mcpio_ies', 'codigo_depto_programa', 'codigo_mcpio_programa',
                'id_sector', 'id_caracter', 'id_genero', 'id_nucleo',
                'id_area_conocimiento', 'id_nivel_formacion', 'id_metodologia']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def procesar_categoria(categoria: str):
    """Procesa graduados o matriculados desde los RAW individuales."""
    categoria_path = RAW_SNIES / categoria
    if not categoria_path.exists():
        logger.error(f"No existe la ruta {categoria_path}")
        return

    archivos = []
    for year_dir in sorted(categoria_path.iterdir()):
        if year_dir.is_dir():
            for f in year_dir.glob("*.parquet"):
                archivos.append(f)

    logger.info(f"Archivos {categoria} encontrados: {len(archivos)}")
    frames = []

    for archivo in archivos:
        anio = archivo.parent.name
        logger.info(f"   Cargando {archivo.name} (anio={anio})...")
        try:
            df = pd.read_parquet(archivo)

            # 1. Normalizar columnas con Cross-Bright
            df = _normalise_columns(df)

            # 2. Inyectar año si no existe
            if 'anio_proceso' not in df.columns:
                df['anio_proceso'] = anio

            # 3. Auditoría: columnas no mapeadas
            unmapped = get_unmapped_columns(df)
            if unmapped:
                logger.info(f"      Columnas preservadas (no mapeadas): {unmapped}")

            frames.append(df)
            logger.info(f"      OK: {len(df):,} registros")
        except Exception as e:
            logger.error(f"      ERROR en {archivo.name}: {e}")

    if not frames:
        logger.error(f"No se cargó ningún archivo de {categoria}.")
        return

    # Concatenar
    logger.info(f"Concatenando {len(frames)} archivos de {categoria}...")
    df_all = pd.concat(frames, ignore_index=True)
    logger.info(f"Total registros crudos: {len(df_all):,}")

    # Casteo de métricas
    logger.info("Casteando metricas a tipos numericos...")
    df_all = _cast_metrics(df_all, categoria)

    # Normalizar textos en columnas string
    logger.info("Normalizando textos (fix mojibake + UPPER + STRIP)...")
    text_cols = df_all.select_dtypes(include=['object']).columns

    # Paso 1: corregir mojibake y eliminar acentos en columnas categóricas clave
    cols_moji = [c for c in _COLS_CATEGORICAS if c in df_all.columns]
    for col in cols_moji:
        df_all[col] = df_all[col].map(
            lambda x: _fix_mojibake(x) if isinstance(x, str) else x
        )
    if cols_moji:
        logger.info(f"   Mojibake corregido en: {cols_moji}")

    # Paso 2: UPPER + STRIP en todas las columnas texto
    for col in text_cols:
        df_all[col] = df_all[col].astype(str).str.upper().str.strip()

    # Paso 3a: Convertir a NULL los valores centinela del SNIES que no aportan información
    # ('SIN INFORMACIÓN' → NULL, 'SIN CLASIFICAR' → NULL, etc.)
    _SIN_INFO_VALS = [
        'NAN', 'NONE', 'NULL', '',
        'SIN INFORMACION', 'SIN INFORMACIÓN', 'SIN CLASIFICAR',
        'SIN INFO', 'SIN DATO', 'NO REPORTA', 'NO APLICA',
    ]
    df_all[text_cols] = df_all[text_cols].replace(_SIN_INFO_VALS, np.nan)

    # Paso 3b: Normalizar sector_ies: 'PRIVADA' → 'PRIVADO' (variante de género)
    if 'sector_ies' in df_all.columns:
        df_all['sector_ies'] = df_all['sector_ies'].replace({'PRIVADA': 'PRIVADO'})

    # Paso 3c: Normalizar area_conocimiento — eliminar comas y espacios múltiples
    #          para unificar variantes como "ECONOMIA, ADMINISTRACION..." vs "ECONOMIA ADMINISTRACION..."
    if 'area_conocimiento' in df_all.columns:
        def _norm_area(s):
            if not isinstance(s, str):
                return s
            # Eliminar comas, puntos y normalizar espacios
            s = s.replace(',', ' ').replace('.', ' ')
            s = ' '.join(s.split())  # colapsar espacios múltiples
            return s
        df_all['area_conocimiento'] = df_all['area_conocimiento'].map(_norm_area)
        logger.info(f"   area_conocimiento normalizada → {df_all['area_conocimiento'].nunique()} valores únicos")

    # Paso 3d: Normalizar nivel_formacion — unificar variantes de género y truncados
    #          'UNIVERSITARIA' = 'UNIVERSITARIO', 'TECNOLOGICA' = 'TECNOLOGICO', etc.
    #          También corrige valores truncados por límite de caracteres en fuentes SNIES.
    #          Se elige la forma masculina como canónica (más frecuente en SNIES reciente).
    if 'nivel_formacion' in df_all.columns:
        import re
        # Primero: correcciones de valores truncados (antes del replace por regex)
        _NF_TRUNCATED = {
            'ESPECIALIZACION TECNICO PROFESION': 'ESPECIALIZACION TECNICO PROFESIONAL',
            'ESPECIALIZACION TECNICO PROFESI':   'ESPECIALIZACION TECNICO PROFESIONAL',
        }
        df_all['nivel_formacion'] = df_all['nivel_formacion'].replace(_NF_TRUNCATED)

        # Luego: unificación de variantes de género (femenino → masculino canónico)
        _NF_GENDER_MAP = {
            r'\bUNIVERSITARIA\b':      'UNIVERSITARIO',
            r'\bTECNOLOGICA\b':        'TECNOLOGICO',
            r'\bTECNICA\b':            'TECNICO',
            r'\bPROFESIONAL\b':        'PROFESIONAL',  # ya es neutro
        }
        for pat, repl in _NF_GENDER_MAP.items():
            df_all['nivel_formacion'] = df_all['nivel_formacion'].str.replace(
                pat, repl, regex=True, case=False
            )
        logger.info(f"   nivel_formacion normalizada → {df_all['nivel_formacion'].nunique()} valores únicos")
        logger.info(f"   Valores: {sorted(df_all['nivel_formacion'].dropna().unique().tolist())}")

    # Paso 3: deduplicar registros exactos (misma combinación tras normalización)
    antes_dedup = len(df_all)
    df_all = df_all.drop_duplicates()
    dupes_elim = antes_dedup - len(df_all)
    if dupes_elim > 0:
        logger.info(f"   Duplicados exactos eliminados tras normalización: {dupes_elim:,}")

    # Filtrar rango de años válido
    df_all = df_all[df_all['anio_proceso'].between(2014, 2025)]

    # Verificar columnas core
    logger.info("Verificando columnas core...")
    for col in CORE_COLUMNS[categoria]:
        if col not in df_all.columns:
            logger.warning(f"   FALTA columna core: {col}")

    # Resumen por año
    logger.info(f"\n--- RESUMEN {categoria.upper()} POR AÑO ---")
    resumen = df_all.groupby('anio_proceso')[categoria].sum()
    for anio, total in resumen.items():
        logger.info(f"   {anio}: {total:>12,}")

    # Exportar
    PROCESSED_SNIES.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_SNIES / f"snies_{categoria}_limpio_consolidado.parquet"
    df_all.to_parquet(out_path, index=False)
    logger.info(f"\nExportado: {out_path}")
    logger.info(f"   Filas: {len(df_all):,}  |  Columnas: {len(df_all.columns)}")
    logger.info(f"   Columnas: {sorted(df_all.columns.tolist())}")


def limpieza_snies():
    """Punto de entrada principal."""
    logger.info("=" * 70)
    logger.info("  LIMPIEZA SNIES — Cross-Bright Pipeline")
    logger.info("=" * 70)
    PROCESSED_SNIES.mkdir(parents=True, exist_ok=True)

    for cat in ['graduados', 'matriculados']:
        logger.info(f"\n{'='*70}")
        logger.info(f"  PROCESANDO: {cat.upper()}")
        logger.info(f"{'='*70}")
        procesar_categoria(cat)


# Alias para compatibilidad con el pipeline anterior
limpieza_snies_ultra_corregida = limpieza_snies


if __name__ == "__main__":
    limpieza_snies()
import pandas as pd
import numpy as np
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent.parent.parent
RAW_SNIES = BASE_DIR / "datos" / "raw" / "snies"
PROCESSED_SNIES = BASE_DIR / "datos" / "processed" / "snies"

def limpieza_snies_ultra_corregida():
    """
    Limpieza ULTRA corregida de datos SNIES
    Maneja nombres de columnas problemáticos y duplicados
    """
    print("--- INICIANDO LIMPIEZA ULTRA CORREGIDA DE DATOS SNIES ---")
    
    # Crear directorio de salida
    PROCESSED_SNIES.mkdir(parents=True, exist_ok=True)
    
    # Procesar cada categoría por separado
    categorias = ['graduados', 'matriculados']
    
    for categoria in categorias:
        print(f"\n--- PROCESANDO {categoria.upper()} ---")
        procesar_categoria_ultra_corregida(categoria)

def procesar_categoria_ultra_corregida(categoria):
    """
    Procesa una categoría específica de SNIES con manejo robusto de columnas
    """
    # Listar archivos de la categoría
    categoria_path = RAW_SNIES / categoria
    if not categoria_path.exists():
        print(f"   No existe la categoría {categoria}")
        return
    
    archivos_categoria = []
    for year_dir in categoria_path.iterdir():
        if year_dir.is_dir():
            for archivo in year_dir.glob("*.parquet"):
                archivos_categoria.append(archivo)
    
    print(f"   Archivos {categoria} encontrados: {len(archivos_categoria)}")
    
    lista_dataframes = []
    
    # Cargar y procesar cada archivo de la categoría
    for archivo in archivos_categoria:
        print(f"   Cargando {archivo.name}...")
        try:
            # Leer el archivo parquet
            df_temp = pd.read_parquet(archivo)
            
            # Para matriculados, saltar las primeras 2 filas que son metadata
            if categoria == 'matriculados' and len(df_temp) > 2:
                # Usar la fila 2 como header y eliminar filas 0-1
                nuevos_headers = df_temp.iloc[2].tolist()
                df_temp = df_temp[3:].reset_index(drop=True)
                df_temp.columns = nuevos_headers
            
            # Extraer el año del directorio
            anio = archivo.parent.name
            df_temp['anio_proceso'] = anio
            
            # Procesar el dataframe con manejo robusto de columnas
            df_temp = procesar_dataframe_ultra_corregido(df_temp, categoria)
            
            lista_dataframes.append(df_temp)
            print(f"      OK {len(df_temp)} registros cargados.")
        except Exception as e:
            print(f"      ERROR en {archivo.name}: {e}")
    
    # Unir todos los dataframes de la categoría
    if lista_dataframes:
        print(f"\n   Concatenando {len(lista_dataframes)} archivos de {categoria}...")
        df_consolidado = pd.concat(lista_dataframes, ignore_index=True)
        print(f"   Registros consolidados de {categoria}: {len(df_consolidado)}")
        
        # --- PASO 1: Limpieza de Texto ---
        print("   Normalizando textos...")
        columnas_texto = df_consolidado.select_dtypes(include=['object']).columns
        for col in columnas_texto:
            df_consolidado[col] = df_consolidado[col].astype(str).str.upper().str.strip()

        # --- PASO 2: Tratamiento de Valores Nulos ---
        # Reemplazar valores nulos con NaN (no con 'SIN_DATOS') para manejo correcto en tablas de hechos
        df_consolidado[columnas_texto] = df_consolidado[columnas_texto].replace(['NAN', 'NONE', 'NULL', ''], np.nan)
        columnas_num = df_consolidado.select_dtypes(include=[np.number]).columns
        df_consolidado[columnas_num] = df_consolidado[columnas_num].fillna(0)

        # --- PASO 3: Normalización EXTREMA de nombres de columnas ---
        print("   Normalizando nombres de columnas...")
        df_consolidado = normalizar_nombres_columnas_extrema(df_consolidado)
        
        # --- PASO 4: Mapeo de columnas normalizadas a nombres estandar ---
        print("   Mapeando columnas normalizadas a nombres estandar...")
        
        # Los nombres exactos despues de normalizar (incluyendo caracteres raros)
        mapeo_columnas_normalizadas = {
            # Columnas de institucion
            'instituci_n_de_educaci_n_superior_ies': 'inst_nombre_institucion',
            'institucion_de_educacion_superior_ies': 'inst_nombre_institucion',
            'ies': 'inst_nombre_institucion',
            # Columnas de programa
            'programa_acad_mico': 'estu_prgm_academico',
            'programa_academico': 'estu_prgm_academico',
            # Columnas de codigo
            'c_digo_de_la_instituci_n': 'inst_codigo_institucion',
            'codigo_de_la_institucion': 'inst_codigo_institucion',
            'c_digo_snies_del_programa': 'prgm_codigo_snies',
            'codigo_snies_del_programa': 'prgm_codigo_snies',
            # Anio
            'anio_proceso': 'anio_proceso'
        }
        
        # Renombrar columnas segun el mapeo
        for col_original, col_nueva in mapeo_columnas_normalizadas.items():
            if col_original in df_consolidado.columns:
                df_consolidado = df_consolidado.rename(columns={col_original: col_nueva})
                print(f"      Renombrada columna: {col_original} -> {col_nueva}")
        
        # --- PASO 5: Validación y creación de columnas clave ---
        print("   Validando columnas clave...")
        columnas_clave = ['inst_nombre_institucion', 'estu_prgm_academico', 'anio_proceso']
        
        # Crear columnas clave si no existen
        for col in columnas_clave:
            if col not in df_consolidado.columns:
                print(f"      Advertencia: Columna clave '{col}' no encontrada, creando con valor por defecto")
                df_consolidado[col] = 'SIN_DATOS'

        # --- PASO 5: Cuadratura de datasets ---
        print("   Realizando cuadratura...")
        df_consolidado = cuadrar_datasets_ultra_corregido(df_consolidado)
        
        # --- PASO 6: Exportación Final ---
        ruta_salida = PROCESSED_SNIES / f"snies_{categoria}_limpio_consolidado.parquet"
        print(f"   Guardando {categoria} en: {ruta_salida}")
        df_consolidado.to_parquet(ruta_salida, index=False)
        
        print(f"   COMPLETADO: {categoria.upper()}")
        print(f"      Archivo generado: {ruta_salida}")
        print(f"      Registros procesados: {len(df_consolidado)}")
        print(f"      Columnas: {len(df_consolidado.columns)}")
    else:
        print(f"\n   No se cargó ningún archivo de {categoria}. Verifica los archivos en la carpeta raw/snies/{categoria}/")

def procesar_dataframe_ultra_corregido(df, categoria):
    """
    Procesa un dataframe de una categoría específica con manejo robusto de columnas
    """
    # Manejar columnas duplicadas
    df = manejar_columnas_duplicadas_ultra_corregido(df, categoria)
    
    # Normalizar nombres de columnas
    df = normalizar_nombres_columnas_extrema(df)
    
    return df

def manejar_columnas_duplicadas_ultra_corregido(df, categoria):
    """
    Maneja columnas duplicadas renombrándolas de forma única para una categoría
    """
    # Identificar columnas duplicadas
    columnas_duplicadas = df.columns.duplicated()
    if columnas_duplicadas.any():
        print(f"      Columnas duplicadas detectadas: {sum(columnas_duplicadas)}")
        
        # Renombrar columnas duplicadas
        nuevos_nombres = []
        contador_duplicados = {}
        
        for col in df.columns:
            if col in contador_duplicados:
                contador_duplicados[col] += 1
                nuevo_nombre = f"{col}_{contador_duplicados[col]}_{categoria}"
            else:
                contador_duplicados[col] = 0
                nuevo_nombre = f"{col}_{categoria}"
            nuevos_nombres.append(nuevo_nombre)
        
        df.columns = nuevos_nombres
        print(f"      Columnas renombradas exitosamente")
    
    return df

def normalizar_nombres_columnas_extrema(df):
    """
    Normaliza nombres de columnas de forma extrema para evitar cualquier problema
    """
    nuevos_nombres = []
    
    for col in df.columns:
        # Convertir a string y eliminar caracteres problemáticos
        col_str = str(col)
        
        # Reemplazar caracteres especiales y símbolos
        col_limpio = re.sub(r'[^a-zA-Z0-9_]', '_', col_str)
        
        # Eliminar múltiples guiones bajos consecutivos
        col_limpio = re.sub(r'_+', '_', col_limpio)
        
        # Eliminar guiones bajos al inicio y final
        col_limpio = col_limpio.strip('_')
        
        # Convertir a minúsculas
        col_limpio = col_limpio.lower()
        
        # Si el nombre está vacío o solo tiene guiones, usar un nombre genérico
        if not col_limpio or col_limpio == '_':
            col_limpio = f'columna_{len(nuevos_nombres)}'
        
        nuevos_nombres.append(col_limpio)
    
    df.columns = nuevos_nombres
    return df

def cuadrar_datasets_ultra_corregido(df):
    """
    Realiza cuadratura de datasets para asegurar consistencia
    """
    print("      Cuadrando datasets...")
    
    # 1. Asegurar consistencia en valores de columnas clave
    if 'inst_nombre_institucion' in df.columns:
        # Normalizar nombres de instituciones
        df['inst_nombre_institucion'] = df['inst_nombre_institucion'].str.replace(r'\s+', ' ', regex=True)
    
    if 'estu_prgm_academico' in df.columns:
        # Normalizar nombres de programas
        df['estu_prgm_academico'] = df['estu_prgm_academico'].str.replace(r'\s+', ' ', regex=True)
    
    # 2. Validar rangos de años
    if 'anio_proceso' in df.columns:
        try:
            df['anio_proceso'] = pd.to_numeric(df['anio_proceso'], errors='coerce')
            df = df[df['anio_proceso'].between(2015, 2025)]
            print(f"      Años validados: {df['anio_proceso'].min()} - {df['anio_proceso'].max()}")
        except:
            print("      No se pudo validar el rango de años")
    
    print(f"      Cuadratura completada: {len(df)} registros finales")
    return df

if __name__ == "__main__":
    limpieza_snies_ultra_corregida()
