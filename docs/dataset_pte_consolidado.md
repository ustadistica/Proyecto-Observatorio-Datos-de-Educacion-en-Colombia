# Explicación del Dataset Consolidado PTE (2015-2024)

## Descripcion General

El archivo `pte_consolidado_full.parquet` es el dataset unificado del
**Presupuesto del Sector Educacion (PTE)** de Colombia, con cobertura de
**2015 a 2024** (10 anos completos).

---

## Fuentes de Datos

El dataset se construye a partir de dos fuentes radicalmente distintas:

| Periodo | Fuente | Formato | Frecuencia |
|---|---|---|---|
| 2015-2018 | Ministerio de Educacion Nacional (MEN) | Excel (.xls / .xlsx) | Mensual |
| 2019-2024 | API Socrata (datos.gov.co) | JSON via API | Anual acumulado |

---

## Por que 2015-2018 Tiene Pocas Filas vs 2019-2024

### La diferencia es ESPERADA y CORRECTA

Los Excel del SIIF historico (2015-2018) reportaban el presupuesto de forma
**acumulada mes a mes**. Cada archivo mensual contenia los **mismos rubros
presupuestales**, pero con los montos actualizados hasta esa fecha.

**Ejemplo:** El Excel de enero de 2015 tenia 287 filas (rubros).
El Excel de diciembre de 2015 tambien tenia ~574 filas (los mismos rubros,
pero con montos acumulados al cierre del ano).

Por lo tanto, el archivo final de cada ano contiene **todos los rubros del
ano** ya consolidados, sin duplicar:

| Ano | Archivos Excel Fuente | Filas en Parquet Final |
|---|---|---|
| 2015 | 12 meses (enero a diciembre) | 576 filas |
| 2016 | 12 meses (enero a diciembre) | 611 filas |
| 2017 | 12 meses (enero a diciembre) | 628 filas |
| 2018 | 12 meses (enero a diciembre) | 146 filas |

> **Nota sobre 2018:** Las 146 filas corresponden al dataset final del ano.
> El MEN cambio de sistema (SIIF antiguo a SIIF moderno) en 2019, lo que
> implico una reestructuracion completa del catalogo de rubros.

### Por que 2019-2024 tiene muchas mas filas

La API de Socrata devuelve **todos los registros de movimientos
presupuestales del ano**, incluyendo:
- Vigencia Actual
- Reservas Presupuestales
- Cuentas por Pagar

Esto genera entre 3,269 y 5,167 registros por ano, reflejando el mayor
detalle del SIIF moderno.

---

## Estructura del Dataset

### Metricas Clave

| Indicador | Valor |
|---|---|
| **Total filas** | 25,607 |
| **Total columnas** | 31 |
| **Cobertura temporal** | 2015 - 2024 (10 anos) |
| **Total pagos acumulados** | 2,815.061 Billones COP |

### Filas y Pagos por Ano

| Ano | Filas | Fuente | Pagos (Billones COP) | Apropiacion Vigente | Ejecucion |
|---|---|---|---|---|---|
| 2015 | 576 | Excel MEN | 180.129 | 348.2 | 51.7% |
| 2016 | 611 | Excel MEN | 199.659 | 379.0 | 52.7% |
| 2017 | 628 | Excel MEN | 218.966 | 415.2 | 52.7% |
| 2018 | 146 | Excel MEN | 236.735 | 451.8 | 52.4% |
| 2019 | 3,591 | API Socrata | 254.198 | 498.5 | 51.0% |
| 2020 | 3,451 | API Socrata | 285.589 | 531.6 | 53.7% |
| 2021 | 3,269 | API Socrata | 304.786 | 572.5 | 53.2% |
| 2022 | 3,343 | API Socrata | 331.336 | 594.3 | 55.8% |
| 2023 | 4,825 | API Socrata | 363.335 | 680.6 | 53.4% |
| 2024 | 5,167 | API Socrata | 440.329 | 845.1 | 52.1% |

### Top 5 Entidades por Pagos (2015-2024)

| Entidad | Pagos (Billones COP) |
|---|---|
| MINISTERIO EDUCACION NACIONAL - GESTION GENERAL | 2,693.256 |
| UNIDAD ADMINISTRATIVA ESPECIAL DE ALIMENTACION ESCOLAR | 44.855 |
| UNIVERSIDADES PUBLICAS - UNIVERSIDAD NACIONAL DE COLOMBIA | 17.524 |
| UNIVERSIDADES PUBLICAS - UNIVERSIDAD DE ANTIOQUIA | 7.530 |
| UNIVERSIDADES PUBLICAS - UNIVERSIDAD DEL VALLE | 5.501 |

---

## Normalizacion Cross-Bright de Headers

El pipeline implementa el protocolo **Cross-Bright** para unificar mas de
**200 variantes distintas** de nombres de columna entre el SIIF antiguo
(Excel 2015-2018) y el SIIF moderno (API 2019+).

El resultado es un esquema canonico de **31 columnas** que cubre ambas fuentes.

### Columnas con Cobertura Parcial

| Columna | Origen | Disponible en |
|---|---|---|
| `codigo_cuarto_nivel` | SIIF Antiguo | Solo 2015-2018 |
| `codigo_quinto_nivel` | SIIF Antiguo | Solo 2015-2018 |
| `cdp` | SIIF Antiguo | Solo 2015-2018 |
| `orden_pago` | SIIF Antiguo | Solo 2015-2018 |
| `apropiacionbloqueada` | SIIF Antiguo | Solo 2015-2018 |
| `apropiaciondisponible` | SIIF Antiguo | Solo 2015-2018 |
| `sector` | SIIF Moderno | Solo 2019-2024 |
| `vigencia` | SIIF Moderno | Solo 2019-2024 |
| `situacion` | SIIF Moderno | Solo 2019-2024 |
| `detalle_gasto` | SIIF Moderno | Solo 2019-2024 |
| `nombre_detalle_gasto` | SIIF Moderno | Solo 2019-2024 |
| `recursos_presupuestales` | SIIF Moderno | Solo 2019-2024 |

> Las columnas ausentes en cada periodo quedan como `null` en el consolidado.
> Esto es correcto por diseno: no se pierde ningun dato historico.

---

## Interpretacion del Campo `vigencia`

En el dataset 2019-2024, la columna `vigencia` contiene valores categoricos
que NO son el ano, sino el tipo de vigencia presupuestal:

| Valor | Descripcion |
|---|---|
| `VigenciaActual` | Presupuesto ejecutado en el ano de vigencia |
| `Reservas Presupuestales` | Compromisos del ano anterior pendientes de pago |
| `Cuentas por Pagar` | Obligaciones del ano anterior pendientes de giro |

El ano del presupuesto se identifica por la columna `anio_proceso`.

---

## Consideraciones de Analisis

### Tasa de Ejecucion Estable (~52%)

La tasa de ejecucion presupuestal (pagos / apropiacion vigente) se mantiene
estable alrededor del **52%** durante todo el periodo. Esto puede indicar:
- Grandes transferencias diferidas al sector publico (universidades, ICFES, etc.)
- Presupuesto asignado pero pendiente de giro al cierre del periodo de reporte

### Concentracion de Recursos (Indice Gini ~0.96)

El **96.2%** del presupuesto del sector educacion pasa por el
**Ministerio de Educacion Nacional - Gestion General**.
Las demas entidades (universidades, IETDH, etc.) representan el 3.8% restante.

### Tendencia de Crecimiento Sostenido

Los pagos del sector educacion han crecido de forma constante:
- 2015: 180.1 Billones COP
- 2024: 440.3 Billones COP
- **Incremento total 2015-2024: +145%**

---

## Ubicacion del Dataset

```
datos/
  raw/
    pte/
      2015/  pte_manual_2015.parquet   (Excel agregado)
      2016/  pte_manual_2016.parquet   (Excel agregado)
      2017/  pte_manual_2017.parquet   (Excel agregado)
      2018/  pte_manual_2018.parquet   (Excel agregado)
      2019/  pte_api_2019.parquet      (API Socrata)
      2020/  pte_api_2020.parquet      (API Socrata)
      2021/  pte_api_2021.parquet      (API Socrata)
      2022/  pte_api_2022.parquet      (API Socrata)
      2023/  pte_api_2023.parquet      (API Socrata)
      2024/  pte_api_2024.parquet      (API Socrata)
      *.xls / *.xlsx                   (Fuentes originales Excel MEN)
  processed/
    pte/
      pte_consolidado_full.parquet     <-- DATASET DEFINITIVO
```

---

## Como Ejecutar el Pipeline

```bash
# Desde la raiz del proyecto, con el venv activo:
python run_full_pipeline.py
```

El pipeline:
1. Borra los parquets antiguos en `datos/raw/pte/<ano>/`
2. Reingesta todos los Excel 2015-2018 desde `datos/raw/pte/*.xls(x)`
3. Descarga la API Socrata 2019-2024 y guarda parquets por ano
4. Consolida todos los parquets en `datos/processed/pte/pte_consolidado_full.parquet`

El proceso es **idempotente**: se puede ejecutar multiples veces sin
generar duplicados.
