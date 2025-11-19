<div align="center">

# Proyecto Observatorio de datos de Educacion en Colombia 🎓📊📝 

Proyecto del curso <b>Consultoría e Investigación</b> – Facultad de Estadística  
<b>Informe Final</b> · <b>Universidad Santo Tomás</b> · <b>Octavo Semestre (2025-2)</b>
<br/>

<b>Equipo:</b> Yeimy Alarcón · Carlos Diaz · Vanessa Cortes 

</div>

> **Estado:** En progreso · **Repositorio:** _[Link Repositorio](https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia.git)_ · **Última actualización:** 2025-11-17

---
## Introducción

El sistema educativo colombiano genera una gran cantidad de información cada año. Sin embargo, estos datos no solo están dispersos en varios portales, sino que también vienen en formatos muy diferentes que hacen difícil analizarlos y, en muchos casos, incluso acceder a ellos de manera sencilla. Frente a este problema, este proyecto nace con la idea de organizar esa información de una forma más clara y ordenada, para que sea más fácil trabajar con ella y para que se pueda actualizar sin complicaciones cuando aparezcan nuevos datos.

El trabajo se concentra en tres fuentes oficiales que permiten ver la educación desde diferentes ángulos. El SNIES muestra cómo se comportan los estudiantes, las instituciones y los programas. El PTE permite seguir el movimiento del presupuesto destinado al sector educación mes a mes. El ICFES, a través de Saber Pro, ofrece información detallada sobre los estudiantes que presentan el examen de competencias genéricas. Aunque estas fuentes tienen datos de muchos otros años, nosotros elegimos trabajar con el periodo 2021 a 2024, porque son los años más recientes, completos y manejables para el análisis que se quería realizar.

En este informe explicamos cómo se organizaron estas bases, cómo se construyó un modelo que facilita su manejo y cuáles fueron los principales resultados obtenidos al explorar los datos de Saber Pro, que fue la base más sólida y completa para este análisis.

---
## Justificación y antecedentes

Los portales públicos del sector educación son valiosos, pero trabajar directamente con ellos puede ser difícil. Cada fuente tiene su propio formato, sus propios niveles de información y diferentes formas de nombrar variables y categorías. Esto complica los análisis y hace que aunque los datos existan, analizarlos pueda tomar mucho tiempo y esfuerzo.

Este proyecto busca solucionar ese problema creando un observatorio que permita tener toda la información organizada desde el principio. La idea es contar con un sistema donde los datos ya estén limpios, estandarizados y listos para usarse, y que además se pueda actualizar sin dificultad cuando salgan nuevos años.

Las tres fuentes que usamos son confiables y se publican con una frecuencia estable. El SNIES y Saber Pro se actualizan cada año, mientras que el presupuesto del sector educación se publica cada mes. Gracias a esto, podemos construir un sistema que se mantiene al día de forma sencilla, ya que solo requiere agregar la información nueva sin tener que repetir todo el proceso desde cero.

Además, Saber Pro es una de las bases más completas que existen en Colombia sobre educación superior. Tiene información de más de un millón de estudiantes, con puntajes en cinco competencias y datos sobre su contexto familiar, institucional y académico. Esto la convierte en la mejor base que permite entender mejor cómo son los estudiantes, cómo les va en las pruebas y qué factores pueden estar relacionados con sus resultados.

---
## Objetivos

### Objetivo general

Crear un observatorio de datos que permita reunir, organizar y preparar la información del sistema educativo colombiano entre 2021 y 2024 de una manera clara y ordenada. La idea es construir una base sólida y fácil de entender, que ayude a analizar estos datos sin dificultad y que pueda seguir creciendo con el paso del tiempo sin necesidad de empezar desde cero cada vez que alguien quiera agregar un año nuevo.

#### Objetivos específicos

• Reunir los datos del SNIES, del PTE y de Saber Pro y crear un sistema que facilite su acceso y manejo. Esto incluye descargar los archivos de forma automática, organizarlos con nombres claros, documentar cada uno y dejarlos listos para trabajar, sin tener que buscarlos uno por uno ni repetir el proceso para cada año. 

• Construir un modelo estrella que integre toda la información de Saber Pro y que permita manejar más de un millón de registros de forma eficiente. Este modelo debe facilitar la exploración de los datos para entender quiénes presentan el examen, cómo les va en cada módulo y qué características pueden estar relacionadas con sus resultados.

• Dejar un sistema preparado para incorporar nuevos años sin rehacer todo el proceso inicial, de modo que el observatorio pueda mantenerse actualizado de manera sencilla. También asegurar que su estructura sea lo suficientemente clara para que otros puedan usarlo, ampliarlo o adaptarlo en análisis futuros.

---
## Metodología

El proyecto se desarrolló en varias etapas. Primero se exploraron los portales del SNIES, del PTE y del ICFES para conocer su estructura, frecuencia de actualización, la calidad de los datos y su vía de acceso. Luego se descargaron las bases oficiales de los años 2021 a 2024.

En el caso del SNIES, se desarrolló un programa que recorre la página del Ministerio de Educación y descarga todas las bases consolidadas. El programa también renombra los archivos de manera clara y deja registrada la ruta original y la ruta final. Esto evita tener que identificar manualmente cada archivo y garantiza orden desde el principio.

Para el PTE se descargaron los archivos mensuales de presupuesto y se creó un programa que selecciona solo el sector educación y une todos los meses en una única tabla. Así se obtiene la información de apropiación, compromisos, obligaciones y pagos sin necesidad de revisar archivo por archivo.

El trabajo más profundo se realizó con Saber Pro. Esta base tiene más de un millón de estudiantes entre 2021 y 2024 y contiene noventa variables. Para manejar esta cantidad de información se creó un modelo estrella que se observa a continuación:

<p align="center">
  <img width="1252" height="454" alt="Figura . Modelo Estrella" src="https://github.com/user-attachments/assets/6a1885f5-c095-4d6d-99ec-1a025f714530" />
  <br>
  <strong>Figura 1.</strong> Modelo Estrella
</p>

En el centro del modelo está la tabla donde guardamos los puntajes de cada estudiante. A su alrededor están las dimensiones, que son tablas más pequeñas que describen información básica como quién es el estudiante, en qué institución estudia, cuál es su programa, cómo es su hogar y a qué año corresponde el registro. Al unir estas tablas se forma la tabla de hechos, que es la que conecta toda la información y guarda los resultados del examen. Esta organización ayuda a manejar bien la cantidad de datos y hace que el análisis sea más fácil y ordenado.

Una vez construido el modelo, se realizaron tres tipos de análisis: univariado, bivariado y multivariado. En el análisis univariado se revisaron las distribuciones de las variables, los valores atípicos, los tipos de datos y la presencia de duplicados o inconsistencias. En el análisis bivariado se compararon relaciones entre variables numéricas y categóricas. Finalmente, se exploraron métodos como componentes principales y análisis factorial con el fin de identificar patrones en los datos.

---

## Resultados

### 1) Alcance y composición de la base 

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Distrib%20sexo.png" alt="Figura 2. Distribución Género" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 2.</strong> Distribución Género
</p>

Se consolidó el universo de **Saber Pro 2021–2024** con **1.015.276** registros de estudiantes. La distribución por sexo es **58% mujeres** y **42% hombres**. Para **2024**, el microdato dispone de **281.601** observaciones y **90** variables (resultados y contexto).

### 2) Niveles de desempeño por módulo

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Distrib%20puntajes.png" alt="Figura 3. Distribución puntajes" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 3.</strong> Distribución Puntajes
</p>

El orden de desempeño promedio del periodo es: **Inglés** (más alto) → **Lectura Crítica** → **Razonamiento Cuantitativo** ≈ **Competencias Ciudadanas** → **Comunicación Escrita** (más bajo). **Comunicación Escrita** presenta la **mayor dispersión**.

### 3) Evolución temporal 2021–2024

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Puntajes%20anuales.png" alt="Figura 4. Promedio Anual" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 4.</strong> Promedio Anual
</p>


- **Inglés:** nivel alto y **estable**; el máximo se observa en **2024**.  
- **Lectura Crítica:** **mejora sostenida** a lo largo del cuatrienio.  
- **Razonamiento Cuantitativo:** **prácticamente plano**, sin cambios relevantes.  
- **Competencias Ciudadanas:** **descenso en 2023** con **recuperación en 2024**.  
- **Comunicación Escrita:** **serie más inestable** (cae en 2022, rebota en 2023 y cede en 2024).

### 4) Participación institucional y modalidad

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Universidades.jpg" alt="Figura 5. Universidades" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 5.</strong> Universidades
</p>

Las IES con mayor peso relativo en la cohorte son **Uniminuto** y **Politécnico Grancolombiano**. Por **modalidad**, los programas **presenciales** muestran **medianas ligeramente superiores** en **Razonamiento Cuantitativo**; **virtual** y **a distancia** quedan en niveles intermedios y **semipresencial** por debajo. Las diferencias son **moderadas** y con **alto solapamiento**.

### 5) Participación departamental

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Departamentos.jpg" alt="Figura 6. Departemnetos" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 6.</strong> Departamentos
</p>

La gráfica evidencia que Bogotá concentra la mayor cantidad de estudiantes por amplio margen, seguida por Antioquia y varios departamentos con volúmenes moderados. En general, la distribución es muy desigual, con un fuerte predominio de las principales ciudades del país en la presentación del SABER-PRO.

### 6) Factores del hogar y brechas asociadas

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/FAMD.png" alt="Figura 7. Componentes" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 7.</strong> Componentes
</p>

Se observa un **gradiente positivo por estrato socioeconómico** en todos los módulos, con la **brecha más marcada en Inglés**. La **educación de madre y padre** se asocia de forma consistente con mejores puntajes. La **disponibilidad de TIC** en el hogar (**internet** y **computador**) se relaciona con **ventajas pequeñas–moderadas**, más evidentes en **Inglés** y **Lectura**.

### 7) Relaciones entre módulos

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Correlaciones.png" alt="Figura 8. Relaciones" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 8.</strong> Relaciones
</p>

Los puntajes muestran **correlaciones altas** entre **Lectura Crítica**, **Razonamiento Cuantitativo** y **Competencias Ciudadanas**, indicando co-ocurrencia de buen desempeño. **Comunicación Escrita** exhibe **correlaciones bajas** con los demás módulos, lo que sugiere un comportamiento **más independiente**.

### 8) Análisis multivariado (FAMD)
La varianza se reparte en varias dimensiones: **una** explica ~**6,6%**, **dos** ~**10,9%** y **siete** ~**28,0%**, por lo que **no existe un único eje dominante**. La **Dimensión 1** se alinea con un **eje socioeconómico/educativo** (estrato, educación parental y TIC), con **Inglés** particularmente asociado a ese eje.

---

## Análisis de resultados

### 1) Alcance y composición de la base
El universo **Saber Pro 2021–2024** (1.015.276 registros) y el corte **2024** (281.601 observaciones; 90 variables) ofrecen potencia estadística para desagregar por **IES**, **modalidad**, **estrato** y **áreas de programa** sin comprometer estabilidad. La composición por sexo (≈58% mujeres; ≈42% hombres) es equilibrada en el agregado, por lo que no exige ponderaciones específicas. La amplitud de variables en 2024 permite integrar **contexto del hogar** y **resultados**, habilitando análisis multivariados consistentes. Toda comparación debe reportar **tamaños muestrales** y **medidas de dispersión** para evitar sobreinterpretar diferencias pequeñas.

### 2) Niveles de desempeño y variabilidad por módulo
Se sostiene un patrón claro: **Inglés** al tope, seguido por **Lectura Crítica**; **Razonamiento Cuantitativo** y **Competencias Ciudadanas** en franja media; **Comunicación Escrita** en el nivel más bajo. **Escrita** presenta, además, la **mayor dispersión**, señal de heterogeneidad en la competencia de producción de texto y posible variabilidad en criterios de evaluación entre programas/IES. Este binomio (media baja + alta variabilidad) indica necesidad de leer resultados con **percentiles/IQR** además de promedios.

### 3) Evolución temporal 2021–2024
Las trayectorias confirman señales robustas: **Inglés** alto y estable (máximo en 2024); **Lectura** con **mejora sostenida**; **Cuantitativo** prácticamente **plano**; **Ciudadanas** con **bache en 2023** y **recuperación en 2024**; **Escrita** es la **más volátil** (caída 2022, rebote 2023, nueva caída 2024). La interpretación debe privilegiar **dirección** y **estabilidad** por encima de variaciones anuales puntuales, distinguiendo tendencia de ruido.

### 4) Participación institucional y modalidad
La cohorte está influida por IES de gran tamaño (p. ej., Uniminuto y Politécnico Grancolombiano), lo que condiciona la composición. Por **modalidad**, **presencial** muestra **medianas ligeramente superiores** en **Cuantitativo**, con **alto solapamiento** frente a **virtual/distancia** y **semipresencial** por debajo. Las diferencias son **moderadas**; sin **controles por área, nivel y perfil del estudiante**, atribuir efectos a la modalidad introduce riesgo de sesgo por composición.

### 5) Participación departamental

Se identifica una fuerte concentración de estudiantes en Bogotá, que supera ampliamente al resto de departamentos, evidenciando su papel como el principal centro educativo del país. Antioquia ocupa el segundo lugar pero con una brecha considerable frente a la capital, mientras que Atlántico, Valle y Santander conforman un grupo intermedio con volúmenes importantes asociados a sus ciudades principales. Los demás departamentos del top (Bolívar, Norte de Santander, Boyacá, Nariño y Córdoba) presentan cifras menores pero que reflejan su peso regional. En conjunto, la distribución exhibe un patrón claramente desigual, donde la oferta educativa y la población estudiantil se concentran especialmente en unas pocas zonas urbanas de gran tamaño.

### 6) Factores del hogar y brechas asociadas
Se observa un **gradiente positivo por estrato** en todos los módulos, con **brecha más marcada en Inglés**. La **educación parental** se asocia consistentemente con mayores puntajes. La disponibilidad de **TIC en el hogar** (internet y computador) se vincula con **ventajas pequeñas–moderadas**, más visibles en **Inglés** y **Lectura**. Son **asociaciones** (no causalidad); en análisis comparativos deben incorporarse como **covariables de control** para reducir sesgos.

### 7) Relaciones entre módulos
Las correlaciones elevadas entre **Lectura Crítica**, **Razonamiento Cuantitativo** y **Competencias Ciudadanas** posicionan a **Lectura** como **indicador bisagra** del desempeño general: avances en esta dimensión suelen co-ocurrir con mejoras en otras. **Inglés** co-varía con **Lectura/Ciudadanas**, lo que sugiere un sustrato común de habilidades verbales/comprensivas. **Comunicación Escrita** muestra **correlaciones bajas** con el resto, por lo que su trayectoria es más **independiente** y debe analizarse por separado.

### 8) Estructura latente (FAMD)
La varianza se **distribuye en múltiples dimensiones** (≈6,6% en Dim.1; ≈10,9% acumulado en Dim.1–2; ≈28% en Dim.1–7), descartando un eje único dominante. La **Dimensión 1** se alinea con un **eje socioeconómico/educativo** (estrato, educación parental y TIC), con **Inglés** mostrando la asociación más fuerte con ese eje. La nube de individuos es **continua** (sin clústeres nítidos): predominan **gradientes** más que segmentos discretos; las segmentaciones deben sustentarse en **modelos multivariados con controles** y reporte de **incertidumbre**.

---

## Conclusión 

El proyecto alcanza su propósito al entregar un observatorio de datos del sistema educativo para 2021 a 2024 que integra fuentes oficiales, estandariza formatos y deja un flujo reproducible de ingesta, limpieza y validación listo para incorporar nuevos años sin rehacer procesos. El modelo en estrella construido sobre Saber Pro, con más de un millón de registros y noventa variables, permite consultas eficientes y análisis consistentes, mientras que los controles de calidad y la documentación técnica aseguran trazabilidad, auditoría y transferencia a otros equipos.

El examen de resultados muestra un sistema estable en el que Inglés se mantiene sólido, Lectura Crítica mejora de manera sostenida, Razonamiento Cuantitativo y Competencias Ciudadanas se ubican en una franja media y Comunicación Escrita aparece rezagada y con mayor variabilidad. Las diferencias asociadas al contexto del hogar se observan de forma consistente pero con magnitud moderada, y las variaciones por modalidad existen aunque presentan alto solapamiento, por lo que conviene interpretar comparaciones con controles adecuados. La estructura multivariada confirma un comportamiento verdaderamente multidimensional, con Lectura como eje articulador del desempeño y Escrita como dimensión que exige acciones específicas.

El valor para la gestión queda claro al contar con una línea base confiable, métricas estandarizadas y un camino de actualización simple que reduce tiempos operativos y mejora la comparabilidad entre periodos y grupos. El alcance de esta versión prioriza el análisis profundo de Saber Pro y deja SNIES y PTE preparados para usos agregados y futuros cruces, reconociendo que los vínculos a nivel individual no se implementaron por diferencias de granularidad y que las relaciones reportadas son asociativas. Con esta base, la organización queda en posición de integrar 2025 con mínimo esfuerzo, profundizar en intervenciones sobre Comunicación Escrita y ampliar los análisis con las demás fuentes para sostener una mejora continua y equitativa.


