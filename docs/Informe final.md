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
