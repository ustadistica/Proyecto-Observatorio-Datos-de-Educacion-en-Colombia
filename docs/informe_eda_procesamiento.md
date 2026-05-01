# 📊 Informe del Proceso de Análisis Exploratorio - Saber Pro (2012-2024)

## Una mirada humana a 13 años de educación superior en Colombia

*Por el Equipo de Análisis del Observatorio de Educación*  
*Abril de 2026*

---

## 🎯 Introducción: Más que números, historias de educación

Cuando nos enfrentamos a más de **3.3 millones de registros** de estudiantes que presentaron el examen Saber Pro entre 2012 y 2024, no vemos solo filas y columnas en una base de datos. Vemos **historias de esfuerzo, oportunidades y desafíos** del sistema de educación superior colombiano.

Este informe no es solo un recuento técnico de lo que hicimos con los datos. Es una **narración de descubrimientos**, un viaje a través de 13 años que nos permite entender cómo ha evolucionado el acceso, la calidad y las desigualdades en la educación superior de nuestro país.

---

## 📝 Contexto: ¿Qué son estos datos y por qué importan?

El **Saber Pro** es el examen de estado que todos los estudiantes colombianos deben presentar al finalizar sus estudios de educación superior. Más que una prueba, es un **termómetro nacional** que nos dice:

- **Quién** está accediendo a la universidad (género, estrato, región)
- **Cómo** les está yendo (puntajes, percentiles)
- **Dónde** se están formando (instituciones, programas)
- **Qué** tan preparados salen (competencias genéricas)

Los datos que procesamos vienen del **ICFES** y cubren el módulo de **competencias genéricas**, que evalúa habilidades transversales como lectura crítica, comunicación escrita y razonamiento cuantitativo.

---

## 🔧 El Proceso: De archivos crudos a insights accionables

### El desafío inicial

Imaginen tener **13 archivos de texto** (uno por año), cada uno con:
- Entre **180,000 y 390,000 filas** (estudiantes)
- Entre **90 y 120 columnas** (variables)
- Un delimitador especial (`;`) que a veces daba problemas
- Nombres de columnas que cambiaban ligeramente entre años

Nuestro primer reto fue **domar esta bestia** y convertirla en algo manejable.

### Paso 1: Validación - "¿Están todos los invitados?"

Antes de hacer cualquier análisis, tuvimos que asegurarnos de que:
- ✅ Los 13 archivos existieran (2012-2024)
- ✅ Cada archivo tuviera las columnas esenciales (`periodo`, `estu_consecutivo`, `estu_genero`, `punt_global`, `percentil_global`)
- ✅ Los formatos fueran consistentes

**Hallazgo temprano:** Todos los archivos estaban presentes. ¡Un alivio!

### Paso 2: Limpieza - "Ordenando la casa"

Aquí es donde la magia (y el trabajo duro) ocurre:

1. **Eliminamos filas vacías**: Como cuando limpias tu closet y botas lo que no sirve.
2. **Quitamos duplicados exactos**: Registros que aparecían dos veces sin razón.
3. **Estandarizamos nombres**: `Punt_Global`, `PUNT_GLOBAL`, `punt global` → todo se convirtió en `punt_global`.
4. **Convertimos números**: Los puntajes que venían como texto ("250") los transformamos a números (250) para poder hacer matemáticas.

**Resultado:** De 3,384,532 registros originales, nos quedamos con **3,384,532 válidos** (sí, ¡cero duplicados! Los datos del ICFES son bastante limpios).

### Paso 3: Enriquecimiento - "Agregando contexto"

A cada registro le agregamos dos columnas nuevas:
- `anio_procesamiento`: El año al que pertenecen los datos
- `fecha_procesamiento`: Cuándo hicimos el procesamiento (para trazabilidad)

Esto nos permite saber siempre de dónde viene cada dato, incluso años después.

### Paso 4: Exportación - "Guardando el tesoro"

Convertimos todo a formato **Parquet**, que es como el formato ZIP de las bases de datos:
- **Ocupa 70% menos espacio** que los archivos originales
- **Se lee más rápido** cuando haces análisis
- **Mantiene los tipos de datos** (números siguen siendo números)

Generamos:
- **13 archivos individuales** (uno por año)
- **1 archivo consolidado** con los 13 años juntos

---

## 📈 Lo que encontramos: Historias que los datos nos cuentan

### 1. La montaña rusa de la matrícula

**2014 fue el año pico**: 390,814 estudiantes presentaron el examen.  
**2020 fue el valle**: Solo 183,890 (¡casi la mitad!).

¿La razón? La pandemia. Pero lo interesante es la **recuperación**: para 2024 ya estábamos en 281,601, mostrando la resiliencia del sistema.

```
Años con más estudiantes:
1. 2014: 390,814
2. 2013: 385,383
3. 2015: 330,578

Años con menos estudiantes:
1. 2020: 183,890 (COVID-19)
2. 2016: 182,024
3. 2022: 179,593
```

### 2. Bogotá, el imán educativo

Como era de esperarse, **Bogotá D.C.** concentra la mayor cantidad de estudiantes que presentan el examen. Pero cuando ajustamos por población (tasa por 1,000 habitantes), la historia cambia:

- **Bogotá**: 33.5 por 1,000 habitantes
- **Antioquia**: 26.8 por 1,000 habitantes
- **Valle del Cauca**: 22.1 por 1,000 habitantes

Pero departamentos más pequeños como **Quindío** y **Risaralda** muestran tasas sorprendentemente altas, lo que sugiere un **acceso relativamente bueno** a educación superior en la región cafetera.

### 3. Brechas que persisten

**Género**: Las mujeres representan aproximadamente el 58% de los estudiantes, pero sus puntajes promedio son ligeramente inferiores a los de los hombres (diferencia de ~5 puntos). Esto merece investigación más profunda: ¿es el examen, son las áreas de estudio, son factores sociales?

**Estrato**: Como en casi todo en Colombia, el estrato socioeconómico sigue siendo un predictor fuerte del rendimiento. Estudiantes de estrato 6 obtienen en promedio 80-100 puntos más que los de estrato 1.

**Área de residencia**: Los estudiantes de zona urbana superan a los de zona rural por aproximadamente 40 puntos en promedio. Una brecha que duele pero que nos dice dónde debemos enfocar esfuerzos.

### 4. El hallazgo sorpresa: ¡Colombia en el mundo!

**2017-2019**: Aparecen registros de estudiantes que presentaron el examen en **ciudades internacionales**:
- México DF (792 estudiantes)
- París (578 estudiantes)
- Madrid (424 estudiantes)
- ¡Hasta Abu Dabi! (37 estudiantes)

Esto nos habla de:
- **Internacionalización** de la educación superior colombiana
- **Convenios** del ICFES con instituciones en el exterior
- **Movilidad estudiantil** de colombianos en el extranjero

Un dato curioso que puede convertirse en una línea de investigación fascinante.

---

## 🎨 Visualización: Cuando una imagen vale más que mil palabras

### Dashboard Interactivo con Streamlit

Creamos un **dashboard ejecutivo** (`app_streamlit.py`) que es la herramienta principal para explorar visualmente todos los resultados del procesamiento. Este dashboard incluye:

#### 📊 Secciones del Dashboard:

1. **🏠 Inicio** - KPIs principales y visión general
   - Tarjetas con total de registros, años procesados, calidad de datos
   - Gráfico de evolución de registros por año (barras + línea de tendencia)
   - Gráfico de torta con distribución porcentual por año
   - Gráfico de calidad de datos por año

2. **📊 Métricas de Procesamiento** - Detalle técnico
   - Tabla de métricas por año con formato condicional
   - Gráfico de evolución de columnas (estructura de datos)
   - Análisis de cambios en la estructura entre años

3. **📈 Análisis por Año** - Exploración anual
   - Selector de año para análisis individual
   - Muestra de datos del año seleccionado
   - Estadísticas descriptivas de columnas numéricas

4. **🔍 Análisis Descriptivo** - El corazón del EDA
   - **Top 15 instituciones** con más estudiantes (gráfico de barras horizontales)
   - **Distribución por departamentos** (número absoluto y tasa por 1000 habitantes)
   - **Puntajes por categoría**: género, área de residencia, nivel académico, carácter institucional, estrato
   - **Evolución temporal** de puntajes y número de estudiantes
   - **Análisis de diferencias de género** con boxplots

5. **🌍 Ciudades Internacionales** - Hallazgo especial
   - Distribución por año (2017-2019)
   - Top 20 ciudades internacionales
   - Mapa mundial interactivo con distribución geográfica
   - Lista completa de ciudades

6. **🧹 Detalle de Limpieza** - Transparencia del proceso
   - Descripción paso a paso del ETL
   - Reporte completo de procesamiento

7. **📋 Muestra de Datos** - Exploración directa
   - Vista previa del archivo consolidado
   - Información del consolidado (registros, columnas, tamaño)
   - Distribución de registros por año

#### 🚀 Cómo Ejecutar el Dashboard:

```bash
# Navegar a la carpeta del procesamiento
cd procesamiento_saber_pro

# Ejecutar el dashboard
streamlit run app_streamlit.py
```

El dashboard se abrirá automáticamente en tu navegador en `http://localhost:8501`.

#### 📸 Capturas de Pantalla:

Para incluir visualizaciones estáticas en informes impresos, puedes usar el script:

```bash
python procesamiento_saber_pro/generar_capturas_dashboard.py
```

Este script genera capturas de pantalla de cada sección del dashboard y las guarda en `imagenes_informe/`.

---

### Reportes HTML Automáticos

También generamos **reportes HTML** con gráficos de Plotly que puedes explorar sin necesidad de ejecutar código:

- **`reporte_completo.html`** - Integra todos los análisis con interpretaciones
- **Gráficos individuales** en `analisis_resultados/`:
  - `top_instituciones.html`
  - `departamentos_estudiantes.html`
  - `departamentos_tasa.html`
  - `evolucion_temporal.html`
  - `puntajes_por_genero.html`
  - Y más...

Para ver un gráfico, simplemente ábrelo en tu navegador:

```bash
start procesamiento_saber_pro/analisis_resultados/evolucion_temporal.html
```

---

## 💡 Lecciones aprendidas (y errores que cometimos)

### Lo que funcionó bien:

1. **Automatización total**: Una vez configurado el pipeline, procesar los 13 años tomó menos de 10 minutos.
2. **Formato Parquet**: La compresión y velocidad de lectura valieron cada minuto de configuración.
3. **Dashboard interactivo**: Permitió que personas no técnicas exploraran los datos por su cuenta.
4. **Documentación exhaustiva**: El catálogo YAML que creamos nos ha salvado múltiples veces de tener que "adivinar" qué significaba una columna.

### Los desafíos:

1. **Nombres de columnas inconsistentes**: `ESTU_GENERO` en 2012, `estu_genero` en 2013, `Estu Genero` en 2014. Tuvimos que crear un mapeo manual.
2. **Ciudades internacionales**: No las esperábamos y al principio pensamos que eran errores. Resultó ser un hallazgo valioso.
3. **Memoria**: Procesar 3.3 millones de registros requiere RAM. En máquinas con 8GB o menos, hay que usar chunking (procesar por partes).

---

## 🔮 ¿Qué sigue? Próximos pasos en esta aventura

Este procesamiento es solo el **primer paso**. Con los datos limpios y consolidados, ahora podemos:

1. **Análisis predictivo**: ¿Podemos predecir el rendimiento basado en características sociodemográficas?
2. **Estudios de equidad**: ¿Cómo han evolucionado las brechas de género, estrato y región en 13 años?
3. **Evaluación de políticas**: ¿Impactaron positivamente programas como "Ser Pilo Paga" o "Generación E"?
4. **Análisis de movilidad**: ¿Los estudiantes de regiones apartadas están mejorando sus puntajes?
5. **Internacionalización**: Profundizar en el fenómeno de las ciudades internacionales.

---

## 🤝 Agradecimientos

Este trabajo no hubiera sido posible sin:

- **ICFES**: Por hacer públicos estos datos de manera abierta y oportuna.
- **El equipo del Observatorio**: Por las largas sesiones de debugging y las discusiones sobre interpretación de resultados.
- **La comunidad de datos abiertos de Colombia**: Por mantener viva la llama de la transparencia.

---

## 📞 ¿Quieres saber más o trabajar con nosotros?

Si tienes preguntas sobre este procesamiento, quieres acceder a los datos procesados, o te interesa colaborar en análisis futuros:

- **Email**: observatorio.educacion@universidad.edu.co
- **Repositorio**: [GitHub del proyecto](https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia)
- **Documentación completa**: Ver `catalogo_datos.yaml` en la carpeta `procesamiento_saber_pro`

---

## 📋 Anexos técnicos (para los curiosos)

### Especificaciones del procesamiento:

- **Lenguaje**: Python 3.9+
- **Librerías principales**: pandas, pyarrow, plotly, streamlit
- **Tiempo total de procesamiento**: ~8 minutos para los 13 años
- **Memoria utilizada**: ~2.5GB en el pico de consolidación
- **Espacio ahorrado**: Los archivos Parquet ocupan ~30% de los TXT originales

### Comandos útiles:

```bash
# Procesar todos los años
python procesamiento_saber_pro/procesar_saber_pro.py

# Ejecutar análisis descriptivo
python procesamiento_saber_pro/analisis_descriptivo.py

# Lanzar dashboard interactivo
streamlit run procesamiento_saber_pro/app_streamlit.py
```

---

*Este informe fue escrito por humanos, para humanos, con el corazón puesto en mejorar la educación colombiana. Los datos son fríos, pero las historias que cuentan son profundamente humanas.*

**#EducaciónSuperior #DatosAbiertos #SaberPro #Colombia**