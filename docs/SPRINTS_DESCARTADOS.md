# Issues Descartados y Replanteados - Observatorio Educación Colombia

**Fecha:** 17 de Mayo, 2026  
**Autor:** German Chamorro  
**Revisión:** Análisis técnico de viabilidad

---

## ❌ Issues DESCARTADOS

### Issue 6.2: Cruce PTE × Saber Pro por Entidad

**Estado:** ❌ **DESCARTADO**

**Razón técnica:**
El Presupuesto Territorial de Educación (PTE) tiene una **limitación crítica de transparencia**:

- **2015-2018:** Datos desglosados por universidad individual (68 registros IES)
- **2019-2024:** Solo "MINISTERIO EDUCACIÓN NACIONAL - GESTIÓN GENERAL" agregado (sin desglose por IES)

**Implicaciones:**
- ❌ No se puede cruzar PTE con Saber Pro a nivel de IES para periodo 2019-2024
- ❌ No se puede calcular ROI educativo por institución con datos actuales
- ❌ Análisis de eficiencia presupuestal limitado a periodo 2015-2018

**Evidencia:**
```yaml
# datos/catalogo.yaml - Líneas 27-41
limitaciones: |
  LIMITACIÓN CRÍTICA: Las 47 universidades públicas (UEJ) solo aparecen en los
  datos 2015-2018 (fuente: men_excel). A partir de 2019, los formatos SIIF y DNP
  Cuadro 7 solo reportan al "MINISTERIO EDUCACION NACIONAL - GESTION GENERAL"
  como entidad agregada. NO hay trazabilidad por universidad, programa o departamento
  en 2019-2024.
```

**Recomendación:**
- ✅ Mantener análisis histórico 2015-2018 en `reporte_eficiencia_universidades.html`
- ✅ Documentar esta limitación como hallazgo en Sprint 8.1 (ETL datos gubernamentales)
- ✅ Proponer mejora metodológica en paper académico

---

### Issue 7.4: Implementar API de Predicciones

**Estado:** ❌ **DESCARTADO**

**Razón académica:**
- ❌ No aporta valor académico/investigativo al proyecto de grado
- ❌ Es un componente de ingeniería de software, no de ciencia de datos
- ❌ Requiere infraestructura y mantenimiento fuera del alcance del proyecto

**Enfoque del proyecto:**
El proyecto es un **observatorio académico** enfocado en:
- ✅ Análisis descriptivo y exploratorio
- ✅ Modelado predictivo y evaluación
- ✅ Documentación metodológica reproducible
- ✅ Generación de insights para políticas públicas

**Alternativa:**
- ✅ Crear notebooks Jupyter interactivos con predicciones
- ✅ Documentar uso de modelos en `artifacts/reportes/`
- ✅ Proporcionar scripts `.py` para replicabilidad

---

## 🔄 Issues REPLANTEADOS

### Issue 7.2: Clustering IES por Desempeño

**Estado Original:**
> "Clasificación automática de instituciones por desempeño"

**Nuevo enfoque:**
> **"Clustering de IES según desempeño Saber Pro y métricas SNIES (graduación, acreditación)"**

**Cambios metodológicos:**
1. **Features adicionales:**
   - Puntajes Saber Pro (por área de conocimiento)
   - Tasa de graduación SNIES
   - Número de graduados
   - Acreditación institucional (si/no)
   - Proporción en P75+ (percentil 75 superior)

2. **Cruces de datos:**
   - Base: `reporte_cruce_snies_saberpro.html` (ya generado)
   - Enriquecer con: matriculados, programas activos, cobertura

3. **Salidas esperadas:**
   - Clusters de IES (e.g., "Alto desempeño", "Medio", "Bajo")
   - Perfiles característicos por cluster
   - Visualización 2D (PCA/t-SNE)
   - Métricas: Silhouette, Davies-Bouldin

**Archivos relacionados:**
- `artifacts/modelos/clasificacion_ies_cluster_YYYYMMDD.pkl`
- `artifacts/metricas/metricas_clustering_YYYYMMDD.json`
- `artifacts/visualizaciones/clusters_ies_2d_YYYYMMDD.png`

---

### Issue 7.3: Predicción de Tasa de Graduación

**Estado:** ⚠️ **VIABILIDAD MEDIA** (requiere datos adicionales)

**Desafío:**
- Necesitas datos longitudinales de cohortes (matriculados → graduados)
- SNIES tiene datos anuales, pero no necesariamente rastreables por cohorte

**Recomendación:**
- ⚠️ Evaluar si SNIES consolidado permite construir cohortes sintéticas
- ⚠️ Alternativamente: predecir "número de graduados año t+1" dado matriculados año t
- ⚠️ Si no es factible, **descartar** y enfocarse en 7.1 y 7.2

---

## ✅ Issues PRIORITARIOS (Mantener)

### Sprint 6

| Issue | Estado | Datos Disponibles |
|-------|--------|-------------------|
| 6.1 | ✅ **COMPLETO** | `reporte_cruce_snies_saberpro.html` |
| 6.3 | ✅ **FACTIBLE** | `snies_matriculados_limpio_consolidado.parquet` |
| 6.4 | ✅ **FACTIBLE** | Cruce matriculados × presentaciones (similar a 6.1) |

### Sprint 7

| Issue | Prioridad | Viabilidad |
|-------|-----------|------------|
| 7.1 | 🔥 **ALTA** | Datos robustos disponibles |
| 7.2 | 🔥 **ALTA** | Replante

ado, muy factible |
| 7.3 | ⚠️ **MEDIA** | Depende de estructura de cohortes |

### Sprint 8

| Issue | Enfoque | Hallazgo clave |
|-------|---------|----------------|
| 8.1 | ETL datos gubernamentales | **Limitación PTE** es caso de estudio |
| 8.2 | Metodología reproducible | Documentar proceso aplicado |
| 8.3 | Marco conceptual | Síntesis de hallazgos |

---

## 📊 Impacto en el Proyecto

### Archivos afectados:
- ❌ **Eliminar:** Ninguno (los descartados no se implementaron)
- ✅ **Mantener:** Todos los reportes HTML actuales
- 🔄 **Replantear:** Scripts de ML en Sprint 7

### Documentación actualizada:
- ✅ `artifacts/README.md` - Estructura para modelos ML
- ✅ `artifacts/metricas/ejemplo_metricas_*.json` - Plantillas
- ✅ Este documento (`SPRINTS_DESCARTADOS.md`)

### Próximos pasos:
1. Implementar Issue 7.1 (Regresión Saber Pro)
2. Implementar Issue 7.2 (Clustering IES - replanteado)
3. Evaluar viabilidad de 7.3 (decisión pendiente)
4. Documentar limitación PTE en paper (Sprint 8.1)

---

## Referencias

- Catálogo de datos: `datos/catalogo.yaml`
- Reportes generados: `docs/reporte_*.html`
- Código ETL: `src/ingesta/`, `src/transformacion/`
- Issue original Sprint 6.2: Análisis de eficiencia presupuestal por IES
- Issue original Sprint 7.4: API REST para predicciones

---

**Conclusión:**  
Los issues descartados se deben a **limitaciones técnicas insalvables** (PTE) o **fuera de alcance académico** (API). El proyecto mantiene su valor científico y todos los análisis factibles siguen en pie.
