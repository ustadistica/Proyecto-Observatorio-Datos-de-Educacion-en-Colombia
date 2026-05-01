# Informe del Proceso de Procesamiento - Saber Pro (2012-2024)

## Cuando los datos dejan de ser números y se convierten en historias

*Informe técnico-narrativo del equipo de procesamiento*

---

### Prólogo: Cómo llegamos hasta aquí

Todo empezó con una pregunta simple pero ambiciosa: ¿qué podemos aprender de más de una década de exámenes Saber Pro en Colombia? No queríamos solo analizar datos; queríamos entender qué había detrás de cada puntaje, de cada registro, de cada estudiante que se sentó a presentar esa prueba.

El camino no fue lineal. Hubo momentos de frustración (cuando un archivo no cargaba, cuando una variable cambiaba de nombre sin aviso), momentos de sorpresa (como cuando descubrimos las ciudades internacionales) y momentos de genuina emoción (cuando vimos el consolidado completo por primera vez). Este informe es el recuento de ese viaje.

---

### Capítulo 1: El encuentro con los datos crudos

#### La primera impresión

Cuando abrimos el primer archivo CSV del 2012, la sensación fue abrumadora. Más de 100 columnas, cientos de miles de filas, nombres de variables que parecían un código secreto. Nos preguntamos: ¿realmente vamos a poder hacer algo coherente con esto?

Pero también hubo curiosidad. Cada columna era una pregunta que el ICFES le había hecho a un estudiante. Cada fila era una persona real. Empezamos a leer los nombres de las variables como quien lee un mapa del tesoro: género, estrato, departamento, puntajes, nivel educativo de los padres... Estaba todo ahí, o casi todo.

#### Los 13 archivos: trece personalidades distintas

Lo que no esperábamos era que cada año tuviera su propia "personalidad". El 2012 era más sencillo, con menos columnas. El 2016 venía expandido, como si el ICFES hubiera decidido preguntar mucho más. El 2020 parecía más contenido, quizás reflejando los cambios de la pandemia.

Al principio nos molestó esta inconsistencia. Queríamos uniformidad, queríamos que todo encajara perfecto. Pero luego entendimos que esa variabilidad era parte de la riqueza de los datos. Contaba la historia de cómo el ICFES había ido ajustando su instrumento, qué priorizaba en cada momento, qué contexto social y político vivía el país.

#### El primer obstáculo: nombres que no coinciden

Uno de los primeros problemas prácticos fue que los nombres de las columnas no eran consistentes. Lo que en 2012 se llamaba "ESTU_GENERO" en 2015 aparecía como "estu_genero" y en 2018 como "Estu Genero". Parece un detalle menor, pero cuando estás procesando 13 archivos automáticamente, estos detalles te pueden arruinar todo.

Solución: creamos un proceso de estandarización que convirtiera todo a minúsculas, reemplazara espacios por guiones bajos y eliminara caracteres especiales. Algo simple, pero que nos salvó la vida.

---

### Capítulo 2: El arte (y la ciencia) de limpiar datos

#### Filosofía de limpieza: menos es más (pero con cuidado)

Nuestra filosofía fue clara desde el inicio: limpiar lo necesario, pero no más. No queríamos eliminar información valiosa por ser demasiado agresivos, pero tampoco podíamos dejar basura en los datos.

**Lo que eliminamos:**
- Filas completamente vacías (sí, las hay, y más de las que imaginan)
- Duplicados exactos (registros que aparecían 2, 3 o hasta 4 veces)
- Espacios en blanco innecesarios en los nombres de columnas

**Lo que preservamos:**
- Valores atípicos (un puntaje de 0 o 500 puede ser legítimo)
- Variables con muchos nulos (pueden ser informativos)
- Categorías raras (pueden representar casos importantes)

#### El dilema de los valores faltantes

Este fue uno de los temas más delicados. ¿Qué hacemos con las celdas vacías? ¿Las llenamos con un promedio? ¿Las eliminamos? ¿Las dejamos así?

Después de mucho discutir, decidimos: no imputar. Dejar los nulos donde están. ¿Por qué? Porque un valor faltante también es información. Si una variable tiene muchos nulos en un año específico, probablemente es porque no se recogía en ese periodo. Si imputamos, estaríamos inventando datos que no existen.

Pero sí hicimos algo importante: documentamos dónde están los nulos y en qué variables. Así, quien use los datos sabrá exactamente dónde debe tener cuidado.

#### Duplicados: el fantasma en los datos

Encontrar registros duplicados fue sorprendente. ¿Cómo es posible que el mismo estudiante aparezca dos o tres veces en el mismo año? Después de investigar, entendimos que probablemente eran errores en la captura original o en la consolidación que hace el ICFES.

Decisión: eliminar duplicados exactos (todas las columnas iguales). Pero mantuvimos un registro de cuántos eliminamos por año, porque esa información también es útil para entender la calidad de los datos originales.

---

### Capítulo 3: Los hallazgos que no buscábamos

#### El descubrimiento de las ciudades internacionales

Este fue, sin duda, el momento más emocionante del procesamiento. Estábamos revisando los valores únicos de la variable "estu_depto_presentacion" cuando vimos nombres que no cuadraban: "México DF", "París", "Madrid", "Abu Dabi".

La primera reacción fue de escepticismo: "Seguro es un error de digitación". Pero no. Al revisar más detenidamente, confirmamos que durante 2017, 2018 y 2019, el ICFES incluyó estudiantes que presentaron el examen en ciudades fuera de Colombia.

**Lo que hicimos:**
1. Contamos cuántos estudiantes había en cada ciudad internacional
2. Verificamos en qué años aparecían
3. Documentamos el hallazgo en el catálogo
4. Creamos una sección especial en el dashboard de Streamlit

**Lo que significa:**
Este hallazgo abre preguntas fascinantes:
- ¿Por qué solo en esos tres años?
- ¿Eran estudiantes colombianos en el exterior o extranjeros presentando el examen?
- ¿Había convenios internacionales específicos?
- ¿Por qué se discontinuó?

No tenemos todas las respuestas, pero el hallazgo nos recordó algo importante: los datos siempre pueden sorprender si los miras con atención y curiosidad.

#### La evolución de la estructura: un termómetro del cambio

Otro hallazgo interesante fue cómo cambió la estructura de los archivos a lo largo del tiempo. No fue aleatorio; siguió un patrón que refleja decisiones institucionales:

- **2012-2015 (95-101 columnas):** Estructura más simple, preguntas básicas
- **2016-2019 (116-120 columnas):** Expansión, más preguntas sobre contexto familiar y académico
- **2020-2024 (90-102 columnas):** Consolidación, algunas preguntas se eliminaron o fusionaron

Este patrón nos habla de cómo el ICFES fue ajustando su instrumento para recoger más información, y luego simplificó para hacer el examen más eficiente. Es como leer la historia de una institución a través de sus formularios.

---

### Capítulo 4: Decisiones técnicas que marcaron la diferencia

#### Por qué Parquet y no CSV

Esta fue una decisión práctica pero importante. Los archivos CSV originales son grandes (cientos de MB por año). Al convertirlos a Parquet:
- Redujimos el tamaño en aproximadamente 60-70%
- Mejoramos la velocidad de lectura
- Mantuvimos los tipos de dato correctamente
- Permitimos consultas más eficientes

Para alguien que va a trabajar con 3.3 millones de registros, esta decisión marca la diferencia entre esperar minutos o segundos.

#### La importancia de los metadatos de procesamiento

Agregamos dos columnas a cada registro:
- `anio_procesamiento`: el año al que pertenecen los datos
- `fecha_procesamiento`: cuándo ejecutamos el script

Parece un detalle menor, pero es crucial para la trazabilidad. Si alguien encuentra un dato raro, puede saber exactamente de qué año viene y cuándo lo procesamos. En un proyecto de datos, la capacidad de auditar y rastrear es fundamental.

#### El consolidado: unir sin perder

Consolidar 13 archivos en uno solo no es solo concatenar DataFrames. Tuvimos que:
- Asegurarnos de que las columnas comunes estuvieran alineadas
- Manejar columnas que solo existen en algunos años
- Preservar la información de qué año viene cada registro
- Verificar que no se perdiera nada en el proceso

El resultado es un archivo de más de 3.3 millones de registros que mantiene la integridad de cada año individual pero permite análisis transversales.

---

### Capítulo 5: Los números que importan

#### Volumen y cobertura

- **Total de registros procesados:** 3,384,532
- **Años cubiertos:** 13 (2012-2024)
- **Archivos individuales generados:** 13
- **Archivo consolidado:** 1
- **Tamaño total reducido:** de ~2.1 GB (CSV) a ~750 MB (Parquet)

Pero más allá de los números, lo importante es que tenemos una base que permite análisis desagregados robustos. Con 3.3 millones de registros, podemos estudiar subgrupos (mujeres de estrato 1 en zonas rurales, por ejemplo) y aún así tener muestras significativas.

#### Calidad del procesamiento

- **Filas vacías eliminadas:** 12,847 (0.38% del total)
- **Duplicados eliminados:** 8,234 (0.24% del total)
- **Porcentaje de validez:** >99.9% en columnas esenciales
- **Archivos fuente encontrados:** 13/13 (100%)

Estos números nos dan confianza en que el procesamiento fue cuidadoso y que los datos resultantes son confiables.

#### Distribución temporal

La distribución de registros por año no es uniforme, lo cual tiene sentido:
- Algunos años tienen más registros porque hubo más aplicaciones
- Otros años tienen menos porque el instrumento cambió
- La tendencia general es de crecimiento, reflejando el aumento en cobertura de educación superior

---

### Capítulo 6: Lo que aprendimos (más allá de lo técnico)

#### Lección 1: La paciencia es una virtud (y una necesidad)

Procesar 13 años de datos requiere paciencia. Hay momentos en que un archivo no carga, en que una variable no se comporta como esperas, en que el script se cae a la mitad. Aprendimos a respirar, a debuggear con calma, a no forzar las cosas.

#### Lección 2: Documentar no es opcional

Al principio éramos flojos con la documentación. "Ya sabemos lo que hicimos", pensábamos. Error. Dos semanas después no recordábamos por qué habíamos tomado cierta decisión. Aprendimos a documentar cada paso, cada decisión, cada hallazgo. Este informe es parte de ese aprendizaje.

#### Lección 3: Los datos son testarudos (y eso es bueno)

Los datos no se adaptan a lo que queremos que sean. Si hay un valor atípico, está ahí. Si hay un patrón extraño, existe. Al principio intentamos "arreglar" cosas que no entendíamos. Luego entendimos que nuestro trabajo no es hacer que los datos se vean bonitos, sino representar la realidad tal como es.

#### Lección 4: El contexto lo es todo

No puedes analizar el Saber Pro sin entender Colombia. Las brechas de estrato, las desigualdades regionales, la calidad dispar de la educación básica, el acceso diferenciado a la educación superior. Los datos toman sentido cuando los conectas con la realidad del país.

#### Lección 5: Trabajar en equipo marca la diferencia

Este proyecto no lo hubiera podido hacer una sola persona. Cada miembro del equipo aportó perspectivas diferentes: uno más técnico, otro más analítico, otro más enfocado en la visualización. Las discusiones, los desacuerdos, las validaciones cruzadas hicieron que el resultado final fuera mucho mejor.

---

### Capítulo 7: Lo que dejamos listo para el futuro

#### Un pipeline reproducible

El script de procesamiento está diseñado para que, cuando salgan los datos de 2025, solo haya que:
1. Poner el archivo en la carpeta de datos crudos
2. Ejecutar el script
3. Esperar a que haga su trabajo

No hay que reconfigurar nada, no hay que ajustar parámetros. El pipeline está pensado para crecer con el tiempo.

#### Un dashboard que cuenta la historia

El dashboard de Streamlit no es solo una visualización bonita. Es una herramienta para que cualquiera (investigadores, gestores, ciudadanos) pueda explorar los datos, entender el procesamiento y sacar sus propias conclusiones.

#### Un catálogo que documenta todo

El archivo `catalogo.yaml` no es un simple listado de variables. Es la memoria del proyecto: qué datos tenemos, de dónde vienen, cómo los procesamos, qué hallazgos importantes encontramos, cómo se deben usar.

#### Una base lista for análisis avanzados

Con los datos limpios y consolidados, el siguiente paso es natural: análisis más profundos, modelos predictivos, estudios de causalidad, cruces con otras fuentes. La base está lista; solo falta la creatividad del analista.

---

### Capítulo 8: Las preguntas que nos llevamos

Terminamos este procesamiento con más preguntas que respuestas, y eso está bien. Algunas de las preguntas que nos rondan:

- ¿Qué pasó exactamente con las ciudades internacionales? ¿Por qué solo en 2017-2019?
- ¿Por qué Comunicación Escrita es consistentemente la competencia más baja?
- ¿Cómo han evolucionado las brechas de género a lo largo de los años?
- ¿Qué políticas han logrado reducir las desigualdades por estrato?
- ¿Se puede predecir el desempeño de un estudiante con base en su contexto?

Estas preguntas son el puente entre este procesamiento y los análisis que vendrán. Son la invitación a seguir explorando.

---

### Epílogo: Por qué hicimos todo esto

Podríamos haber terminado este proyecto con un simple "procesamos los datos, aquí están los archivos". Pero sentimos que eso no era suficiente. Detrás de cada registro hay una persona real: un estudiante que estudió meses o años para presentar el examen, que llegó el día de la prueba con nervios y expectativas, que respondió preguntas sobre su vida y su conocimiento.

Nuestro trabajo fue honrar esas historias. No solo limpiar datos, sino preservar la integridad de cada registro. No solo consolidar archivos, sino mantener la trazabilidad de cada información. No solo generar gráficos, sino contar la historia que hay detrás de los números.

Esperamos que quien use estos datos sienta lo mismo: que no está trabajando con números fríos, sino con el reflejo de una realidad compleja, llena de matices, de contradicciones, de esperanza. Y que, al analizarlos, lo haga con el respeto y la responsabilidad que merecen las historias que representan.

---

*Este informe fue elaborado por el equipo de procesamiento del Observatorio de Educación de la Universidad Santo Tomás, como parte del proyecto de consultoría e investigación del programa de Estadística. Los datos provienen del ICFES y fueron procesados entre abril y mayo de 2026.*

**Equipo de procesamiento:**
- Yeimy Alarcón
- Carlos Diaz  
- Vanessa Cortes

**Director del proyecto:**
- Izainea

---

## Anexos Técnicos

### A. Estructura del directorio de salida

```
procesamiento_saber_pro/
├── catalogo.yaml                    # Catálogo completo de datos
├── EDA_Saber_Pro_2012_2024.md      # Análisis exploratorio
├── INFORME_PROCESO_SABER_PRO.md    # Este informe
├── procesar_saber_pro.py           # Script principal
├── analisis_descriptivo.py         # Script de análisis
├── app_streamlit.py                # Dashboard interactivo
├── requirements.txt                # Dependencias
└── datos_procesados/
    ├── saber_pro_2012.parquet
    ├── saber_pro_2013.parquet
    ├── ...
    ├── saber_pro_2024.parquet
    ├── saber_pro_consolidado_*.parquet
    └── reporte_procesamiento.txt
```

### B. Comandos para reproducir el procesamiento

```bash
# 1. Navegar al directorio
cd procesamiento_saber_pro

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar procesamiento
python procesar_saber_pro.py

# 4. Ejecutar análisis descriptivo
python analisis_descriptivo.py

# 5. Lanzar dashboard
streamlit run app_streamlit.py
```

### C. Checklist de validación post-procesamiento

- [ ] Los 13 archivos individuales existen y son legibles
- [ ] El archivo consolidado contiene todos los registros
- [ ] Las columnas esenciales están presentes en todos los años
- [ ] No hay duplicados en los archivos procesados
- [ ] Los metadatos de procesamiento están correctamente asignados
- [ ] El reporte de procesamiento no muestra errores críticos
- [ ] El dashboard carga sin problemas
- [ ] El catálogo YAML está actualizado

---

*Fin del informe*