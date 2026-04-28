# 📋 Resumen Ejecutivo - Procesamiento y Catálogo de Datos Saber Pro (2012-2024)

## 🎯 ¿Qué hicimos?

Hemos completado el **procesamiento integral** de las bases de datos del examen Saber Pro (competencias genéricas) de los años 2012 a 2024, y hemos creado un **catálogo de datos profesional** junto con un **informe de análisis exploratorio (EDA) humanizado** y **visualizaciones interactivas**.

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
- 📈 **Hallazgos clave** presentados como historias
- 💡 **Lecciones aprendidas** y próximos pasos
- 🤝 **Agradecimientos** y contacto

**📁 Ubicación:** `procesamiento_saber_pro/informe_eda_procesamiento.md`

### 3. Dashboard Interactivo y Gráficas (`analisis_resultados/`)
**11 visualizaciones interactivas generadas automáticamente:**

#### 📊 Gráficas de Distribución y Tendencias
1. **`top_instituciones.html`** - Top 20 instituciones con mayor número de estudiantes
2. **`departamentos_estudiantes.html`** - Distribución de estudiantes por departamento (número absoluto)
3. **`departamentos_tasa.html`** - Tasa de presentación por 1000 habitantes por departamento
4. **`evolucion_temporal.html`** - Evolución de puntajes y número de estudiantes a través de los años (2012-2024)

#### 📊 Gráficas de Puntajes por Categorías
5. **`puntajes_por_genero.html`** - Distribución de puntajes según género del estudiante
6. **`puntajes_por_estu_genero.html`** - Versión alternativa del análisis de género
7. **`puntajes_por_estu_nivel_prgm_academico.html`** - Puntajes promedio por nivel académico del programa
8. **`puntajes_por_inst_caracter_academico.html`** - Puntajes promedio según carácter de la institución (pública/privada)
9. **`puntajes_por_estu_areareside.html`** - Puntajes promedio por área de residencia (urbana/rural)
10. **`puntajes_por_fami_estratovivienda.html`** - Puntajes promedio por estrato socioeconómico

#### 📊 Reporte Consolidado
11. **`reporte_completo.html`** - Reporte HTML interactivo que integra todos los análisis con gráficos de Plotly y interpretaciones automáticas

**📁 Ubicación:** `procesamiento_saber_pro/analisis_resultados/`

---

## 🔧 Proceso Realizado

### Pipeline ETL Automatizado
1. **Validación** - Verificación de existencia y estructura
2. **Carga** - Lectura de 13 archivos TXT con delimitador `;`
3. **Limpieza** - Eliminación de vacíos/duplicados, estandarización
4. **Enriquecimiento** - Agregación de metadatos (año, fecha procesamiento)
5. **Exportación** - Conversión a Parquet (70% menos espacio)
6. **Consolidación** - Unión de todos los años en un solo archivo
7. **Análisis** - Generación de 11 gráficas interactivas y dashboard

### Scripts Desarrollados
- `procesar_saber_pro.py` - Procesamiento ETL principal
- `analisis_descriptivo.py` - Análisis exploratorio automático y generación de gráficas
- `app_streamlit.py` - Dashboard ejecutivo interactivo
- `analizar_departamentos.py` - Script especializado en análisis geográfico

---

## 📈 Métricas del Procesamiento

| Concepto | Valor |
|----------|-------|
| **Total de registros procesados** | 3,384,532 |
| **Años cubiertos** | 13 (2012-2024) |
| **Archivos Parquet generados** | 14 (13 individuales + 1 consolidado) |
| **Gráficas interactivas creadas** | 11 |
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

## 🌟 Hallazgos Destacados (con Gráficas)

### 1. 📊 Top Instituciones que más Presentan el Examen
**Gráfica:** `top_instituciones.html`

Las universidades con mayor número de estudiantes que presentan el Saber Pro son principalmente instituciones públicas y de gran cobertura. La Universidad Nacional de Colombia lidera consistentemente, seguida por universidades regionales importantes.

**¿Qué muestra la gráfica?**
- Barras horizontales con las 20 instituciones con más estudiantes
- Colores que indican la cantidad (escala de azules)
- Permite identificar rápidamente las universidades con mayor población estudiantil

---

### 2. 🗺️ Distribución Geográfica por Departamentos

#### 2.1 Número Absoluto de Estudiantes
**Gráfica:** `departamentos_estudiantes.html`

Bogotá D.C. concentra el mayor número absoluto de estudiantes, lo cual es esperado por su población. Le siguen Antioquia y Valle del Cauca, reflejando la concentración poblacional y de instituciones de educación superior en estas regiones.

**¿Qué muestra la gráfica?**
- Barras verticales con los 15 departamentos con más estudiantes
- Colores que indican la cantidad (escala de azules)
- Eje Y con número de estudiantes, eje X con departamentos

#### 2.2 Tasa por 1000 Habitantes (Ajustado por Población)
**Gráfica:** `departamentos_tasa.html`

Cuando ajustamos por población, la historia cambia: departamentos más pequeños como Quindío y Risaralda muestran tasas sorprendentemente altas, lo que sugiere un acceso relativamente bueno a educación superior en la región cafetera.

**¿Qué muestra la gráfica?**
- Barras verticales con los 15 departamentos con mayor tasa por 1000 habitantes
- Colores que indican la tasa (escala de naranjas)
- Permite comparar acceso relativo, no solo números absolutos

---

### 3. 📈 Evolución Temporal (2012-2024)
**Gráfica:** `evolucion_temporal.html`

La evolución temporal muestra dos historias paralelas:
- **Línea superior:** Puntaje promedio y mediana a través de los años
- **Barras inferiores:** Número de estudiantes por año

**¿Qué muestra la gráfica?**
- **Panel 1:** Líneas de tendencia con puntaje promedio (azul) y mediana (naranja punteada)
- **Panel 2:** Barras con el número de estudiantes por año
- Permite ver el impacto de la pandemia en 2020 (caída del 53%)
- Muestra la recuperación gradual 2021-2024

**Hallazgo clave:** 2014 fue el año pico (390,814 estudiantes), 2020 el valle (183,890), y 2024 muestra recuperación (281,601).

---

### 4. ⚖️ Brechas de Género en Puntajes
**Gráficas:** `puntajes_por_genero.html` y `puntajes_por_estu_genero.html`

Las mujeres representan aproximadamente el 58% de los estudiantes, pero sus puntajes promedio son ligeramente inferiores a los de los hombres (diferencia de ~5 puntos).

**¿Qué muestran las gráficas?**
- **Gráfico de cajas (boxplot):** Muestra la distribución completa de puntajes por género
  - Caja que indica el 50% central de los datos
  - Línea media que muestra la mediana
  - Bigotes que indican el rango intercuartílico
  - Puntos atípicos (outliers) si los hay
- Permite comparar no solo promedios, sino toda la distribución
- Muestra si hay diferencias en la dispersión de puntajes

**Preguntas que surgen:**
- ¿Es el examen el que tiene sesgo?
- ¿Son las áreas de estudio las que explican la diferencia?
- ¿Son factores sociales y económicos?

---

### 5. 🎓 Puntajes por Nivel Académico del Programa
**Gráfica:** `puntajes_por_estu_nivel_prgm_academico.html`

Los estudiantes de posgrado (maestría y doctorado) obtienen puntajes significativamente superiores a los de pregrado, lo cual es esperado dado su mayor nivel de formación.

**¿Qué muestra la gráfica?**
- Barras verticales con el puntaje promedio por nivel académico
- Categorías: Técnico Profesional, Tecnológico, Profesional Universitario, Maestría, Doctorado
- Colores que indican el puntaje (escala divergente rojo-azul)
- Permite ver la jerarquía esperada en el sistema educativo

---

### 6. 🏛️ Puntajes por Carácter de la Institución
**Gráfica:** `puntajes_por_inst_caracter_academico.html`

Comparación entre instituciones públicas y privadas. Las diferencias observadas pueden reflejar diversos factores como selectividad, recursos, perfil de estudiantes, etc.

**¿Qué muestra la gráfica?**
- Barras verticales con el puntaje promedio por carácter (Pública vs Privada)
- Colores que indican el puntaje (escala divergente)
- Permite identificar brechas institucionales

---

### 7. 🏙️ Puntajes por Área de Residencia
**Gráfica:** `puntajes_por_estu_areareside.html`

Los estudiantes de zona urbana superan a los de zona rural por aproximadamente 40 puntos en promedio. Una brecha que duele pero que nos dice dónde debemos enfocar esfuerzos.

**¿Qué muestra la gráfica?**
- Barras verticales con el puntaje promedio por área (Urbana, Rural, Otra)
- Colores que indican el puntaje (escala divergente)
- Evidencia clara de la brecha urbano-rural en educación superior

---

### 8. 💰 Puntajes por Estrato Socioeconómico
**Gráfica:** `puntajes_por_fami_estratovivienda.html`

Como en casi todo en Colombia, el estrato socioeconómico sigue siendo un predictor fuerte del rendimiento. Estudiantes de estrato 6 obtienen en promedio 80-100 puntos más que los de estrato 1.

**¿Qué muestra la gráfica?**
- Barras verticales con el puntaje promedio por estrato (1 a 6)
- Colores que indican el puntaje (escala divergente)
- Muestra una tendencia clara: a mayor estrato, mayor puntaje
- Evidencia de la desigualdad estructural en el sistema educativo

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
├── reporte_completo.html          ← Reporte integrado con todas las gráficas
├── top_instituciones.html         ← Top 20 instituciones
├── departamentos_estudiantes.html ← Distribución por departamentos (absoluto)
├── departamentos_tasa.html        ← Tasa por 1000 habitantes
├── evolucion_temporal.html        ← Evolución 2012-2024
├── puntajes_por_genero.html       ← Distribución por género (boxplot)
├── puntajes_por_estu_genero.html  ← Análisis de género (alternativo)
├── puntajes_por_estu_nivel_prgm_academico.html ← Por nivel académico
├── puntajes_por_inst_caracter_academico.html   ← Pública vs Privada
├── puntajes_por_estu_areareside.html           ← Urbana vs Rural
└── puntajes_por_fami_estratovivienda.html      ← Por estrato socioeconómico
```

---

## 🎨 Cómo Explorar las Gráficas

### Opción 1: Abrir Gráficas Individualmente
Cada archivo HTML en `analisis_resultados/` es completamente interactivo:
- **Haz hover** sobre las barras/líneas para ver detalles
- **Pasa el mouse** para ver valores exactos
- **Usa las herramientas** de Plotly para zoom, pan, download
- **Abre en tu navegador** favorito (Chrome, Firefox, Edge)

**Ejemplo:** Para ver la evolución temporal:
```bash
# En Windows
start procesamiento_saber_pro/analisis_resultados/evolucion_temporal.html

# En Mac/Linux
open procesamiento_saber_pro/analisis_resultados/evolucion_temporal.html
# o
xdg-open procesamiento_saber_pro/analisis_resultados/evolucion_temporal.html
```

### Opción 2: Ver Reporte Completo Integrado
El archivo `reporte_completo.html` integra todas las gráficas en un solo documento con:
- KPIs principales (total registros, años analizados, instituciones)
- Interpretaciones automáticas de cada hallazgo
- Navegación entre secciones
- Diseño responsivo y profesional

**Para abrirlo:**
```bash
start procesamiento_saber_pro/analisis_resultados/reporte_completo.html
```

### Opción 3: Dashboard Interactivo con Streamlit
El dashboard (`app_streamlit.py`) permite:
- Navegar por secciones con menú lateral
- Filtrar por años específicos
- Ver métricas de procesamiento en tiempo real
- Explorar datos con gráficos interactivos
- Descargar subconjuntos de datos

**Para ejecutarlo:**
```bash
streamlit run procesamiento_saber_pro/app_streamlit.py
```

---

## 🚀 Cómo Usar Este Trabajo

### Para Analistas de Datos
1. **Consulta el catálogo** (`catalogo.yaml`) para entender la estructura
2. **Usa el consolidado** para análisis longitudinales (2012-2024)
3. **Usa archivos individuales** para análisis transversales (un año específico)
4. **Explora las gráficas** en `analisis_resultados/` para insights visuales
5. **Ejecuta los scripts** para reproducir o extender el análisis

### Para Tomadores de Decisión
1. **Lee el informe EDA** (`informe_eda_procesamiento.md`) para una narrativa accesible
2. **Abre el reporte completo** (`reporte_completo.html`) para ver todas las gráficas con interpretaciones
3. **Explora el dashboard** (`app_streamlit.py`) para visualizaciones interactivas
4. **Revisa los hallazgos** en el catálogo para insights clave

### Para Investigadores
1. **Revisa las limitaciones** documentadas en el catálogo
2. **Considera el contexto histórico** de cada periodo
3. **Valida con múltiples enfoques** metodológicos
4. **Usa las gráficas** como punto de partida para análisis más profundos

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
5. **Visualizaciones profesionales** - 11 gráficas interactivas listas para usar
6. **Escalabilidad** - Pipeline que puede extenderse a años futuros

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

---

## 📎 Anexos: Lista Completa de Visualizaciones

| # | Nombre del Archivo | Tipo de Gráfica | Qué Muestra |
|---|-------------------|-----------------|-------------|
| 1 | `top_instituciones.html` | Barras horizontales | Top 20 instituciones con más estudiantes |
| 2 | `departamentos_estudiantes.html` | Barras verticales | Distribución por departamentos (número absoluto) |
| 3 | `departamentos_tasa.html` | Barras verticales | Tasa por 1000 habitantes por departamento |
| 4 | `evolucion_temporal.html` | Líneas + Barras | Evolución de puntajes y estudiantes (2012-2024) |
| 5 | `puntajes_por_genero.html` | Boxplot | Distribución de puntajes por género |
| 6 | `puntajes_por_estu_genero.html` | Barras | Puntaje promedio por género |
| 7 | `puntajes_por_estu_nivel_prgm_academico.html` | Barras | Puntaje promedio por nivel académico |
| 8 | `puntajes_por_inst_caracter_academico.html` | Barras | Puntaje promedio pública vs privada |
| 9 | `puntajes_por_estu_areareside.html` | Barras | Puntaje promedio urbana vs rural |
| 10 | `puntajes_por_fami_estratovivienda.html` | Barras | Puntaje promedio por estrato (1-6) |
| 11 | `reporte_completo.html` | Dashboard integrado | Todas las gráficas con interpretaciones |

**Todas las gráficas son interactivas y están disponibles en:** `procesamiento_saber_pro/analisis_resultados/`