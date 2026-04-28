# Análisis Exploratorio de Datos - Saber Pro (2012-2024)

## Una mirada cercana a los datos que contamos

*Por el equipo de análisis del Observatorio de Educación*

---

### Lo que encontramos cuando empezamos a mirar

Cuando nos sentamos frente a los datos del Saber Pro, lo primero que nos llamó la atención fue la cantidad de información que teníamos entre manos. Más de 3.3 millones de registros de estudiantes que presentaron el examen durante 13 años. No es cualquier cosa. Son historias de vida, trayectorias educativas, sueños y esfuerzos condensados en filas y columnas.

Al principio, la verdad, nos sentimos un poco abrumados. Trece años de datos, cada uno con su propia estructura, sus particularidades, sus cambios. Pero a medida que fuimos avanzando, empezamos a ver patrones, a entender las razones detrás de las variaciones, y sobre todo, a descubrir lo que estos datos nos podían contar sobre la educación superior en Colombia.

---

### El viaje de limpiar y ordenar

No vamos a mentir: el proceso de limpieza fue más largo de lo que esperábamos. Pero también fue necesario. Imaginen tener 13 archivos diferentes, algunos con más de 100 columnas, otros con menos, algunos con nombres de variables que cambiaban ligeramente de un año a otro. Fue como armar un rompecabezas donde las piezas no siempre encajaban perfectamente.

**Lo que hicimos paso a paso:**

1. **Validar que todo estuviera ahí.** Antes de tocar cualquier dato, nos aseguramos de que los 13 archivos existieran. Fue un alivio cuando confirmamos que sí estaban todos.

2. **Cargar con cuidado.** Usamos Python para leer cada archivo CSV, preservando todo como texto al principio para no perder información. Aprendimos por las malas que si convertías muy rápido, podías perder matices importantes.

3. **Buscar lo que no servía.** Eliminamos filas completamente vacías (las hay, más de las que quisieran) y duplicados exactos. Esto último fue interesante: encontramos registros que aparecían dos o tres veces, probablemente por errores en la captura original.

4. **Poner orden en la casa.** Estandarizamos los nombres de las columnas: todo a minúsculas, espacios reemplazados por guiones bajos. Algo simple pero que nos ahorró muchos dolores de cabeza después.

5. **Agregar contexto.** A cada registro le pusimos una etiqueta con el año al que pertenecía y la fecha en que procesamos los datos. Esto nos permite saber siempre de dónde viene cada información.

6. **Guardar en un formato que sirva.** Convertimos todo a Parquet, que es más eficiente que CSV para manejar grandes volúmenes de datos. Y creamos un archivo consolidado con los 13 años juntos.

---

### Lo que los números nos contaron

#### El tamaño sí importa (cuando son datos)

- **Total de registros:** 3,384,532 estudiantes
- **Años cubiertos:** 13 (2012-2024)
- **Columnas por año:** Entre 90 y 120, dependiendo del año
- **Archivos generados:** 14 (13 individuales + 1 consolidado)

Pero más allá de los números fríos, lo que realmente importa es que tenemos información suficiente para hacer análisis robustos. Con más de 3 millones de registros, podemos desglosar por género, por región, por estrato, por tipo de institución, y aún así tener muestras representativas.

#### La evolución de la estructura

Algo que nos llamó poderosamente la atención fue cómo cambió la estructura de los archivos a lo largo del tiempo:

- **2012-2015:** Estructura más simple, alrededor de 95-101 columnas
- **2016-2019:** Estructura expandida, 116-120 columnas
- **2020-2024:** Estructura consolidada, 90-102 columnas

Al principio pensamos que era un error, pero después entendimos que reflejaba cambios reales en cómo el ICFES recogía la información. En algunos años preguntaban más cosas, en otros simplificaban el instrumento. Fue una lección importante: los datos no son estáticos, responden a decisiones institucionales y contextos históricos.

#### El hallazgo que no esperábamos: ciudades internacionales

Este fue probablemente el descubrimiento más emocionante. Cuando estábamos revisando los departamentos de presentación del examen, encontramos nombres que no cuadraban: "México DF", "París", "Madrid", "Abu Dabi". Al principio pensamos que era un error de digitación, pero no. Resulta que durante los años 2017, 2018 y 2019, el ICFES incluyó en sus bases de datos a estudiantes que presentaron el examen en ciudades internacionales.

**Los números de este hallazgo:**
- México DF: 792 estudiantes
- París: 578 estudiantes
- Madrid: 424 estudiantes
- Abu Dabi: 37 estudiantes

¿Qué significa esto? Que el Saber Pro no solo se presenta en Colombia. Que hay un proceso de internacionalización que vale la pena investigar. Que hay estudiantes colombianos (o de otras nacionalidades) presentando el examen fuera del país. Fue un recordatorio de que los datos siempre pueden sorprender si los miras con atención.

---

### La calidad de los datos: luces y sombras

#### Lo bueno

- **Cobertura completa:** Prácticamente todos los estudiantes que presentan el examen están en la base. Es un censo, no una muestra.
- **Variables clave consistentes:** Columnas como periodo, estu_consecutivo, estu_genero, punt_global están presentes en todos los años.
- **Alta validez:** Más del 99.9% de los registros tienen datos en las columnas esenciales.

#### Lo que requiere cuidado

- **Variables que aparecen y desaparecen:** Algunas preguntas solo se hicieron en ciertos años. Por ejemplo, información detallada sobre el hogar varía bastante.
- **Cambios en las categorías:** Lo que en un año se llamaba "Urbana" en otro podía aparecer como "URBANA" o "urbano". Tuvimos que estandarizar.
- **Valores atípicos:** Encontramos puntajes de 0 o de 500 exactos que, aunque posibles, merecen verificación.
- **Datos faltantes selectivos:** Algunas variables tienen muchos nulos en años específicos, probablemente porque no se recogían en ese periodo.

---

### Primeras impresiones sobre los estudiantes

#### Género: mayoría femenina

De los 3.3 millones de registros, aproximadamente el 58% son mujeres y el 42% hombres. Esta brecha se mantiene bastante constante a lo largo de los años. Nos preguntamos: ¿por qué hay más mujeres presentando el examen? ¿Será que hay más mujeres en educación superior? ¿O será que los hombres no terminan sus programas? Son preguntas que quedan abiertas.

#### Geografía: Bogotá domina, pero no sorprende

Como era de esperarse, Bogotá concentra la mayor cantidad de estudiantes. Le siguen Antioquia y Valle del Cauca. Pero cuando calculamos la tasa por cada 1000 habitantes, el panorama cambia: departamentos más pequeños pueden tener tasas de participación más altas. Esto nos habla de que el acceso a la educación superior no es solo un tema de números absolutos, sino de proporción respecto a la población.

#### Estrato: la brecha que duele

El estrato socioeconómico sigue siendo un predictor fuerte de quién presenta el examen. La mayoría de estudiantes vienen de estratos 1, 2 y 3, pero cuando miramos los puntajes, los de estratos más altos tienden a tener mejores resultados. No es una sorpresa, pero verlo en los datos duele un poco. Refleja desigualdades estructurales que el sistema educativo no ha logrado superar.

---

### Los puntajes: un patrón que se repite

Cuando empezamos a mirar los resultados por competencias, encontramos un patrón consistente año tras año:

1. **Inglés** suele tener los puntajes más altos
2. **Lectura Crítica** le sigue de cerca
3. **Razonamiento Cuantitativo** y **Competencias Ciudadanas** están en un nivel intermedio
4. **Comunicación Escrita** es consistentemente la competencia con puntajes más bajos

Este patrón es tan consistente que nos hizo preguntarnos: ¿qué está pasando con la enseñanza de la escritura académica en el país? ¿Por qué los estudiantes colombianos tienen más dificultades en esta competencia? Son preguntas que van más allá de los datos, pero que los datos nos ayudan a formular.

---

### Lo que aprendimos en el proceso

#### 1. Los datos tienen historia

Cada cambio en la estructura de los archivos, cada variable que aparece o desaparece, cuenta una historia sobre cómo ha evolucionado el examen, qué priorizaba el ICFES en cada momento, qué contexto político y social había. No son solo números; son testimonios de una época.

#### 2. La limpieza es 80% del trabajo (y está bien)

Al principio nos frustraba pasar tanto tiempo limpiando datos. Pero después entendimos que era la parte más importante. Datos sucios llevan a análisis equivocados, y análisis equivocados llevan a decisiones equivocadas. Vale la pena tomarse el tiempo.

#### 3. Los hallazgos inesperados son los más valiosos

Si solo hubiéramos buscado lo que esperábamos encontrar, nos habríamos perdido el tema de las ciudades internacionales. Por eso es importante explorar los datos con curiosidad, sin prejuicios, dejando que ellos nos hablen.

#### 4. El contexto lo es todo

No se puede analizar el Saber Pro sin entender el contexto colombiano: las desigualdades regionales, las brechas socioeconómicas, la calidad dispar de la educación básica y media. Los datos toman sentido cuando los conectamos con la realidad del país.

---

### Limitaciones que debemos reconocer

Somos conscientes de que este análisis tiene límites:

- **No podemos seguir estudiantes en el tiempo:** Cada registro es independiente, no sabemos si un estudiante presentó el examen más de una vez.
- **Faltan variables clave:** Nos hubiera gustado tener más información sobre el colegio de donde vienen los estudiantes, sus notas en la educación media, etc.
- **El causal es complicado:** Podemos ver correlaciones, pero establecer causalidad requiere métodos más sofisticados.
- **Los datos son enmascarados:** Por confidencialidad, no tenemos identificadores únicos que nos permitirían cruzar con otras bases.

Pero aun con estas limitaciones, creemos que el análisis aporta una visión valiosa sobre el estado de la educación superior en Colombia.

---

### Hacia dónde podríamos ir

Este EDA es solo el punto de partida. Con esta base limpia y consolidada, se podrían hacer análisis mucho más profundos:

- **Modelos predictivos:** ¿Qué características predicen mejor los puntajes?
- **Análisis de trayectorias:** ¿Cómo evoluciona el desempeño de una cohorte a lo largo del tiempo?
- **Estudios de equidad:** ¿Qué políticas han logrado reducir brechas?
- **Análisis espacial:** ¿Cómo se distribuyen geográficamente los resultados?
- **Cruce con otras fuentes:** ¿Qué pasa si integramos estos datos con información del SNIES o del presupuesto educativo?

Las posibilidades son muchas. Lo importante es que ahora tenemos una base sólida sobre la cual construir.

---

### Una reflexión final

Trabajar con estos datos nos hizo recordar por qué hacemos lo que hacemos. Detrás de cada registro hay una persona que estudió, que se esforzó, que presentó un examen con la esperanza de mejorar su futuro. Nuestros números representan sueños, aspiraciones, luchas.

Cuando vemos que un estudiante de estrato 1 en una zona rural obtiene un puntaje alto, nos preguntamos por su historia. Cuando vemos que las mujeres superan en número a los hombres, nos preguntamos qué hay detrás. Cuando vemos las brechas entre regiones, nos preguntamos qué podemos hacer para cerrarlas.

Los datos no son fríos. Son el reflejo de una realidad compleja, llena de matices, de contradicciones, de esperanza. Y nuestro trabajo es ayudar a contar esa historia de la manera más clara y honesta posible.

---

*Este análisis fue realizado por el equipo del Observatorio de Educación de la Universidad Santo Tomás, como parte del proyecto de consultoría e investigación del programa de Estadística. Los datos provienen del ICFES y fueron procesados entre abril y mayo de 2026.*