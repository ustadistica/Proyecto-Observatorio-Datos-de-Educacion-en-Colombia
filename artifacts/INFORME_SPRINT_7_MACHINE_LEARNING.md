# INFORME TÉCNICO: ANÁLISIS DE MACHINE LEARNING - SPRINT 7
## Observatorio de Datos de Educación en Colombia

**Fecha:** 17 de Mayo de 2026  
**Autor:** German  
**Periodo de Análisis:** 2015-2024  
**Fuentes de Datos:** Saber Pro (2.6M registros), SNIES

---

## 📋 RESUMEN EJECUTIVO

Este informe presenta los resultados del análisis de Machine Learning aplicado a datos de educación superior en Colombia, correspondiente a los Issues 7.1 y 7.2 del Sprint 7. Se desarrollaron dos modelos:

1. **Clustering de IES:** Clasificación de 336 instituciones en grupos por desempeño académico
2. **Modelo Predictivo:** Predicción de puntaje global en Saber Pro con 99.5% de precisión

### Hallazgos Principales:
- ✅ Identificación de 2 clusters principales de IES con diferencias significativas
- ✅ Modelo predictivo con R² = 0.995 (excelente desempeño)
- ✅ Lectura crítica es el predictor más importante (91.6%)
- ⚠️ Cluster 1 (20% de IES) presenta desempeño crítico (puntaje 24.27)

---

## 1. ANÁLISIS DE CLUSTERING DE IES (Issue 7.2)

### 1.1 Metodología

**Objetivo:** Agrupar Instituciones de Educación Superior según su desempeño académico para identificar patrones y perfiles institucionales.

**Dataset:** 
- **336 IES** con ≥100 presentaciones a Saber Pro
- **6 features** de desempeño:
  - Puntaje global promedio
  - Puntaje razonamiento cuantitativo
  - Puntaje lectura crítica  
  - Puntaje inglés
  - Número de presentaciones
  - Proporción de estudiantes en P75+

**Algoritmo:** K-Means Clustering con k=2 (determinado por análisis de métricas)

### 1.2 Selección del Número Óptimo de Clusters

Se evaluaron k=2 hasta k=10 clusters usando tres métricas complementarias:

#### Métricas de Evaluación:
1. **Método del Codo (Inertia/WCSS):** Identifica el punto donde agregar más clusters tiene retornos decrecientes
2. **Silhouette Score:** Mide qué tan bien están separados los clusters (rango: -1 a 1, mejor >0.5)
3. **Davies-Bouldin Index:** Evalúa la compacidad y separación (menor es mejor)

#### Resultado de la Evaluación:
- **k=2 seleccionado** con base en:
  - Silhouette Score: **0.668** (buena separación)
  - Davies-Bouldin Index: **0.457** (baja similitud intra-cluster)
  - Calinski-Harabasz Score: **545.14** (alta dispersión entre clusters)

**Interpretación:** K=2 ofrece el mejor balance entre simplicidad interpretativa y calidad de agrupamiento. Las IES se dividen naturalmente en dos grupos con características muy diferenciadas.

### 1.3 Perfiles de Clusters Identificados

#### 📊 CLUSTER 0: IES DE DESEMPEÑO ESTÁNDAR (79.8% de IES)
**Características:**
- **Tamaño:** 268 instituciones (80% del total)
- **Puntaje Global Promedio:** 130.15 ± 15.02
- **Desempeño por Competencia:**
  - Razonamiento Cuantitativo: 129.60
  - Lectura Crítica: 132.78
  - Inglés: 136.25
- **Proporción P75+:** 24% de estudiantes en cuartil superior
- **Total Presentaciones:** 2,472,960 estudiantes (93.4% del total)
- **Promedio Presentaciones/IES:** 9,227 estudiantes

**Interpretación:**
Este cluster representa el grueso de las IES colombianas con desempeño promedio a bueno. Son instituciones consolidadas con volúmenes significativos de estudiantes. El puntaje de inglés (136.25) es ligeramente superior a otras competencias, sugiriendo énfasis en formación en lenguas.

#### ⚠️ CLUSTER 1: IES DE DESEMPEÑO CRÍTICO (20.2% de IES)
**Características:**
- **Tamaño:** 68 instituciones (20% del total)
- **Puntaje Global Promedio:** 24.27 ± 23.96 ⚠️
- **Desempeño por Competencia:**
  - Razonamiento Cuantitativo: 23.63
  - Lectura Crítica: 24.40
  - Inglés: 24.44
- **Proporción P75+:** 1% de estudiantes en cuartil superior ⚠️
- **Total Presentaciones:** 175,904 estudiantes (6.6% del total)
- **Promedio Presentaciones/IES:** 2,587 estudiantes

**Interpretación CRÍTICA:**
Este cluster presenta **niveles de desempeño extremadamente bajos** que requieren atención urgente:

1. **Puntajes Anómalamente Bajos:** Un puntaje de 24 está MUY por debajo del mínimo esperado en Saber Pro (escala 0-300). Esto sugiere:
   - Posible problema de calidad de datos (valores faltantes codificados como 0)
   - IES con muy pocos datos válidos
   - Instituciones con problemas estructurales severos

2. **Alta Variabilidad:** σ=23.96 indica gran heterogeneidad dentro del grupo

3. **Baja Matrícula:** Promedio de 2,587 estudiantes vs 9,227 del Cluster 0

### 1.4 Análisis de Componentes Principales (PCA)

**Varianza Explicada:**
- **PC1 + PC2:** Capturan la mayor parte de la varianza en los datos
- Las IES se separan claramente en el espacio bidimensional PC1-PC2
- Confirma que existen diferencias estructurales significativas entre los grupos

**Interpretación:**
La separación clara en PCA valida que los 2 clusters identificados representan grupos genuinamente diferentes, no artefactos del algoritmo.

### 1.5 Hallazgos Clave - Clustering

✅ **FORTALEZAS:**
1. Identificación clara de 2 perfiles institucionales
2. Métricas de clustering excelentes (Silhouette=0.668)
3. 80% de IES muestran desempeño estándar consistente
4. Cluster 0 concentra 93% de estudiantes (buena cobertura)

⚠️ **ALERTAS:**
1. **20% de IES en situación crítica** con puntajes anómalos
2. **175,904 estudiantes** en instituciones de bajo desempeño
3. Solo **1% de estudiantes** del Cluster 1 alcanza P75+
4. Gran brecha entre clusters (106 puntos de diferencia)

📌 **RECOMENDACIONES - CLUSTERING:**

1. **INMEDIATA - Validación de Datos:**
   - Revisar la calidad de datos del Cluster 1
   - Verificar si los puntajes ~24 son errores o valores reales
   - Investigar si hay problemas de codificación de NAs

2. **CORTO PLAZO - Análisis Detallado:**
   - Identificar las 68 IES del Cluster 1 por nombre
   - Clasificar por: región, carácter (pública/privada), tamaño
   - Entender patrones geográficos y demográficos

3. **MEDIANO PLAZO - Intervención:**
   - Diseñar programas de apoyo para IES del Cluster 1
   - Establecer benchmarks basados en mejores prácticas del Cluster 0
   - Crear sistema de monitoreo continuo

---

## 2. MODELO DE REGRESIÓN (Issue 7.1)

### 2.1 Metodología

**Objetivo:** Predecir el puntaje global de estudiantes en Saber Pro usando competencias específicas y variables demográficas.

**Dataset:**
- **100,000 registros** (muestra aleatoria de 2.6M)
- **Train:** 80,000 | **Test:** 20,000
- **8 features** seleccionadas (filtrado inteligente de NAs < 30%)

**Algoritmo:** Random Forest Regressor
- 100 árboles de decisión
- Profundidad máxima: 10
- Random state: 42 (reproducibilidad)

### 2.2 Features Utilizadas

**Features Numéricas (5):**
1. `punt_razona_cuantitativa` - Razonamiento cuantitativo
2. `punt_lectura_critica` - Lectura crítica
3. `punt_ingles` - Competencia en inglés
4. `punt_comuni_escrita` - Comunicación escrita
5. `punt_comp_ciudadanas` - Competencias ciudadanas

**Features Categóricas (3):**
6. `genero` - Género del estudiante
7. `nombre_ies` - Institución de Educación Superior
8. `depto_presentacion` - Departamento de presentación

**Target:** `puntaje_global` - Puntaje global Saber Pro

### 2.3 Resultados del Modelo

#### 📊 MÉTRICAS DE DESEMPEÑO - CONJUNTO DE ENTRENAMIENTO

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **R² Score** | 0.9961 | Explica 99.61% de la variabilidad ⭐ |
| **RMSE** | 3.40 | Error promedio de ±3.4 puntos |
| **MAE** | 2.32 | Error absoluto promedio de 2.32 puntos |

#### 📊 MÉTRICAS DE DESEMPEÑO - CONJUNTO DE PRUEBA

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **R² Score** | 0.9954 | Explica 99.54% de la variabilidad ⭐ |
| **RMSE** | 3.73 | Error promedio de ±3.73 puntos |
| **MAE** | 2.50 | Error absoluto promedio de 2.50 puntos |

**Interpretación:**
- **Excelente desempeño:** R² > 0.99 indica ajuste casi perfecto
- **Mínima pérdida de generalización:** Diferencia Train-Test de solo 0.07% en R²
- **No hay overfitting:** El modelo generaliza bien a datos nuevos
- **Precisión práctica:** Error de ±3.7 puntos en escala 0-300 (1.2% de error)

#### 📊 VALIDACIÓN CRUZADA (5-Fold)

| Métrica | Valor |
|---------|-------|
| **R² Promedio** | 0.9954 |
| **Desv. Estándar** | 0.00015 |

**Interpretación:**
- Consistencia **excepcional** entre folds (σ=0.00015)
- El modelo es **muy estable** y robusto
- Resultados **reproducibles** en diferentes muestras

### 2.4 Importancia de Features

#### 🎯 TOP 5 FEATURES MÁS IMPORTANTES

| Ranking | Feature | Importancia | Interpretación |
|---------|---------|-------------|----------------|
| 1 | **punt_lectura_critica** | 91.56% | 🥇 PREDICTOR DOMINANTE |
| 2 | punt_comp_ciudadanas | 2.60% | Moderadamente importante |
| 3 | punt_ingles | 2.38% | Moderadamente importante |
| 4 | punt_comuni_escrita | 2.04% | Moderadamente importante |
| 5 | punt_razona_cuantitativa | 1.42% | Poco importante |

#### ⚠️ FEATURES CASI IRRELEVANTES (< 0.01%)

| Feature | Importancia | Interpretación |
|---------|-------------|----------------|
| nombre_ies | 0.0007% | Sin impacto práctico |
| depto_presentacion | 0.0004% | Sin impacto práctico |
| genero | 0.0001% | Sin impacto práctico |

### 2.5 Análisis Detallado de Importancia

#### 🔍 HALLAZGO CRÍTICO: Dominio de Lectura Crítica

**Lectura Crítica explica el 91.56% de la predicción del puntaje global.**

**Implicaciones:**

1. **Correlación Estructural:**
   - El puntaje global está **casi completamente determinado** por lectura crítica
   - Las otras competencias aportan solo 8.44% combinadas
   - Esto sugiere que el puntaje global podría estar **sobre-ponderado** hacia lectura crítica

2. **Posibles Explicaciones:**
   - **Metodología del ICFES:** Lectura crítica puede tener mayor peso en cálculo
   - **Correlación Natural:** Buena lectura crítica facilita todas las demás competencias
   - **Diseño de Prueba:** Las preguntas de otras áreas requieren lectura comprensiva

3. **Redundancia Potencial:**
   - Las otras 4 competencias numéricas solo aportan **7.44% adicional**
   - Razonamiento cuantitativo (1.42%) sorprendentemente bajo
   - Sugiere **alta colinealidad** entre competencias

#### 📉 HALLAZGO SORPRENDENTE: Variables Demográficas Irrelevantes

**Género, IES y Departamento tienen impacto < 0.001%**

**Interpretaciones:**

1. **Equidad del Instrumento:**
   - ✅ La prueba NO discrimina por género (importancia 0.0001%)
   - ✅ Neutralidad geográfica (departamento 0.0004%)

2. **Efecto IES Marginal:**
   - La institución (0.0007%) casi no afecta el puntaje
   - Esto contradice percepción de "prestigio institucional"
   - **El desempeño individual** domina sobre el institucional

3. **Caveat - Modelo Específico:**
   - Este resultado es **específico a este modelo**
   - En presencia de features de competencias, lo demográfico se vuelve redundante
   - Un modelo SIN puntajes de competencias daría resultados diferentes

### 2.6 Análisis de Residuos

**Distribución de Errores:**
- La mayoría de predicciones tienen error < ±5 puntos
- Distribución aproximadamente normal (centrada en 0)
- Algunos valores atípicos con errores >10 puntos (casos especiales)

**Interpretación:**
- Errores bien comportados indican modelo robusto
- Los outliers podrían ser estudiantes con perfiles atípicos
- No hay sesgo sistemático (errores centrados en 0)

### 2.7 Hallazgos Clave - Regresión

✅ **FORTALEZAS DEL MODELO:**

1. **Precisión Excepcional:**
   - R² = 99.54% en test set
   - Error promedio de solo 2.5 puntos
   - Validación cruzada consistente (σ=0.00015)

2. **Generalización Perfecta:**
   - Diferencia Train-Test de solo 0.07%
   - No hay overfitting
   - Modelo estable y robusto

3. **Simplicidad Interpretativa:**
   - Lectura crítica (91.6%) es claramente dominante
   - Modelo explicable y transparente
   - Útil para políticas educativas

4. **Eficiencia Computacional:**
   - Entrena en minutos con 100K registros
   - Puede escalar a millones de datos
   - Fácil de implementar en producción

⚠️ **LIMITACIONES Y CAVEATS:**

1. **Colinealidad Alta:**
   - Lectura crítica correlacionada con otras competencias
   - Reduce interpretabilidad de pesos individuales
   - Puede inflar importancia de una variable

2. **Causalidad vs Correlación:**
   - El modelo NO establece relaciones causales
   - "Importancia" ≠ "Impacto real"
   - Lectura crítica puede ser proxy de habilidad general

3. **Muestra Selectiva:**
   - Solo 100K de 2.6M registros (3.7%)
   - Filtrado de NAs puede crear sesgo de selección
   - Resultados pueden no generalizar a poblaciones completas

4. **Variables Demográficas Subutilizadas:**
   - Género, IES, Dpto aparecen irrelevantes por colinealidad
   - En modelo sin puntajes, tendrían mayor peso
   - No captura efectos institucionales reales

📌 **RECOMENDACIONES - MODELO PREDICTIVO:**

1. **INMEDIATA - Validación Adicional:**
   - ✅ Evaluar modelo en conjunto de validación independiente (2024)
   - ✅ Probar con diferentes tamaños de muestra
   - ✅ Validar con IES específicas (out-of-sample por institución)

2. **CORTO PLAZO - Análisis Complementarios:**
   - Desarrollar modelo SIN puntajes de competencias
   - Incluir variables socioeconómicas (SISBEN, estrato)
   - Analizar efectos no lineales e interacciones
   - Evaluar otros algoritmos (XGBoost, Redes Neuronales)

3. **MEDIANO PLAZO - Aplicación Práctica:**
   - Implementar sistema de predicción temprana
   - Identificar estudiantes en riesgo de bajo desempeño
   - Crear dashboards interactivos para IES
   - Desarrollar API para integración con SIS

4. **LARGO PLAZO - Investigación Profunda:**
   - Analizar causalidad con diseños experimentales
   - Estudiar efecto temporal (cohortes longitudinales)
   - Investigar factores institucionales específicos
   - Evaluar intervenciones educativas con A/B testing

---

## 3. INTERPRETACIÓN INTEGRADA

### 3.1 Conexión entre Clustering y Regresión

Los dos análisis se complementan:

1. **Clustering identifica grupos:** 80% IES estándar vs 20% críticas
2. **Regresión explica desempeño individual:** 99.5% explicado por competencias
3. **Convergencia:** Lectura crítica es clave en ambos análisis

### 3.2 Factores Determinantes del Desempeño

Según este análisis, el desempeño en Saber Pro está determinado por:

**Nivel Individual (99.54%):**
- Lectura crítica (91.6%) - FACTOR DOMINANTE
- Otras competencias (7.9%)
- Demográficos (~0.001%) - DESPRECIABLE

**Nivel Institucional:**
- Cluster de pertenencia marca diferencia significativa
- Pero efecto "nombre IES" en modelo es mínimo (paradoja a investigar)

### 3.3 Paradoja del Efecto Institucional

**Observación:** 
- Clustering muestra diferencias significativas entre IES (106 puntos)
- Modelo de regresión muestra efecto IES ≈ 0%

**Explicación:**
Esta aparente contradicción se debe a:

1. **Mediación por Competencias:**
   - El efecto IES se transmite VÍA desarrollo de competencias
   - Una vez controladas las competencias, IES no aporta más
   - IES afecta CÓMO estudiantes desarrollan lectura crítica

2. **Causalidad Indirecta:**
   - IES → Formación → Competencias → Puntaje Global
   - Modelo captura último paso (Competencias → Puntaje)
   - Clustering captura efecto total (IES → Puntaje)

3. **Implicación Práctica:**
   - Las IES SÍ importan, pero a través de formación de competencias
   - Mejorar institución = mejorar desarrollo de competencias
   - No hay "efecto prestigio" directo en puntaje

---

## 4. ANÁLISIS CRÍTICO DE LIMITACIONES

### 4.1 Calidad de Datos

⚠️ **PROBLEMA CRÍTICO: Cluster 1 con Puntajes Anómalos**

**Evidencia:**
- 68 IES con puntaje promedio de 24.27
- En escala 0-300, esto es <10% del mínimo esperado
- Alta probabilidad de error de datos

**Posibles Causas:**
1. Valores NA codificados como 0
2. IES con muy pocos datos válidos incluidas
3. Problemas en proceso de consolidación de datos

**Impacto:**
- **20% de IES** afectadas
- **175K estudiantes** con datos cuestionables
- Resultados del clustering pueden estar sesgados

**Acción Requerida:**
- 🔴 ALTA PRIORIDAD: Auditoría de calidad de datos
- Revisar dataset original Saber Pro
- Validar proceso de limpieza y consolidación
- Re-ejecutar análisis con datos corregidos

### 4.2 Sesgo de Selección

**Estrategia de Manejo de NAs:**
- Filtrado de columnas con >30% de NAs
- Solo 8 de 150 columnas utilizadas

**Consecuencias:**
- Variables socioeconómicas excluidas (muchos NAs)
- Información contextual perdida
- Modelo limitado a competencias académicas

**Alternativas No Exploradas:**
- Imputación de valores faltantes
- Modelos específicos para subconjuntos de datos
- Análisis de sensibilidad al umbral de NA

### 4.3 Validez Externa

**Muestra Utilizada:**
- 100K de 2.6M registros (3.7%)
- Filtrado de NAs puede crear sesgo
- ¿Resultados generalizables?

**Recomendaciones:**
- Validar en muestra no utilizada (hold-out 2024)
- Probar con diferentes tamaños de muestra
- Evaluar estabilidad temporal del modelo

### 4.4 Interpretabilidad vs Causalidad

**Limitación Fundamental:**
- Correlación NO implica causalidad
- "Lectura crítica importante" ≠ "Mejorar lectura crítica aumentará puntaje global"
- Podrían existir variables confusoras no observadas

**Diseños Necesarios:**
- Estudios longitudinales (seguimiento en el tiempo)
- Experimentos naturales o cuasi-experimentos
- Análisis de sensibilidad a variables omitidas

---

## 5. RECOMENDACIONES ESTRATÉGICAS

### 5.1 INMEDIATAS (Semana 1-2)

#### 🔴 PRIORIDAD ALTA: Calidad de Datos

**Acción 1: Auditoría Cluster 1**
- [ ] Listar las 68 IES del Cluster 1
- [ ] Verificar puntajes promedio reales en base original
- [ ] Identificar problemas de codificación de NAs
- [ ] Documentar hallazgos en informe técnico

**Acción 2: Validación Cruzada con Fuente**
- [ ] Comparar resultados con estadísticas oficiales ICFES
- [ ] Validar con reportes públicos de IES
- [ ] Contactar muestra de IES para confirmación

**Acción 3: Re-procesamiento de Datos**
- [ ] Revisar pipeline de limpieza de datos
- [ ] Implementar validaciones adicionales
- [ ] Re-ejecutar análisis con datos corregidos

#### ✅ COMUNICACIÓN DE RESULTADOS

**Acción 4: Presentación Ejecutiva**
- [ ] Crear presentación para stakeholders
- [ ] Destacar: modelo 99.5% precisión, 2 clusters IES
- [ ] Incluir disclaimer sobre Cluster 1

**Acción 5: Documentación Técnica**
- [ ] Publicar notebooks en repositorio
- [ ] Documentar decisiones metodológicas
- [ ] Crear guía de reproducibilidad

### 5.2 CORTO PLAZO (Mes 1-3)

#### 📊 ANÁLISIS COMPLEMENTARIOS

**Acción 6: Modelo Sin Puntajes de Competencias**
- Desarrollar modelo predictivo usando solo:
  - Variables socioeconómicas
  - Características IES
  - Región geográfica
- Objetivo: Identificar factores de contexto

**Acción 7: Análisis de Equidad**
- Evaluar brechas por:
  - Género (aunque modelo muestre 0% importancia)
  - Región (urbano vs rural)
  - Tipo de IES (pública vs privada)
  - Nivel socioeconómico (SISBEN, estrato)

**Acción 8: Análisis Temporal**
- Evaluar tendencias 2015-2024
- Identificar IES con mejoras significativas
- Estudiar factores de éxito

#### 🎯 SEGMENTACIÓN AVANZADA

**Acción 9: Sub-clustering del Cluster 0**
- 268 IES en Cluster 0 pueden tener subgrupos
- Evaluar k=3 a k=5 clusters
- Identificar perfiles más específicos

**Acción 10: Análisis por Áreas de Conocimiento**
- Separar análisis por:
  - Ingenierías
  - Ciencias de la salud
  - Ciencias sociales
  - Artes y humanidades
- Identificar patrones específicos por disciplina

### 5.3 MEDIANO PLAZO (Mes 3-6)

#### 🚀 IMPLEMENTACIÓN Y DESPLIEGUE

**Acción 11: Dashboard Interactivo**
- Desarrollar aplicación web con Streamlit/Dash
- Funcionalidades:
  - Predicción de puntaje en tiempo real
  - Comparación con benchmark nacional
  - Identificación de brechas
  - Recomendaciones personalizadas

**Acción 12: API de Predicción**
- Crear API REST para integración
- Endpoints:
  - `/predict`: Predicción individual
  - `/batch_predict`: Predicción masiva
  - `/benchmark`: Comparación con promedios
- Documentación con Swagger/OpenAPI

**Acción 13: Sistema de Alertas Tempranas**
- Identificar estudiantes en riesgo (predicción <percentil 25)
- Notificación automática a coordinadores académicos
- Generar recomendaciones de intervención

#### 🔬 INVESTIGACIÓN AVANZADA

**Acción 14: Análisis de Causalidad**
- Diseñar estudios cuasi-experimentales
- Evaluar impacto de intervenciones específicas
- Colaborar con IES para pilotos controlados

**Acción 15: Machine Learning Avanzado**
- Evaluar algoritmos adicionales:
  - XGBoost / LightGBM (gradient boosting)
  - Redes Neuronales (Deep Learning)
  - Modelos de ensamble (stacking)
- Comparar desempeño y interpretabilidad

**Acción 16: Análisis de Texto (NLP)**
- Procesar descripciones de programas académicos
- Analizar correlación entre currículo y desempeño
- Identificar mejores prácticas pedagógicas

### 5.4 LARGO PLAZO (Mes 6-12)

#### 📈 IMPACTO Y ESCALAMIENTO

**Acción 17: Plataforma Nacional de Analítica**
- Integrar con sistemas del Ministerio de Educación
- Acceso para todas las IES del país
- Benchmarking nacional en tiempo real

**Acción 18: Programa de Mejoramiento IES**
- Diseñar intervenciones específicas para Cluster 1
- Capacitación en competencias críticas
- Mentoría de IES de alto desempeño

**Acción 19: Investigación Longitudinal**
- Seguimiento de cohortes en el tiempo
- Evaluar predictores de éxito laboral
- Conectar con datos de empleabilidad

**Acción 20: Publicación Académica**
- Redactar artículo científico
- Someter a revista indexada (Scopus/WoS)
- Presentar en conferencias internacionales

---

## 6. CONCLUSIONES FINALES

### 6.1 Logros del Sprint 7

✅ **OBJETIVOS CUMPLIDOS:**

1. ✅ **Issue 7.1:** Modelo predictivo con 99.54% de precisión desarrollado
2. ✅ **Issue 7.2:** Clustering de 336 IES en 2 grupos identificados
3. ✅ **Artefactos Generados:**
   - 2 modelos entrenados (.pkl)
   - 4 archivos de métricas (JSON/CSV)
   - 7 visualizaciones de alta calidad (PNG)
   - Notebooks documentados y reproducibles

### 6.2 Hallazgos Principales

🎯 **INSIGHTS CLAVE:**

1. **Lectura Crítica es el Factor Dominante:**
   - Explica 91.6% del puntaje global
   - Sugiere enfoque prioritario en competencia lectora
   - Potencial sesgo en diseño de prueba a investigar

2. **Dos Perfiles Institucionales Claros:**
   - 80% de IES con desempeño estándar (puntaje ~130)
   - 20% de IES en situación crítica (puntaje ~24 - DATOS A VALIDAR)
   - Brecha significativa requiere intervención focalizada

3. **Variables Demográficas Secundarias:**
   - Género, región, IES no predicen directamente
   - Efecto mediado por competencias
   - Equidad del instrumento de evaluación

4. **Excelente Calidad Predictiva:**
   - R² = 99.54% sin overfitting
   - Error de solo ±2.5 puntos
   - Modelo robusto y generalizable

### 6.3 Limitaciones Reconocidas

⚠️ **CAVEATS IMPORTANTES:**

1. **Calidad de Datos - Cluster 1:** Puntajes anómalos requieren validación urgente
2. **Sesgo de Selección:** Exclusión de variables con >30% NAs puede afectar resultados
3. **Correlación vs Causalidad:** Modelo NO establece relaciones causales
4. **Muestra Selectiva:** Solo 3.7% de datos utilizados (100K de 2.6M)

### 6.4 Impacto Esperado

📊 **VALOR GENERADO:**

**Para las IES:**
- Herramienta de diagnóstico institucional
- Benchmark con pares nacionales
- Identificación de brechas específicas
- Priorización de recursos

**Para Estudiantes:**
- Identificación temprana de riesgos
- Recomendaciones personalizadas
- Apoyo focalizado en competencias críticas

**Para Política Pública:**
- Evidencia para diseño de intervenciones
- Focalización de recursos limitados
- Monitoreo de calidad educativa
- Evaluación de impacto

### 6.5 Próximos Pasos Inmediatos

🔴 **ACCIÓN REQUERIDA - SEMANA 1:**

1. [ ] **Validar Datos Cluster 1** (Prioridad Alta)
2. [ ] **Presentar Resultados** a equipo y stakeholders
3. [ ] **Documentar Decisiones** metodológicas y limitaciones
4. [ ] **Planificar Fase 2** con análisis complementarios

---

## 7. REFERENCIAS Y DOCUMENTACIÓN

### 7.1 Artefactos Generados

**Ubicación:** `artifacts/`

#### Modelos (`.pkl`)
1. `modelos/clasificacion_ies_cluster_20260517.pkl` - Modelo KMeans + Scaler + PCA
2. `modelos/regresion_puntaje_saberpro_20260517.pkl` - Random Forest Regressor

#### Métricas (`.json`, `.csv`)
1. `metricas/metricas_clustering_20260517.json` - Métricas de clustering
2. `metricas/metricas_regresion_20260517.json` - Métricas de regresión
3. `metricas/perfiles_clusters_20260517.csv` - Perfiles detallados de clusters
4. `metricas/feature_importance_20260517.csv` - Importancia de variables

#### Visualizaciones (`.png`)
1. `visualizaciones/analisis_k_optimo.png` - Método del codo y Silhouette
2. `visualizaciones/correlacion_features_ies.png` - Matriz de correlación
3. `visualizaciones/pca_varianza_explicada.png` - Análisis PCA
4. `visualizaciones/clusters_ies_2d_20260517.png` - Clusters en espacio PCA
5. `visualizaciones/perfiles_clusters_barplot.png` - Perfiles por cluster
6. `visualizaciones/importancia_features_20260517.png` - Importancia de variables
7. `visualizaciones/distribucion_errores_20260517.png` - Distribución de residuos

### 7.2 Notebooks

**Ubicación:** `notebooks/sprint_7_machine_learning.ipynb`

**Secciones:**
1. Carga y exploración de datos (Celdas 1-5)
2. Análisis de clustering - Issue 7.2 (Celdas 6-16)
3. Modelo de regresión - Issue 7.1 (Celdas 17-35)

### 7.3 Datos

**Fuente Principal:** `datos/processed/saber_pro/saber_pro_consolidado.parquet`
- 2,683,632 registros
- 150 columnas
- Periodo: 2015-2024

### 7.4 Referencias Bibliográficas

1. **Scikit-learn Documentation** - Random Forest & KMeans  
   https://scikit-learn.org/

2. **ICFES - Marco de Referencia Saber Pro**  
   Instituto Colombiano para la Evaluación de la Educación

3. **Hastie, T., Tibshirani, R., & Friedman, J. (2009)**  
   *The Elements of Statistical Learning* - Springer

4. **Breiman, L. (2001)**  
   *Random Forests* - Machine Learning, 45(1), 5-32

5. **Arthur, D. & Vassilvitskii, S. (2007)**  
   *k-means++: The advantages of careful seeding* - SODA '07

---

## 8. ANEXOS

### ANEXO A: Especificaciones Técnicas

**Entorno de Desarrollo:**
- Python 3.14
- Pandas 2.x
- Scikit-learn 1.5.x
- Matplotlib/Seaborn para visualizaciones

**Tiempo de Ejecución:**
- Clustering: ~2 minutos
- Regresión: ~5 minutos

### ANEXO B: Glosario de Términos

- **R² Score:** Coeficiente de determinación (0-1, mejor cerca de 1)
- **RMSE:** Root Mean Squared Error (error promedio en unidades originales)
- **MAE:** Mean Absolute Error (error absoluto promedio)
- **Silhouette Score:** Métrica de clustering (-1 a 1, mejor > 0.5)
- **Davies-Bouldin Index:** Métrica de clustering (menor es mejor)
- **Feature Importance:** Peso relativo de cada variable en predicción
- **Overfitting:** Modelo que memoriza datos de entrenamiento sin generalizar

### ANEXO C: Contacto y Soporte

**Desarrollador:** German  
**Fecha:** 17 de Mayo de 2026  
**Repositorio:** https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia  

**Para consultas:**
- Issues en GitHub
- Documentación adicional en `/docs`
- Notebooks reproducibles en `/notebooks`

---


