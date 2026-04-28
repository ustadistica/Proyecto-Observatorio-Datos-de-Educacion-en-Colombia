# 📋 Resumen Ejecutivo - Procesamiento y Catálogo de Datos Saber Pro (2012-2024)

## 🎯 ¿Qué hicimos?

Hemos completado el **procesamiento integral** de las bases de datos del examen Saber Pro (competencias genéricas) de los años 2012 a 2024, y hemos creado un **catálogo de datos profesional** junto con un **informe de análisis exploratorio (EDA) humanizado**.

---

## 📊 Entregables Principales

### 1. Catálogo de Datos (`catalogo.yaml`)
**Versión 2.0 - Consolidada y Mejorada**

Un documento YAML exhaustivo que incluye:
- ✅ **Metadatos completos** de las bases de datos
- ✅ **Descripción detallada del proceso ETL** (7 pasos)
- ✅ **Métricas de procesamiento** por año (3.3+ millones de registros totales)
- ✅ **Esquema completo de variables** (identificación, demográficas, académicas, puntajes)
- ✅ **Lista de archivos generados** (13 individuales + 1 consolidado)
- ✅ **Hallazgos importantes** (ciudades internacionales, variación estructural, pandemia)
- ✅ **Control de calidad** con métricas y resultados
- ✅ **Recomendaciones de uso** para diferentes tipos de análisis
- ✅ **Notas técnicas** y comandos útiles

**📁 Ubicación:** `procesamiento_saber_pro/catalogo.yaml`

### 2. Informe EDA Humanizado (`informe_eda_procesamiento.md`)
**"Una mirada humana a 13 años de educación superior en Colombia"**

Un informe narrativo que cuenta la historia detrás de los datos:
- 📖 **Introducción contextual** que explica la importancia del Saber Pro
- 🔧 **Descripción del proceso** de manera accesible (no técnica)
- 📈 **Hallazgos clave** presentados como historias:
  - La montaña rusa de la matrícula (pico 2014, valle 2020 por COVID)
  - Bogotá como imán educativo (y el ajuste por población)
  - Brechas que persisten (género, estrato, área de residencia)
  - El hallazgo sorpresa: ¡Colombia en el mundo! (ciudades internacionales 2017-2019)
- 💡 **Lecciones aprendidas** (qué funcionó, qué desafíos enfrentamos)
- 🔮 **Próximos pasos** sugeridos para investigación futura
- 🤝 **Agradecimientos** y contacto

**📁 Ubicación:** `procesamiento_saber_pro/informe_eda_procesamiento.md`

---

## 🔧 Proceso Realizado

### Pipeline ETL Automatizado
1. **Validación** - Verificación de existencia y estructura
2. **Carga** - Lectura de 13 archivos TXT con delimitador `;`
3. **Limpieza** - Eliminación de vacíos/duplicados, estandarización
4. **Enriquecimiento** - Agregación de metadatos (año, fecha procesamiento)
5. **Exportación** - Conversión a Parquet (70% menos espacio)
6. **Consolidación** - Unión de todos los años en un solo archivo
7. **Análisis** - Generación de gráficos interactivos y dashboard

### Scripts Desarrollados
- `procesar_saber_pro.py` - Procesamiento ETL principal
- `analisis_descriptivo.py` - Análisis exploratorio automático
- `app_streamlit.py` - Dashboard ejecutivo interactivo
- `analizar_departamentos.py` - Script especializado en análisis geográfico

---

## 📈 Métricas del Procesamiento

| Concepto | Valor |
|----------|-------|
| **Total de registros procesados** | 3,384,532 |
| **Años cubiertos** | 13 (2012-2024) |
| **Archivos Parquet generados** | 14 (13 individuales + 1 consolidado) |
| **Registros válidos** | 99.9% |
| **Duplicados eliminados** | 0 (datos muy limpios) |
| **Tiempo de procesamiento** | ~8 minutos |
| **Memoria requerida** | ~2.5GB (pico de consolidación) |
| **Espacio ahorrado** | ~70% vs archivos originales |

### Distribución por Año
- **Año pico:** 2014 (390,814 estudiantes)
- **Año más bajo:** 2020 (183,890 estudiantes - impacto COVID-19)
- **Promedio anual:** ~260,000 estudiantes

---

## 🌟 Hallazgos Destacados

### 1. Internacionalización del Examen (2017-2019)
- **5,847 estudiantes** presentaron el examen en ciudades internacionales
- Principales destinos: México DF (792), París (578), Madrid (424)
- ¡Hasta Abu Dabi! (37 estudiantes)
- **Interpretación:** Evidencia de convenios internacionales y movilidad estudiantil

### 2. Brechas Persistentes
- **Género:** Mujeres son 58% de estudiantes pero con puntajes ~5 puntos inferiores
- **Estrato:** Diferencia de 80-100 puntos entre estrato 1 y 6
- **Área:** Zona urbana supera a rural por ~40 puntos en promedio

### 3. Resiliencia del Sistema
- Caída del 53% en 2020 por pandemia
- Recuperación gradual 2021-2024 (281,601 estudiantes en 2024)

---

## 💾 Archivos Generados

### Datos Procesados
```
procesamiento_saber_pro/datos_procesados/
├── saber_pro_2012.parquet
├── saber_pro_2013.parquet
├── ... (uno por año hasta 2024)
├── saber_pro_consolidado_20260421.parquet
└── reporte_procesamiento.txt
```

### Análisis y Visualizaciones
```
procesamiento_saber_pro/analisis_resultados/
├── reporte_completo.html
├── top_instituciones.html
├── departamentos_estudiantes.html
├── departamentos_tasa.html
├── evolucion_temporal.html
├── puntajes_por_genero.html
└── ... (más gráficos interactivos)
```

---

## 🚀 Cómo Usar Este Trabajo

### Para Analistas de Datos
1. **Consulta el catálogo** (`catalogo.yaml`) para entender la estructura
2. **Usa el consolidado** para análisis longitudinales (2012-2024)
3. **Usa archivos individuales** para análisis transversales (un año específico)
4. **Ejecuta los scripts** para reproducir o extender el análisis

### Para Tomadores de Decisión
1. **Lee el informe EDA** (`informe_eda_procesamiento.md`) para una narrativa accesible
2. **Explora el dashboard** (`app_streamlit.py`) para visualizaciones interactivas
3. **Revisa los hallazgos** en el catálogo para insights clave

### Para Investigadores
1. **Revisa las limitaciones** documentadas en el catálogo
2. **Considera el contexto histórico** de cada periodo
3. **Valida con múltiples enfoques** metodológicos

---

## 📞 Contacto y Soporte

- **Equipo:** Observatorio de Educación - Universidad Santo Tomás
- **Email:** observatorio.educacion@usantotomas.edu.co
- **Repositorio:** [GitHub del proyecto](https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia)
- **Documentación completa:** Ver `catalogo.yaml` y `README.md`

---

## 🎓 Valor Agregado

Este trabajo proporciona:

1. **Datos listos para analizar** - Procesados, limpios y documentados
2. **Transparencia total** - Cada paso del proceso está documentado
3. **Reproducibilidad** - Scripts automatizados y comandos claros
4. **Accesibilidad** - Información técnica y narrativa humanizada
5. **Escalabilidad** - Pipeline que puede extenderse a años futuros

---

## 🙏 Agradecimientos

- **ICFES** por hacer públicos estos datos
- **Universidad Santo Tomás** por el apoyo institucional
- **Comunidad de datos abiertos de Colombia** por inspirar este trabajo

---

*Este resumen fue elaborado con el compromiso de hacer de la educación superior colombiana un sistema más transparente, equitativo y basado en evidencia.*

**#EducaciónSuperior #DatosAbiertos #SaberPro #ICFES #Colombia**

---

**📅 Fecha de elaboración:** Abril 2026  
**👥 Equipo responsable:** Yeimy Alarcón, Carlos Diaz, Vanessa Cortes  
**🏫 Institución:** Universidad Santo Tomás - Facultad de Estadística  
**📚 Curso:** Consultoría e Investigación