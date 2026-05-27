"""
Módulo de mapeo de columnas del dataset Saber Pro consolidado

Este módulo contiene el mapeo entre los nombres de columnas del nuevo dataset
consolidado (2012-2024) y los nombres esperados por los scripts de análisis existentes.
"""

# Mapeo de columnas: nombre_nuevo -> nombre_esperado
MAPEO_COLUMNAS = {
    # Identificadores básicos
    'estu_consecutivo': 'estu_consecutivo',  # Ya tiene el mismo nombre
    'periodo': 'periodo',
    'anio': 'anio',
    
    # Departamento y municipio de presentación
    'estu_depto_presentacion': 'depto_presentacion',
    'estu_cod_depto_presentacion': 'cod_depto_presentacion',
    'estu_mcpio_presentacion': 'mcpio_presentacion',
    'estu_cod_mcpio_presentacion': 'cod_mcpio_presentacion',
    
    # Departamento y municipio de residencia
    'estu_depto_reside': 'depto_residencia',
    'estu_cod_reside_depto': 'cod_depto_residencia',
    'estu_mcpio_reside': 'mcpio_residencia',
    'estu_cod_reside_mcpio': 'cod_mcpio_residencia',
    
    # Información de la IES
    'inst_nombre_institucion': 'nombre_ies',
    'inst_cod_institucion': 'codigo_ies',
    'inst_caracter_academico': 'caracter_ies',
    'inst_origen': 'origen_ies',
    'estu_inst_departamento': 'depto_ies',
    'estu_inst_codmunicipio': 'codigo_mcpio_ies',
    'estu_inst_municipio': 'mcpio_ies',
    
    # Información del programa académico
    'estu_prgm_academico': 'programa_academico',
    'estu_snies_prgmacademico': 'codigo_snies_programa',
    'estu_prgm_departamento': 'depto_programa',
    'estu_prgm_codmunicipio': 'codigo_mcpio_programa',
    'estu_prgm_municipio': 'mcpio_programa',
    'estu_nivel_prgm_academico': 'nivel_programa',
    'estu_nucleo_pregrado': 'nucleo_pregrado',
    'estu_metodo_prgm': 'metodologia_programa',
    
    # Características del estudiante
    'estu_genero': 'genero',
    'estu_etnia': 'estu_etnia',
    'estu_discapacidad': 'estu_discapacidad',
    'estu_estadocivil': 'estu_estado_civil',
    'estu_nacionalidad': 'estu_nacionalidad',
    'estu_fechanacimiento': 'fecha_nacimiento',
    'estu_horassemanatrabaja': 'horas_semana_trabaja',
    'estu_trabaja_actualmente': 'trabaja_actualmente',
    'estu_semestrecursa': 'semestre_cursa',
    'estu_porcentajecreditosaprob': 'pct_creditos_aprobados',
    
    # Puntajes de los módulos
    'mod_comuni_escrita_punt': 'punt_comuni_escrita',
    'mod_razona_cuantitat_punt': 'punt_razona_cuantitativa',
    'mod_ingles_punt': 'punt_ingles',
    'mod_lectura_critica_punt': 'punt_lectura_critica',
    'mod_competen_ciudada_punt': 'punt_comp_ciudadanas',
    
    # Desempeños
    'mod_comuni_escrita_desem': 'desem_comuni_escrita',
    'mod_razona_cuantitat_desem': 'desem_razona_cuantitativa',
    'mod_ingles_desem': 'desem_ingles',
    'mod_lectura_critica_desem': 'desem_lectura_critica',
    'mod_competen_ciudada_desem': 'desem_comp_ciudadanas',
    
    # NSE (Nivel Socioeconómico)
    'estu_nse_individual': 'nse_individual',
    'estu_nse_ies': 'nse_ies',
    'inst_nse': 'nse_ies',  # Posible variación
    
    # Percentiles y puntajes globales
    'percentil_global': 'percentil_global',
    'punt_global': 'puntaje_global',
    'percentil_nbc': 'percentil_nbc',
    
    # Variables familiares
    'fami_estratovivienda': 'fami_estrato_vivienda',
    'fami_ingreso_fmiliar_mensual': 'fami_ingreso_familiar_mensual',
    'fami_numpersonasacargo': 'fami_num_personas_acargo',
    'fami_personashogar': 'fami_personas_hogar',
    'fami_cuartoshogar': 'fami_cuartos_hogar',
    'fami_pisos_hogar': 'fami_pisos_hogar',
    'fami_educacionmadre': 'fami_educacion_madre',
    'fami_educacionpadre': 'fami_educacion_padre',
    'fami_ocupacionmadre': 'fami_ocupacion_madre',
    'fami_ocupacionpadre': 'fami_ocupacion_padre',
    'fami_cabezafamilia': 'fami_cabeza_familia',
    'fami_hogaractual': 'fami_hogar_actual',
    'fami_telefono': 'fami_telefono',
    'fami_tiene_celular': 'fami_tiene_celular',
    'fami_tieneinternet': 'fami_tiene_internet',
    'fami_tienecomputador': 'fami_tiene_computador',
    'fami_tieneautomovil': 'fami_tiene_automovil',
    'fami_tienelavadora': 'fami_tiene_lavadora',
    'fami_tiene_microondas': 'fami_tiene_microondas',
    'fami_tiene_nevera': 'fami_tiene_nevera',
    'fami_tienehornomicroogas': 'fami_tiene_horno_microondas',
    'fami_tienehornomicroondas': 'fami_tiene_horno_microondas',  # Posible variación
    'fami_tienemotocicleta': 'fami_tiene_motocicleta',
    'fami_tieneserviciotv': 'fami_tiene_servicio_tv',
    'fami_numlibros': 'fami_num_libros',
    'fami_tieneconsolavideojuegos': 'fami_tiene_consola',
    
    # Pagos de matrícula
    'estu_pagomatriculabeca': 'pago_matricula_beca',
    'estu_pagomatriculacredito': 'pago_matricula_credito',
    'estu_pagomatriculapadres': 'pago_matricula_padres',
    'estu_pagomatriculapropio': 'pago_matricula_propio',
    'estu_pagomatriculaext': 'pago_matricula_exterior',
    'estu_valormatriculauniversidad': 'valor_matricula_universidad',
    'estu_valormatriculauext': 'valor_matricula_exterior',
    
    # Apoyos
    'estu_apo_acompañamiento': 'estu_apo_acompanamiento',
    'estu_apo_desplazasitio': 'estu_apo_desplaza_sitio',
    'estu_apo_interpseñas': 'estu_apo_interp_senas',
    'estu_apo_interpsordociego': 'estu_apo_interp_sordo_ciego',
    'estu_apo_jefesalon': 'estu_apo_jefe_salon',
    'estu_apo_lectorapoyo': 'estu_apo_lector_apoyo',
    'estu_apo_maniobrarmat': 'estu_apo_maniobrar_material',
    'estu_apo_norequiere': 'estu_apo_no_requiere',
    
    # Otras variables
    'estu_areareside': 'area_residencia',
    'estu_zona_presentacion': 'zona_presentacion',
    'estu_inse_individual': 'inse_individual',
    'estu_agregado': 'estu_agregado',
    'inst_nombre': 'nombre_ies',  # Posible variación
}


def aplicar_mapeo_columnas(df):
    """
    Aplica el mapeo de columnas al DataFrame
    
    Args:
        df: DataFrame con los nombres de columnas originales
        
    Returns:
        DataFrame con las columnas renombradas
    """
    # Crear copia para no modificar el original
    df_mapped = df.copy()
    
    # Renombrar columnas según el mapeo
    columnas_a_renombrar = {}
    for nombre_nuevo, nombre_esperado in MAPEO_COLUMNAS.items():
        if nombre_nuevo in df_mapped.columns and nombre_nuevo != nombre_esperado:
            columnas_a_renombrar[nombre_nuevo] = nombre_esperado
    
    if columnas_a_renombrar:
        df_mapped = df_mapped.rename(columns=columnas_a_renombrar)
    
    return df_mapped