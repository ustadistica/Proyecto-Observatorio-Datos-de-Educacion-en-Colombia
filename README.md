# Proyecto-Observatorio-Datos-de-Educación-en-Colombia 🎓

## 📊Dataset: Estudiantes Matriculados y Graduados en Instituciones de Educación Superior – Colombia – Año 2024

*Fuente:* Sistema Nacional de Información de la Educación Superior (SNIES), Ministerio de Educación Nacional.

## 📝Descripción
El dataset proviene del Sistema Nacional de Información de la Educación Superior (SNIES), administrado por el Ministerio de Educación Nacional, y reúne información consolidada sobre estudiantes matriculados y graduados en Instituciones de Educación Superior (IES) en Colombia durante 2024.

Los registros originales se encontraban en dos archivos separados (matriculados y graduados), los cuales fueron integrados en una sola base de datos. Se añadieron variables que diferencian los registros (Tipo: matriculado o graduado) y permiten estandarizar el conteo (Número). La base final cuenta con 42 variables y 121.715 registros, ofreciendo un panorama detallado sobre la dinámica de la educación superior en el país, tanto en ingreso como en egreso.

### Variables relevantes
- Institución de educación superior (IES), sector (oficial o privado), programa académico.
- Nivel académico (pregrado o posgrado), nivel de formación.
- Modalidad de estudio (presencial, distancia o virtual).
- Variables geográficas de departamento y municipio.
- Sexo de los estudiantes.
- Año y semestre de referencia.
- Número de matriculados o graduados.
- Variable Tipo (Graduados o Matriculados).

Esta información permite construir indicadores de cobertura, permanencia y eficiencia, y facilita la conexión con otros conjuntos de datos como las pruebas Saber del ICFES o los registros del Portal de Transparencia Económica (PTE).

## ⏳Frecuencia de actualización
Las bases de datos de Estudiantes Matriculados y Graduados 2024 del SNIES se publican *una vez al año*. Las IES envían su información al Ministerio de Educación Nacional cada semestre, pero el consolidado oficial se presenta en *mayo del año siguiente*. En este caso, los datos de 2024 se publicaron en mayo de 2025, asegurando un corte completo y validado a nivel nacional.  

Esta periodicidad permite comparaciones anuales, seguimiento de tendencias en matrícula y graduación, y evaluación de la evolución del sistema de educación superior en el mediano plazo.

## 🔎Calidad y retos de limpieza de los datos
La base consolidada resultante cuenta con 121.715 filas y 42 variables. Una de sus principales fortalezas es que *no presenta datos faltantes en las variables*, facilitando el análisis estadístico sin necesidad de imputaciones.

Durante la exploración y procesamiento se identificaron algunos retos importantes:

- *Integración de bases separadas:* Dado que los datos de matriculados y graduados se encontraban en archivos separados, se realizó un proceso de integración en RStudio, añadiendo la variable TIPO (con valores "Matriculado" o "Graduado") y una variable de conteo estandarizada (NÚMERO DE GRADUADOS/MATRICULADOS). Esto mejora la consistencia y facilita comparaciones dentro de un mismo marco de análisis.

- *Tratamiento de variables de identificación territorial:* En la carga inicial de datos en R, los códigos de departamento y municipio fueron interpretados como números, lo que ocasionó la pérdida de ceros a la izquierda (ejemplo: “05” → “5”). Se solucionó forzando el tratamiento de estas variables como texto, conservando la codificación oficial del DANE.

*Conclusión:* La calidad de los datos puede calificarse como alta, dado que las inconsistencias encontradas no comprometen la integridad de la información y fueron corregidas con procedimientos sencillos de limpieza.

## 🌐Vía de acceso
El acceso a la base es *público y gratuito*, reforzando la transparencia del sistema. Los archivos están disponibles en formato Excel (.xlsx) en el portal oficial del SNIES, dentro de la sección:  
Estadísticas → Bases consolidadas. Desde allí se pueden descargar las bases correspondientes a cada año y sus metadatos asociados.

Para el dataset trabajado, la información corresponde al corte estadístico de *2024*, publicado en *mayo de 2025*. Además, el portal ofrece un archivo complementario llamado “Metadatos bases consolidadas 2024”, que contiene la descripción detallada de cada variable y es fundamental para interpretar correctamente la estructura de las base.

🔗 *Enlace oficial:* [SNIES - Ministerio de Educación Nacional](https://snies.mineducacion.gov.co/portal/)

---


## 📊Dataset: Dataset: Saber Pro 2024 

*Fuente:*  Instituto Colombiano para la Evaluación de la Educación (ICFES), a través del portal 
oficial DataIcfes. 

## 📝Descripción
La base de datos Saber Pro 2024 corresponde a los microdatos anonimizados de los estudiantes que presentaron el examen de competencias genéricas en ese año. Contiene información detallada tanto de los resultados en las pruebas (Comunicación Escrita, Inglés, Lectura Crítica, Razonamiento Cuantitativo y Competencias Ciudadanas) como de variables sociodemográficas, familiares e institucionales de los evaluados. Gracias a esta estructura, es posible analizar no solo los puntajes y niveles de desempeño, sino también las condiciones de contexto que influyen en los resultados académicos.

En total, la base cuenta con 281.601 registros y 90 variables, donde cada fila corresponde a un estudiante que presentó el examen y cada columna a una característica o resultado asociado. Entre las variables se incluyen datos del estudiante (edad, género, tipo de documento, nivel del programa académico), de la institución de educación superior (nombre, carácter académico, origen) y del hogar (ocupación y educación de los padres, acceso a bienes y servicios). Adicionalmente, se incorporan indicadores como percentiles nacionales y por núcleo básico de conocimiento, lo cual facilita comparaciones entre diferentes grupos poblacionales o académicos. Este conjunto de datos es producido y difundido por el ICFES a través del portal DataIcfes, con el propósito de apoyar procesos de investigación, formulación de políticas y evaluación de la calidad de la educación superior en Colombia. 

Los microdatos permiten un análisis amplio de la equidad y calidad del sistema, pero garantizan el anonimato de los estudiantes. Así, la base Saber Pro 2024 constituye una herramienta clave para investigadores, instituciones y tomadores de decisiones interesados en comprender y mejorar el desempeño académico en el país.

## ⏳Frecuencia de actualización
El examen Saber Pro se aplica anualmente a los estudiantes de educación superior próximos a culminar sus programas académicos en Colombia. En consecuencia, la base de microdatos asociada también se actualiza con esta misma frecuencia: cada año, el ICFES publica los resultados correspondientes a la cohorte que presentó el examen. Esto asegura que investigadores, instituciones y formuladores de política cuenten con información reciente y comparable en el tiempo, permitiendo el análisis de tendencias y cambios en el desempeño de los estudiantes y en las condiciones de contexto. La publicación de los microdatos generalmente ocurre unos meses después de la aplicación del examen, tras los procesos de consolidación, validación y anonimización de la información. Esta dinámica de actualización anual hace que la base de datos sea un insumo confiable para estudios longitudinales, ya que ofrece series continuas año tras año. Además, al estar disponible en el portal DataIcfes, los usuarios pueden acceder a los archivos históricos junto con la versión más reciente, facilitando el análisis comparativo entre diferentes periodos académicos.

## 🔎Calidad y retos de limpieza de los datos
La calidad de la base de datos Saber Pro 2024 es consistente con los estándares de difusión de microdatos del ICFES: los registros se encuentran anonimizados, las variables están estandarizadas y cuentan con documentación en el diccionario de datos, lo cual facilita su interpretación y análisis. No obstante, al tratarse de información masiva con más de 280 mil registros y 90 variables, se observan algunos desafíos relacionados con valores faltantes, respuestas inconsistentes en las preguntas de contexto y variaciones en los formatos de ciertas variables categóricas. Estos aspectos requieren procesos previos de validación y depuración antes de realizar análisis estadísticos o modelos comparativos. Entre los principales retos de limpieza se encuentran la gestión de valores nulos o no reportados, la recodificación de categorías con nombres largos o inconsistentes, y la homogeneización de variables que pueden presentar diferencias frente a años anteriores (por ejemplo, en escalas de desempeño o en preguntas de caracterización socioeconómica). Asimismo, algunos estudiantes pueden tener registros incompletos en pruebas específicas, lo que obliga a los analistas a definir estrategias de imputación o exclusión según el objetivo del estudio. En este sentido, aunque la base es robusta y confiable, su uso óptimo exige un trabajo riguroso de preprocesamiento que asegure la coherencia y comparabilidad de los resultados.

## 🌐Vía de acceso
El acceso a la base de datos Saber Pro 2024 se realiza a través del portal oficial DataIcfes, que centraliza la publicación de los microdatos anonimizados de las diferentes evaluaciones aplicadas por el ICFES. Desde esta plataforma, los usuarios pueden consultar la documentación técnica, descargar los diccionarios de variables y acceder a los archivos en formato txt, lo que garantiza un uso ágil de la información por parte de investigadores, instituciones de educación superior y público en general. Adicionalmente, los microdatos se encuentran almacenados en el SharePoint institucional del ICFES, el cual actúa como repositorio seguro y de respaldo. Esta infraestructura asegura la disponibilidad, preservación y actualización de las bases de datos, manteniendo tanto la trazabilidad de las versiones históricas como el acceso a las más recientes. De este modo, el ICFES garantiza un canal de distribución confiable que combina transparencia en la difusión pública de la información y control sobre la integridad de los archivos.


🔗 *Enlace oficial:* [Instituto Colombiano para la Evaluación de la Educación - ICFES](https://www.icfes.gov.co/investigaciones/data-icfes/)

---

## 📊Dataset: Presupuesto General de la Nación – Educación 2024

*Fuente:*  Portal de Transparencia Economica (PTE)

## 📝Descripción
El dataset **Presupuesto General de la Nación – Educación 2024** corresponde a la información oficial publicada por el **Portal de Transparencia Económica (PTE)** del Ministerio de Hacienda y Crédito Público.  

El Presupuesto General de la Nación (PGN) es el principal instrumento financiero del Estado colombiano y refleja cómo se asignan y ejecutan los recursos públicos en cada vigencia fiscal. Dentro de él, el sector **Educación** constituye uno de los rubros más relevantes, al ser históricamente el sector con mayor apropiación del presupuesto nacional.  

Este dataset muestra, **mes a mes durante el año 2024**, la ejecución de los recursos destinados al sector Educación. Sus principales variables son:  

- **Apropiación Vigente (1):** monto del presupuesto autorizado para la vigencia.  
- **Compromisos (2):** recursos ya asignados formalmente a un propósito.  
- **Obligaciones (3):** compromisos respaldados legal o contractualmente, que deben pagarse.  
- **Pagos (4):** giros efectivamente realizados.  
- **Apropiación sin comprometer (5 = 1 – 2):** saldo de presupuesto aún no comprometido.  
- **Comp./Apro. (6 = 2/1):** porcentaje del presupuesto que fue comprometido.  
- **Oblig./Apro. (7 = 3/1):** porcentaje del presupuesto que se convirtió en obligaciones.  
- **Pago/Apro. (8 = 4/1):** porcentaje del presupuesto que fue efectivamente pagado.  
- **Oblig./Comp. (9 = 3/2):** proporción de compromisos que pasaron a ser obligaciones.  
- **Pago/Oblig. (10 = 4/3):** proporción de obligaciones que ya fueron pagadas.  

Este dataset es estratégico porque evidencia cómo se materializa la política pública en educación, mostrando el flujo real de recursos que financian **programas de cobertura, calidad y permanencia en el sistema educativo colombiano** (desde preescolar hasta educación superior, incluyendo pregrado y posgrado). Su disponibilidad mensual permite observar la dinámica de la ejecución, identificar en qué periodos del año se concentran los desembolsos y facilitar comparaciones con indicadores de cobertura (SNIES) y calidad académica (ICFES).


## ⏳Frecuencia de actualización
El dataset tiene una **frecuencia de actualización mensual**.  
Cada mes, el PTE publica los reportes de ejecución acumulada con corte a la fecha, lo que permite seguir la trazabilidad del gasto público en Educación durante toda la vigencia fiscal. Al final del año (diciembre), se cuenta con el consolidado anual definitivo.  


## 🔎Calidad y retos de limpieza de los datos
- **Fuente oficial:** Ministerio de Hacienda y Crédito Público, a través del **Portal de Transparencia Económica (PTE)**.  
- **Cobertura:** Nacional, con desglose por sector presupuestal (en este caso, Educación).  
- **Confiabilidad:** Alta, ya que corresponde a cifras oficiales reportadas por el Sistema Integrado de Información Financiera (SIIF Nación).  
- **Retos en el uso:**  
  - Los archivos mensuales se presentan en formato Excel con múltiples cuadros; es necesario ubicar el cuadro que presenta la ejecución por sectores y extraer la fila correspondiente a Educación.  
  - Puede haber variaciones menores en el formato de un mes a otro.  
  - Se requiere consolidación de los 12 meses para análisis anual y comparativo. 

## 🌐Vía de acceso
Los datos del Presupuesto General de la Nación – Educación 2024 se encuentran disponibles en el PTE dentro de la ruta *Presupuesto General de la Nación → Ejecución Presupuestal → Vigencia 2024 → carpetas por mes → archivo “Cuadros informe de ejecución”*. La información puede descargarse en formatos Excel y PDF, con acceso totalmente abierto y gratuito, lo que permite tanto la consulta en línea como la descarga directa de los archivos para su análisis.


🔗 *Enlace oficial:* [Portal de Transparencia Economica (PTE)]
(https://www.pte.gov.co/presupuesto-general-nacion/seguimiento-ejecucion-presupuestal-gastos/2024)



## Viabilidad 

**Factibilidad de uso:** Las tres bases —SNIES (matriculados y graduados 2024), ICFES (Saber Pro 2024) y PTE (Presupuesto Educación 2024)— presentan una alta factibilidad de uso, pues abarcan los tres ejes estratégicos del Observatorio: cobertura, calidad y financiamiento.  

**Cobertura y comparabilidad:** Son fuentes oficiales, nacionales y de acceso abierto. El SNIES refleja la dinámica de ingreso y egreso en las IES, el ICFES consolida resultados académicos y el PTE muestra la ejecución presupuestal. Su comparabilidad es posible gracias a variables comunes como institución, nivel académico y territorio.  

**Hallazgos preliminares:** Los datos son consistentes y confiables, aunque fue necesario integrar archivos en el SNIES, depurar microdatos del ICFES y unificar formatos en el PTE. Estos retos fueron solucionables y no afectan la calidad general.  

**Usos estratégicos:** En conjunto, las bases permiten relacionar inversión pública con acceso, desempeño y resultados en la educación superior, identificar diferencias entre instituciones o territorios y analizar brechas regionales en cobertura y calidad.  

**Recomendaciones:** Integrar las tres fuentes como núcleo del Observatorio, construir un diccionario común de variables, estandarizar códigos geográficos y categorías, realizar cruces entre bases y desarrollar visualizaciones claras que comuniquen los resultados a tomadores de decisiones y público general.  
