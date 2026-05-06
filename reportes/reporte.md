# Reporte de Investigación: Comparación de Bases de Datos SNIES

## Fecha
21 de marzo de 2026

## Resumen Ejecutivo

Durante la investigación para el proyecto "Observatorio de Datos de Educación en Colombia", se realizó una comparación entre las bases de datos disponibles en **datos.gov.co** y las bases oficiales del **Sistema Nacional de Información de la Educación Superior (SNIES)**.

## Hallazgos Principales

### 1. Incompletitud de datos en datos.gov.co

Al acceder a la plataforma de datos.gov.co en busca de la base de datos de matriculados SNIES, se encontró que:

- **Falta de cobertura temporal**: Los datos disponibles en datos.gov.co presentan lagunas significativas en el rango temporal 2015-2024
- **Ausencia de variables clave**: Muchas variables esenciales para el análisis educativo no están disponibles o están incompletas
- **Problemas de consistencia**: Los formatos y estructuras de los datos varían considerablemente entre años

### 2. Calidad y completitud de SNIES

En contraste, al acceder directamente a la página oficial de SNIES (https://snies.mineducacion.gov.co/portal/ESTADISTICAS/Bases-consolidadas/):

- **Cobertura completa**: Disponibilidad de datos para todos los años del periodo 2015-2024
- **Consistencia metodológica**: Estandarización de variables y formatos a través del tiempo
- **Variables completas**: Acceso a todas las variables necesarias para un análisis integral
- **Actualización oportuna**: Los datos están actualizados y validados por la entidad oficial

### 3. Implicaciones para el Proyecto

Esta comparación determinó que:

1. **datos.gov.co no es viable** como fuente principal para este proyecto debido a la incompletitud de los datos
2. **SNIES es la fuente confiable** y debe ser la base principal del observatorio
3. **Se requiere ingesta directa** desde la página oficial de SNIES para garantizar la calidad del análisis

## Recomendaciones

1. **Utilizar SNIES como fuente principal** para todas las bases de datos de matriculados y graduados
2. **Implementar proceso de descarga automática** desde la página oficial de SNIES
3. **Establecer protocolo de validación** para asegurar la integridad de los datos descargados
4. **Documentar las diferencias** encontradas para futuras referencias

## Conclusión

La decisión de utilizar directamente las bases de datos de SNIES en lugar de los datos disponibles en datos.gov.co garantiza la integridad, completitud y confiabilidad del observatorio de datos educativos. Esta elección metodológica es fundamental para asegurar la validez de los análisis y conclusiones del proyecto.

## Metodología de Investigación

- **Acceso a datos.gov.co**: Revisión exhaustiva de datasets relacionados con educación superior
- **Acceso a SNIES**: Descarga y análisis de las bases consolidadas oficiales
- **Comparación sistemática**: Evaluación de cobertura temporal, variables disponibles y consistencia de datos
- **Validación cruzada**: Verificación de la correspondencia entre ambas fuentes donde era posible

## Responsable
Equipo de Desarrollo del Observatorio de Datos de Educación en Colombia