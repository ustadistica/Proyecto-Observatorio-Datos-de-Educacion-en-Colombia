# Proyecto-Observatorio-Datos-de-Educacion-en-Colombia

# Dataset: Estudiantes Matriculados y Graduados en Instituciones de Educación Superior – Colombia – Año 2024

*Fuente:* Sistema Nacional de Información de la Educación Superior (SNIES), Ministerio de Educación Nacional.

---

## Descripción
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

---

## Frecuencia de actualización
La base de datos de Estudiantes Matriculados y Graduados 2024 del SNIES se publica *una vez al año. Las IES envían su información al Ministerio de Educación Nacional cada semestre, pero el consolidado oficial se presenta en **mayo del año siguiente*. En este caso, los datos de 2024 se publicaron en mayo de 2025, asegurando un corte completo y validado a nivel nacional.  

Esta periodicidad permite comparaciones anuales, seguimiento de tendencias en matrícula y graduación, y evaluación de la evolución del sistema de educación superior en el mediano plazo.

---

## Calidad y retos de limpieza de los datos
La base consolidada resultante cuenta con 121.715 filas y 42 variables. Una de sus principales fortalezas es que *no presenta datos faltantes en las variables principales*, facilitando el análisis estadístico sin necesidad de imputaciones.

Durante la exploración y procesamiento se identificaron algunos retos importantes:

- *Integración de bases separadas:* Dado que los datos de matriculados y graduados se encontraban en archivos separados, se realizó un proceso de integración en RStudio, añadiendo la variable TIPO (con valores "Matriculado" o "Graduado") y una variable de conteo estandarizada (NÚMERO DE GRADUADOS/MATRICULADOS). Esto mejora la consistencia y facilita comparaciones dentro de un mismo marco de análisis.

- *Tratamiento de variables de identificación territorial:* En la carga inicial de datos en R, los códigos de departamento y municipio fueron interpretados como números, lo que ocasionó la pérdida de ceros a la izquierda (ejemplo: “05” → “5”). Se solucionó forzando el tratamiento de estas variables como texto, conservando la codificación oficial del DANE.

*Conclusión:* La calidad de los datos puede calificarse como alta, dado que las inconsistencias encontradas no comprometen la integridad de la información y fueron corregidas con procedimientos sencillos de limpieza.

---

## Vía de acceso
El acceso a la base es *público y gratuito*, reforzando la transparencia del sistema. Los archivos están disponibles en formato Excel (.xlsx) en el portal oficial del SNIES, dentro de la sección:  
Estadísticas → Bases consolidadas. Desde allí se pueden descargar las bases correspondientes a cada año y sus metadatos asociados.

Para el dataset trabajado, la información corresponde al corte estadístico de *2024, publicado en **mayo de 2025*. Además, el portal ofrece un archivo complementario llamado “Metadatos bases consolidadas 2024”, que contiene la descripción detallada de cada variable y es fundamental para interpretar correctamente la estructura de la base.

*Enlace oficial:* [SNIES - Ministerio de Educación Nacional](https://snies.mineducacion.gov.co/portal/)
