"""
Módulo para el Análisis de Correlación entre Crecimiento de Matrícula y Rendimiento Académico
Issue 6.5: Determinar si programas con crecimiento exponencial de matrícula sufren caída en calidad
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import logging
from mapeo_columnas_saber_pro import aplicar_mapeo_columnas

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def cargar_datos(ruta_base: str = "datos/processed"):
    """
    Carga los datos de Saber Pro, SNIES Matriculados y SNIES Graduados
    """
    logger.info("Cargando datos para análisis de correlación matrícula-rendimiento...")
    
    # Cargar Saber Pro
    logger.info("Cargando Saber Pro...")
    saber_pro = pd.read_parquet(Path(ruta_base) / "saber_pro/saber_pro_consolidado.parquet")
    
    # Cargar SNIES Matriculados
    logger.info("Cargando SNIES Matriculados...")
    snies_matriculados = pd.read_parquet(Path(ruta_base) / "snies/snies_matriculados_limpio_consolidado.parquet")
    
    # Cargar SNIES Graduados (para contexto)
    logger.info("Cargando SNIES Graduados...")
    snies_graduados = pd.read_parquet(Path(ruta_base) / "snies/snies_graduados_consolidado.parquet")
    
    logger.info(f"Saber Pro: {saber_pro.shape[0]:,} registros")
    logger.info(f"SNIES Matriculados: {snies_matriculados.shape[0]:,} registros")
    logger.info(f"SNIES Graduados: {snies_graduados.shape[0]:,} registros")
    
    return saber_pro, snies_matriculados, snies_graduados


def preparar_saber_pro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara Saber Pro para el análisis
    - Aplica mapeo de columnas
    - Extrae año del periodo
    - Calcula puntaje promedio por módulo
    - Agrega por programa y año
    """
    # Aplicar mapeo de columnas primero
    df = aplicar_mapeo_columnas(df)
    
    df_prep = df.copy()
    
    # Extraer año (si no existe)
    if 'anio' not in df_prep.columns:
        df_prep['anio'] = df_prep['periodo'].astype(str).str[:4].astype(int)
    
    # Convertir codigo_snies_programa a numérico (si existe)
    if 'codigo_snies_programa' in df_prep.columns:
        df_prep['codigo_snies_programa'] = pd.to_numeric(df_prep['codigo_snies_programa'], errors='coerce')
        df_prep['codigo_snies_programa'] = df_prep['codigo_snies_programa'].astype('Int64')
    
    # Calcular puntaje promedio por estudiante
    modulos = ['punt_comuni_escrita', 'punt_razona_cuantitativa', 'punt_ingles', 'punt_lectura_critica', 'punt_comp_ciudadanas']
    df_prep['puntaje_promedio'] = df_prep[modulos].mean(axis=1, skipna=True)
    
    # Agregar por programa y año
    saber_agg = df_prep.groupby(['codigo_snies_programa', 'programa_academico', 'nombre_ies', 'anio']).agg(
        promedio_puntaje=('puntaje_promedio', 'mean'),
        total_presentados=('estu_consecutivo', 'nunique'),
        # Puntajes individuales por módulo
        promedio_comuni_escrita=('punt_comuni_escrita', 'mean'),
        promedio_razona_cuantitativo=('punt_razona_cuantitativa', 'mean'),
        promedio_ingles=('punt_ingles', 'mean'),
        promedio_lectura_critica=('punt_lectura_critica', 'mean'),
        promedio_comp_ciudadanas=('punt_comp_ciudadanas', 'mean')
    ).reset_index()
    
    logger.info(f"Saber Pro agregado: {saber_agg.shape[0]} registros (programa-año)")
    return saber_agg


def preparar_snies_matriculados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara SNIES Matriculados para el análisis
    - Convierte codigo_snies_programa
    - Agrega por programa y año
    """
    df_prep = df.copy()
    
    # Renombrar anio_proceso a anio
    df_prep = df_prep.rename(columns={'anio_proceso': 'anio'})
    
    # Convertir codigo_snies_programa
    df_prep['codigo_snies_programa'] = pd.to_numeric(df_prep['codigo_snies_programa'], errors='coerce')
    df_prep['codigo_snies_programa'] = df_prep['codigo_snies_programa'].astype('Int64')
    
    # Agregar por programa y año
    matriculados_agg = df_prep.groupby(['codigo_snies_programa', 'nombre_programa', 'nombre_institucion', 'anio']).agg(
        total_matriculados=('matriculados', 'sum')
    ).reset_index()
    
    # Renombrar para cruce
    matriculados_agg = matriculados_agg.rename(columns={'nombre_programa': 'programa_academico', 'nombre_institucion': 'nombre_ies'})
    
    logger.info(f"SNIES Matriculados agregados: {matriculados_agg.shape[0]} registros (programa-año)")
    return matriculados_agg


def cruzar_datos(saber_agg: pd.DataFrame, matriculados_agg: pd.DataFrame) -> pd.DataFrame:
    """
    Cruza Saber Pro con SNIES Matriculados por programa y año
    """
    logger.info("Cruzando Saber Pro con SNIES Matriculados...")
    
    # Cruce por codigo_snies_programa, programa_academico, nombre_ies y anio
    cruce = pd.merge(
        saber_agg,
        matriculados_agg,
        on=['codigo_snies_programa', 'programa_academico', 'nombre_ies', 'anio'],
        how='inner'  # Solo programas que aparecen en ambas fuentes
    )
    
    logger.info(f"Datos cruzados: {cruce.shape[0]} registros")
    return cruce


def calcular_crecimiento_matricula(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula tasas de crecimiento de matrícula por programa
    """
    logger.info("Calculando crecimiento de matrícula por programa...")
    
    # Ordenar por programa y año
    df = df.sort_values(['codigo_snies_programa', 'anio'])
    
    # Calcular crecimiento anual por programa
    df['matricula_anterior'] = df.groupby('codigo_snies_programa')['total_matriculados'].shift(1)
    df['crecimiento_absoluto'] = df['total_matriculados'] - df['matricula_anterior']
    df['tasa_crecimiento'] = np.where(
        df['matricula_anterior'] > 0,
        (df['total_matriculados'] - df['matricula_anterior']) / df['matricula_anterior'] * 100,
        np.nan
    )
    
    # Calcular crecimiento acumulado (desde el primer año)
    df['primer_anio'] = df.groupby('codigo_snies_programa')['anio'].transform('min')
    df['matricula_inicial'] = df.groupby(['codigo_snies_programa', 'primer_anio'])['total_matriculados'].transform('first')
    df['crecimiento_acumulado'] = np.where(
        df['matricula_inicial'] > 0,
        (df['total_matriculados'] - df['matricula_inicial']) / df['matricula_inicial'] * 100,
        np.nan
    )
    
    # Calcular promedio móvil de matrícula (3 años)
    df['matricula_promedio_movil'] = df.groupby('codigo_snies_programa')['total_matriculados'].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    
    logger.info("Crecimiento de matrícula calculado")
    return df


def calcular_correlaciones_temporales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula correlaciones entre crecimiento de matrícula y cambio en puntajes
    por programa a lo largo del tiempo
    """
    logger.info("Calculando correlaciones temporales por programa...")
    
    # Calcular cambio en puntajes
    df = df.sort_values(['codigo_snies_programa', 'anio'])
    df['puntaje_anterior'] = df.groupby('codigo_snies_programa')['promedio_puntaje'].shift(1)
    df['cambio_puntaje'] = df['promedio_puntaje'] - df['puntaje_anterior']
    
    # Calcular correlaciones por programa (solo para programas con suficientes datos)
    resultados = []
    programas_validos = df.groupby('codigo_snies_programa').size()
    programas_validos = programas_validos[programas_validos >= 3].index  # Mínimo 3 años de datos
    
    for codigo_prog in programas_validos:
        datos_prog = df[df['codigo_snies_programa'] == codigo_prog].dropna(subset=['tasa_crecimiento', 'cambio_puntaje'])
        
        if len(datos_prog) >= 3:
            # Correlación entre tasa de crecimiento y cambio en puntaje
            if datos_prog['tasa_crecimiento'].std() > 0 and datos_prog['cambio_puntaje'].std() > 0:
                corr_pearson, p_valor = stats.pearsonr(datos_prog['tasa_crecimiento'], datos_prog['cambio_puntaje'])
                corr_spearman, _ = stats.spearmanr(datos_prog['tasa_crecimiento'], datos_prog['cambio_puntaje'])
            else:
                corr_pearson = 0
                corr_spearman = 0
                p_valor = 1
            
            resultados.append({
                'codigo_snies_programa': codigo_prog,
                'programa_academico': datos_prog['programa_academico'].iloc[0],
                'nombre_ies': datos_prog['nombre_ies'].iloc[0],
                'correlacion_crecimiento_puntaje': corr_pearson,
                'correlacion_spearman': corr_spearman,
                'p_valor': p_valor,
                'anios_analisis': len(datos_prog),
                'crecimiento_promedio': datos_prog['tasa_crecimiento'].mean(),
                'cambio_puntaje_promedio': datos_prog['cambio_puntaje'].mean()
            })
    
    resultados_df = pd.DataFrame(resultados)
    
    # Ordenar por correlación (las más negativas primero - posible pérdida de calidad)
    resultados_df = resultados_df.sort_values('correlacion_crecimiento_puntaje')
    
    logger.info(f"Correlaciones calculadas para {len(resultados_df)} programas")
    return resultados_df


def identificar_programas_criticoss(df: pd.DataFrame, correlaciones: pd.DataFrame, 
                                    umbral_crecimiento: float = 50, 
                                    umbral_correlacion: float = -0.3) -> pd.DataFrame:
    """
    Identifica programas con crecimiento exponencial y posible pérdida de calidad
    
    Args:
        df: DataFrame con datos cruzados
        correlaciones: DataFrame con correlaciones por programa
        umbral_crecimiento: Porcentaje de crecimiento acumulado para considerar "exponencial"
        umbral_correlacion: Umbral de correlación negativa para considerar "pérdida de calidad"
    """
    logger.info(f"Identificando programas críticos (crecimiento > {umbral_crecimiento}%, correlación < {umbral_correlacion})...")
    
    # Programas con crecimiento exponencial
    crecimiento_max = df.groupby('codigo_snies_programa')['crecimiento_acumulado'].max().reset_index()
    crecimiento_max = crecimiento_max[crecimiento_max['crecimiento_acumulado'] > umbral_crecimiento]
    
    # Unir con correlaciones
    programas_crecimiento = pd.merge(crecimiento_max, correlaciones, on='codigo_snies_programa')
    
    # Filtrar por correlación negativa significativa
    programas_criticoss = programas_crecimiento[
        programas_crecimiento['correlacion_crecimiento_puntaje'] < umbral_correlacion
    ].copy()
    
    # Agregar información adicional
    info_adicional = df.groupby('codigo_snies_programa').agg(
        matricula_maxima=('total_matriculados', 'max'),
        anios_analisis=('anio', 'nunique')
    ).reset_index()
    
    programas_criticoss = pd.merge(programas_criticoss, info_adicional, on='codigo_snies_programa', how='left')
    
    # Ordenar por correlación (las más negativas primero)
    programas_criticoss = programas_criticoss.sort_values('correlacion_crecimiento_puntaje')
    
    logger.info(f"Programas críticos identificados: {len(programas_criticoss)}")
    return programas_criticoss


def estandarizar_area_conocimiento(area: str) -> str:
    """
    Estandariza nombres de áreas de conocimiento corrigiendo encoding y duplicados
    """
    if not isinstance(area, str):
        return area
    
    # Diccionario de corrección de áreas de conocimiento
    correcciones_areas = {
        # Corregir encoding (quitar tildes corruptos)
        'ADMINISTRACIÓN': 'ADMINISTRACIÓN',
        'AGRONOMÍA': 'AGRONOMÍA',
        'ANTROPOLOGÍA, ARTES LIBERALES': 'ANTROPOLOGÍA, ARTES LIBERALES',
        'ARTES PLÁSTICAS, VISUALES Y AFINES': 'ARTES PLÁSTICAS, VISUALES Y AFINES',
        'BACTERIOLOGÍA': 'BACTERIOLOGÍA',
        'BIBLIOTECOLOGÍA, OTROS DE CIENCIAS SOCIALES Y HUMANAS': 'BIBLIOTECOLOGÍA, OTROS DE CIENCIAS SOCIALES Y HUMANAS',
        'BIOLOGÍA, MICROBIOLOGÍA Y AFINES': 'BIOLOGÍA, MICROBIOLOGÍA Y AFINES',
        'CIENCIA POLÍTICA, RELACIONES INTERNACIONALES': 'CIENCIA POLÍTICA, RELACIONES INTERNACIONALES',
        'COMUNICACIÓN SOCIAL, PERIODISMO Y AFINES': 'COMUNICACIÓN SOCIAL, PERIODISMO Y AFINES',
        'CONTADURÍA PUBLICA': 'CONTADURÍA PÚBLICA',
        'CONTADURIA PUBLICA': 'CONTADURÍA PÚBLICA',
        'DEPORTES, EDUCACIÓN FÍSICA Y RECREACIÓN': 'DEPORTES, EDUCACIÓN FÍSICA Y RECREACIÓN',
        'DISEÑO': 'DISEÑO',
        'ECONOMÍA': 'ECONOMÍA',
        'EDUCACIÓN': 'EDUCACIÓN',
        'ENFERMERÍA': 'ENFERMERÍA',
        'FILOSOFÍA, TEOLOGÍA Y AFINES': 'FILOSOFÍA, TEOLOGÍA Y AFINES',
        'FÍSICA': 'FÍSICA',
        'FORMACIÓN RELACIONADA CON EL CAMPO MILITAR O POLICIAL': 'FORMACIÓN RELACIONADA CON EL CAMPO MILITAR O POLICIAL',
        'GEOGRAFÍA, HISTORIA': 'GEOGRAFÍA, HISTORIA',
        'GEOLOGÍA, OTROS PROGRAMAS DE CIENCIAS NATURALES': 'GEOLOGÍA, OTROS PROGRAMAS DE CIENCIAS NATURALES',
        'INGENIERÍA ADMINISTRATIVA Y AFINES': 'INGENIERÍA ADMINISTRATIVA Y AFINES',
        'INGENIERÍA AGROINDUSTRIAL, ALIMENTOS Y AFINES': 'INGENIERÍA AGROINDUSTRIAL, ALIMENTOS Y AFINES',
        'INGENIERÍA AGRÍCOLA, FORESTAL Y AFINES': 'INGENIERÍA AGRÍCOLA, FORESTAL Y AFINES',
        'INGENIERÍA AGRONÓMICA, PECUARIA Y AFINES': 'INGENIERÍA AGRONÓMICA, PECUARIA Y AFINES',
        'INGENIERÍA AMBIENTAL, SANITARIA Y AFINES': 'INGENIERÍA AMBIENTAL, SANITARIA Y AFINES',
        'INGENIERÍA BIOMÉDICA Y AFINES': 'INGENIERÍA BIOMÉDICA Y AFINES',
        'INGENIERÍA CIVIL Y AFINES': 'INGENIERÍA CIVIL Y AFINES',
        'INGENIERÍA DE MINAS, METALURGIA Y AFINES': 'INGENIERÍA DE MINAS, METALURGIA Y AFINES',
        'INGENIERÍA DE SISTEMAS, TELEMÁTICA Y AFINES': 'INGENIERÍA DE SISTEMAS, TELEMÁTICA Y AFINES',
        'INGENIERÍA ELÉCTRICA Y AFINES': 'INGENIERÍA ELÉCTRICA Y AFINES',
        'INGENIERÍA ELECTRÓNICA, TELECOMUNICACIONES Y AFINES': 'INGENIERÍA ELECTRÓNICA, TELECOMUNICACIONES Y AFINES',
        'INGENIERÍA INDUSTRIAL Y AFINES': 'INGENIERÍA INDUSTRIAL Y AFINES',
        'INGENIERÍA MECÁNICA Y AFINES': 'INGENIERÍA MECÁNICA Y AFINES',
        'INGENIERÍA QUÍMICA Y AFINES': 'INGENIERÍA QUÍMICA Y AFINES',
        'INSTRUMENTACIÓN QUIRÚRGICA': 'INSTRUMENTACIÓN QUIRÚRGICA',
        'LENGUAS MODERNAS, LITERATURA, LINGÜÍSTICA Y AFINES': 'LENGUAS MODERNAS, LITERATURA, LINGÜÍSTICA Y AFINES',
        'MATEMÁTICAS, ESTADÍSTICA Y AFINES': 'MATEMÁTICAS, ESTADÍSTICA Y AFINES',
        'MÚSICA': 'MÚSICA',
        'NUTRICIÓN Y DIETÉTICA': 'NUTRICIÓN Y DIETÉTICA',
        'ODONTOLOGÍA': 'ODONTOLOGÍA',
        'OPTOMETRÍA, OTROS PROGRAMAS DE CIENCIAS DE LA SALUD': 'OPTOMETRÍA, OTROS PROGRAMAS DE CIENCIAS DE LA SALUD',
        'OTRAS INGENIERÍAS': 'OTRAS INGENIERÍAS',
        'PSICOLOGÍA': 'PSICOLOGÍA',
        'QUÍMICA Y AFINES': 'QUÍMICA Y AFINES',
        'SOCIOLOGÍA, TRABAJO SOCIAL Y AFINES': 'SOCIOLOGÍA, TRABAJO SOCIAL Y AFINES',
        
        # Corregir versiones sin tildes (mapeo inverso)
        'ADMINISTRACION': 'ADMINISTRACIÓN',
        'AGRONOMIA': 'AGRONOMÍA',
        'ANTROPOLOGIA, ARTES LIBERALES': 'ANTROPOLOGÍA, ARTES LIBERALES',
        'ARTES PLASTICAS, VISUALES Y AFINES': 'ARTES PLÁSTICAS, VISUALES Y AFINES',
        'BACTERIOLOGIA': 'BACTERIOLOGÍA',
        'BIBLIOTECOLOGIA, OTROS DE CIENCIAS SOCIALES Y HUMANAS': 'BIBLIOTECOLOGÍA, OTROS DE CIENCIAS SOCIALES Y HUMANAS',
        'BIOLOGIA, MICROBIOLOGIA Y AFINES': 'BIOLOGÍA, MICROBIOLOGÍA Y AFINES',
        'CIENCIA POLITICA, RELACIONES INTERNACIONALES': 'CIENCIA POLÍTICA, RELACIONES INTERNACIONALES',
        'COMUNICACION SOCIAL, PERIODISMO Y AFINES': 'COMUNICACIÓN SOCIAL, PERIODISMO Y AFINES',
        'DEPORTES, EDUCACION FISICA Y RECREACION': 'DEPORTES, EDUCACIÓN FÍSICA Y RECREACIÓN',
        'DISENIO': 'DISEÑO',
        'ECONOMIA': 'ECONOMÍA',
        'EDUCACION': 'EDUCACIÓN',
        'ENFERMERIA': 'ENFERMERÍA',
        'FILOSOFIA, TEOLOGIA Y AFINES': 'FILOSOFÍA, TEOLOGÍA Y AFINES',
        'FISICA': 'FÍSICA',
        'FORMACION RELACIONADA CON EL CAMPO MILITAR O POLICIAL': 'FORMACIÓN RELACIONADA CON EL CAMPO MILITAR O POLICIAL',
        'GEOGRAFIA, HISTORIA': 'GEOGRAFÍA, HISTORIA',
        'GEOLOGIA, OTROS PROGRAMAS DE CIENCIAS NATURALES': 'GEOLOGÍA, OTROS PROGRAMAS DE CIENCIAS NATURALES',
        'INGENIERIA ADMINISTRATIVA Y AFINES': 'INGENIERÍA ADMINISTRATIVA Y AFINES',
        'INGENIERIA ADMNISTRATIVA Y AFINES': 'INGENIERÍA ADMINISTRATIVA Y AFINES',
        'INGENIERIA AGROINDUSTRIAL, ALIMENTOS Y AFINES': 'INGENIERÍA AGROINDUSTRIAL, ALIMENTOS Y AFINES',
        'INGENIERIA AGRICOLA, FORESTAL Y AFINES': 'INGENIERÍA AGRÍCOLA, FORESTAL Y AFINES',
        'INGENIERIA AGRONOMICA, PECUARIA Y AFINES': 'INGENIERÍA AGRONÓMICA, PECUARIA Y AFINES',
        'INGENIERIA AMBIENTAL, SANITARIA Y AFINES': 'INGENIERÍA AMBIENTAL, SANITARIA Y AFINES',
        'INGENIERIA BIOMEDICA Y AFINES': 'INGENIERÍA BIOMÉDICA Y AFINES',
        'INGENIERIA CIVIL Y AFINES': 'INGENIERÍA CIVIL Y AFINES',
        'INGENIERIA DE MINAS, METALURGIA Y AFINES': 'INGENIERÍA DE MINAS, METALURGIA Y AFINES',
        'INGENIERIA DE SISTEMAS, TELEMATICA Y AFINES': 'INGENIERÍA DE SISTEMAS, TELEMÁTICA Y AFINES',
        'INGENIERIA ELECTRICA Y AFINES': 'INGENIERÍA ELÉCTRICA Y AFINES',
        'INGENIERIA ELECTRONICA, TELECOMUNICACIONES Y AFINES': 'INGENIERÍA ELECTRÓNICA, TELECOMUNICACIONES Y AFINES',
        'INGENIERIA INDUSTRIAL Y AFINES': 'INGENIERÍA INDUSTRIAL Y AFINES',
        'INGENIERIA MECANICA Y AFINES': 'INGENIERÍA MECÁNICA Y AFINES',
        'INGENIERIA QUIMICA Y AFINES': 'INGENIERÍA QUÍMICA Y AFINES',
        'INSTRUMENTACION QUIRURGICA': 'INSTRUMENTACIÓN QUIRÚRGICA',
        'LENGUAS MODERNAS, LITERATURA, LINGUISTICA Y AFINES': 'LENGUAS MODERNAS, LITERATURA, LINGÜÍSTICA Y AFINES',
        'MATEMATICAS, ESTADISTICA Y AFINES': 'MATEMÁTICAS, ESTADÍSTICA Y AFINES',
        'MUSICA': 'MÚSICA',
        'NUTRICION Y DIETETICA': 'NUTRICIÓN Y DIETÉTICA',
        'ODONTOLOGIA': 'ODONTOLOGÍA',
        'OPTOMETRIA, OTROS PROGRAMAS DE CIENCIAS DE LA SALUD': 'OPTOMETRÍA, OTROS PROGRAMAS DE CIENCIAS DE LA SALUD',
        'OTRAS INGENIERIAS': 'OTRAS INGENIERÍAS',
        'PSICOLOGIA': 'PSICOLOGÍA',
        'QUIMICA Y AFINES': 'QUÍMICA Y AFINES',
        'SOCIOLOGIA, TRABAJO SOCIAL Y AFINES': 'SOCIOLOGÍA, TRABAJO SOCIAL Y AFINES',
        
        # Corregir errores tipográficos
        'ATES PLASTICAS, VISUALES Y AFINES': 'ARTES PLÁSTICAS, VISUALES Y AFINES',
        'SALUD PUBLICA': 'SALUD PÚBLICA',
    }
    
    # Aplicar corrección
    area_upper = area.strip().upper()
    return correcciones_areas.get(area_upper, area_upper)


def analisis_por_area_conocimiento(saber_pro_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Realiza análisis de correlación agregado por área de conocimiento
    Usando núcleo de pregrado como proxy de área
    """
    logger.info("Realizando análisis por área de conocimiento...")
    
    # Preparar datos de Saber Pro
    df = saber_pro_raw.copy()
    df['anio'] = df['periodo'].astype(str).str[:4].astype(int)
    
    # Verificar nombre de columna para núcleo de pregrado
    col_nucleo = 'nucleo_pregrado'
    if col_nucleo not in df.columns:
        # Buscar columna alternativa
        col_alternativas = ['estu_nucleo_pregrado', 'nucleo', 'area_conocimiento']
        for alt in col_alternativas:
            if alt in df.columns:
                col_nucleo = alt
                break
    
    if col_nucleo not in df.columns:
        logger.warning("No se encontró columna de núcleo de pregrado, omitiendo análisis por área")
        return pd.DataFrame()
    
    # Estandarizar nombres de áreas de conocimiento antes de agrupar
    df[col_nucleo] = df[col_nucleo].apply(estandarizar_area_conocimiento)
    
    # Agrupar por núcleo de pregrado y año
    # Verificar nombre de columna para puntaje
    col_puntaje = 'punt_comuni_escrita'
    if col_puntaje not in df.columns:
        # Buscar columna alternativa
        col_alternativas = ['mod_comuni_escrita_punt', 'mod_comuni_escrita_punt', 'punt_global']
        for alt in col_alternativas:
            if alt in df.columns:
                col_puntaje = alt
                break
    
    df_area = df.groupby([col_nucleo, 'anio']).agg(
        promedio_puntaje=(col_puntaje, lambda x: x.mean()),
        total_presentados=('estu_consecutivo', 'nunique')
    ).reset_index()
    
    # Renombrar columna de núcleo a area_conocimiento
    df_area = df_area.rename(columns={col_nucleo: 'area_conocimiento'})
    
    # Calcular crecimiento de presentaciones por área (proxy de matrícula)
    df_area = df_area.sort_values(['area_conocimiento', 'anio'])
    df_area['presentados_anterior'] = df_area.groupby('area_conocimiento')['total_presentados'].shift(1)
    df_area['tasa_crecimiento'] = np.where(
        df_area['presentados_anterior'] > 0,
        (df_area['total_presentados'] - df_area['presentados_anterior']) / df_area['presentados_anterior'] * 100,
        np.nan
    )
    df_area['cambio_puntaje'] = df_area.groupby('area_conocimiento')['promedio_puntaje'].diff()
    
    # Calcular correlación por área
    areas_validas = df_area.groupby('area_conocimiento').size()
    areas_validas = areas_validas[areas_validas >= 3].index
    
    resultados_areas = []
    for area in areas_validas:
        datos_area = df_area[df_area['area_conocimiento'] == area].dropna(subset=['tasa_crecimiento', 'cambio_puntaje'])
        
        if len(datos_area) >= 3:
            if datos_area['tasa_crecimiento'].std() > 0 and datos_area['cambio_puntaje'].std() > 0:
                corr, p_valor = stats.pearsonr(datos_area['tasa_crecimiento'], datos_area['cambio_puntaje'])
            else:
                corr = 0
                p_valor = 1
            
            resultados_areas.append({
                'area_conocimiento': area,
                'correlacion_crecimiento_puntaje': corr,
                'p_valor': p_valor,
                'anios_analisis': len(datos_area)
            })
    
    resultados_areas_df = pd.DataFrame(resultados_areas)
    resultados_areas_df = resultados_areas_df.sort_values('correlacion_crecimiento_puntaje')
    
    logger.info(f"Análisis por área completado: {len(resultados_areas_df)} áreas")
    return resultados_areas_df


def generar_alertas_tempranas(programas_criticoss: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """
    Genera reporte de alertas tempranas de pérdida de calidad por sobrepoblación
    """
    logger.info(f"Generando alertas tempranas (top {n})...")
    
    # Seleccionar los programas con mayor riesgo
    alertas = programas_criticoss.head(n).copy()
    
    # Clasificar nivel de riesgo
    alertas['nivel_riesgo'] = np.where(
        alertas['correlacion_crecimiento_puntaje'] < -0.5,
        'ALTO',
        np.where(alertas['correlacion_crecimiento_puntaje'] < -0.3, 'MEDIO', 'BAJO')
    )
    
    # Ordenar por nivel de riesgo y correlación
    alertas = alertas.sort_values(['nivel_riesgo', 'correlacion_crecimiento_puntaje'])
    
    logger.info(f"Alertas tempranas generadas: {len(alertas)}")
    return alertas


def guardar_resultados(cruce: pd.DataFrame, correlaciones: pd.DataFrame, 
                       programas_criticoss: pd.DataFrame, alertas: pd.DataFrame,
                       areas_analisis: pd.DataFrame,
                       ruta_salida: str = "datos/processed"):
    """
    Guarda los resultados del análisis
    """
    logger.info("Guardando resultados del análisis de correlación...")
    
    ruta = Path(ruta_salida)
    ruta.mkdir(parents=True, exist_ok=True)
    
    # Guardar datos cruzados
    cruce.to_parquet(ruta / "cruce_matricula_rendimiento.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'cruce_matricula_rendimiento.parquet'}")
    
    # Guardar correlaciones por programa
    correlaciones.to_parquet(ruta / "correlaciones_por_programa.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'correlaciones_por_programa.parquet'}")
    
    # Guardar programas críticos
    programas_criticoss.to_parquet(ruta / "programas_criticoss.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'programas_criticoss.parquet'}")
    
    # Guardar alertas tempranas
    alertas.to_parquet(ruta / "alertas_tempranas.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'alertas_tempranas.parquet'}")
    
    # Guardar análisis por área
    areas_analisis.to_parquet(ruta / "analisis_por_area_conocimiento.parquet", index=False)
    logger.info(f"Guardado: {ruta / 'analisis_por_area_conocimiento.parquet'}")


def ejecutar_analisis_correlacion():
    """
    Función principal que ejecuta todo el pipeline de análisis
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISIS DE CORRELACIÓN MATRÍCULA-RENDIMIENTO")
    logger.info("=" * 60)
    
    # 1. Cargar datos
    saber_pro, snies_matriculados, snies_graduados = cargar_datos()
    
    # 2. Preparar datos
    saber_agg = preparar_saber_pro(saber_pro)
    matriculados_agg = preparar_snies_matriculados(snies_matriculados)
    
    # 3. Cruzar datos
    cruce = cruzar_datos(saber_agg, matriculados_agg)
    
    # 4. Calcular crecimiento de matrícula
    cruce = calcular_crecimiento_matricula(cruce)
    
    # 5. Calcular correlaciones temporales
    correlaciones = calcular_correlaciones_temporales(cruce)
    
    # 6. Identificar programas críticos
    programas_criticoss = identificar_programas_criticoss(cruce, correlaciones)
    
    # 7. Análisis por área de conocimiento
    areas_analisis = analisis_por_area_conocimiento(saber_pro)
    
    # 8. Generar alertas tempranas
    alertas = generar_alertas_tempranas(programas_criticoss, n=20)
    
    # 9. Guardar resultados
    guardar_resultados(cruce, correlaciones, programas_criticoss, alertas, areas_analisis)
    
    logger.info("=" * 60)
    logger.info("ANÁLISIS DE CORRELACIÓN COMPLETADO EXITOSAMENTE")
    logger.info("=" * 60)
    
    return cruce, correlaciones, programas_criticoss, alertas, areas_analisis


if __name__ == "__main__":
    # Ejecutar análisis
    cruce, correlaciones, programas_criticoss, alertas, areas_analisis = ejecutar_analisis_correlacion()
    
    # Imprimir resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL ANÁLISIS DE CORRELACIÓN MATRÍCULA-RENDIMIENTO")
    print("=" * 60)
    
    print(f"\nTotal programas analizados: {len(correlaciones)}")
    print(f"Programas con crecimiento exponencial: {len(programas_criticoss)}")
    print(f"Alertas tempranas generadas: {len(alertas)}")
    
    print(f"\nTop 10 programas con mayor riesgo de pérdida de calidad:")
    columns_to_show = ['programa_academico', 'nombre_ies', 'crecimiento_acumulado', 
                       'correlacion_crecimiento_puntaje', 'nivel_riesgo']
    print(alertas[columns_to_show].head(10).to_string(index=False))
    
    print(f"\nCorrelaciones por área de conocimiento:")
    print(areas_analisis.sort_values('correlacion_crecimiento_puntaje').head(10).to_string(index=False))