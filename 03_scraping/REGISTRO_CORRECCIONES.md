# Registro de correcciones de calidad de datos

Este archivo documenta cada corrección aplicada al pipeline de extracción
que cambia el contenido de los datos ya recolectados, para que el cambio
en los números del corpus entre corridas tenga una explicación trazable
— sin este registro, un conteo que cambia de una corrida a otra puede
malinterpretarse como manipulación de datos.

**Principio de trazabilidad**: ninguna corrección de este registro edita
un dato a mano. Todas corrigen el **código de extracción** y luego
**regeneran** los datos desde el HTML ya cacheado (o re-scrapeado si hace
falta). Es equivalente a corregir un instrumento de medición y volver a
medir, no a alterar una lectura ya tomada. El historial de git
(`git log -- 03_scraping/scraper/`) es la evidencia complementaria de cada
cambio de código, con diff completo.

## 2026-09-22

### 1. Boilerplate de "Chequeo Múltiple" sin colapsar (ColombiaCheck)

- **Encontrado**: revisando el ítem de texto más largo del corpus
  (109.815 caracteres), se halló la frase "Chequeo Múltiple" repetida 8
  veces al inicio del texto extraído -- una cinta decorativa del sitio,
  no contenido del artículo.
- **Causa raíz**: la limpieza de boilerplate existente
  (`extraction.py::_collapse_repeated_words`) solo colapsaba repeticiones
  de **una** palabra ("Cuestionable Cuestionable..."), no de una frase de
  **dos** palabras ("Chequeo Múltiple Chequeo Múltiple...").
- **Alcance**: 86 de 725 ítems de ColombiaCheck (~12%) tenían este
  patrón sin colapsar.
- **Corrección**: se generalizó la función para colapsar frases de 1 a 4
  palabras repetidas, no solo palabras sueltas. Ver commit de
  `03_scraping/scraper/extraction.py`.

### 2. Calificaciones de ColombiaCheck no contempladas en el mapeo

- **Encontrado**: al revisar `fact_checker_rating_original` completo (no
  solo la muestra de calibración), aparecieron valores reales no
  anticipados: `"Verdadero pero..."` (con puntos suspensivos -- no
  coincidía con la clave mapeada `"verdadero, pero"`), `"Inchequeable"`
  (calificación real de "no se puede verificar", nunca vista antes), y
  `"Podcast"` (4 ítems que son episodios de un pódcast temático, no
  chequeos individuales con veredicto).
- **Alcance**: 9 ítems con "Verdadero pero...", 1 con "Inchequeable", 4
  con "Podcast".
- **Corrección**: se agregó "Inchequeable" al mapeo (→ dudosa, por ser
  semánticamente "no se puede verificar"), se corrigió la clave de
  "Verdadero pero..." para que coincida con el texto real del sitio, y
  los 4 ítems de "Podcast" se excluyen del corpus (no son chequeos
  individuales, no encajan en la taxonomía trinaria). Ver
  `03_scraping/scraper/rating_maps.py`.

### 3. Sufijo del título sin limpiar cuando falta el espacio antes del guion (Halcones y Palomas)

- **Encontrado**: 7 de 232 títulos conservaban el sufijo
  `"- Halcones y Palomas"` sin recortar.
- **Causa raíz**: la limpieza usaba `.removesuffix(" - Halcones y Palomas")`
  (con espacio antes del guion), pero algunos títulos del sitio real
  no tienen ese espacio (ej. `"...(ii)- Halcones y Palomas"`).
- **Alcance**: 7 de 232 ítems.
- **Corrección**: se cambió a una expresión regular que no exige el
  espacio. Ver `03_scraping/scraper/spiders/halconesypalomas_spider.py`.

### 4. Deduplicación cruzada se comparaba contra sí misma vía `corpus_consolidado.parquet`

- **Encontrado**: al intentar regenerar `halconesypalomas.parquet` con las
  correcciones 1-3, la corrida completa se descartó (0 ítems escritos,
  "no produjo ítems válidos") -- el log mostraba cientos de
  `Dropped: Duplicado (similitud=1.00)`.
- **Causa raíz**: `DeduplicationPipeline` siembra su índice leyendo
  *todos* los `.parquet` de `02_corpus/raw/` excepto el del propio
  spider en curso. `corpus_consolidado.parquet` (generado por
  `02_corpus/consolidar_corpus.py`, que junta las 7 fuentes) vive en esa
  misma carpeta y no estaba excluido -- así que cada ítem de
  Halcones y Palomas se comparaba contra su propia copia, ya incluida en
  el consolidado, y se descartaba como duplicado exacto de sí mismo.
- **Alcance**: 100% de los ítems de la corrida de regeneración (232 de
  232) se perdieron en esa corrida específica -- no se perdió el dato
  original (el Parquet previo no se sobrescribe si la corrida no produce
  ítems válidos), pero si no se hubiera detectado, el archivo habría
  quedado vacío en la siguiente corrida exitosa.
- **Corrección**: se excluye explícitamente `corpus_consolidado` (y
  cualquier archivo derivado futuro) de la siembra del índice de
  deduplicación. Ver `03_scraping/scraper/pipelines.py`.

**Resultado esperado tras regenerar**: el total de ColombiaCheck baja en
4 (se excluyen los "Podcast"), el resto de los conteos por fuente no
debería cambiar -- solo cambia el contenido interno de `texto` y
`titulo` en los ítems afectados, y el mapeo de 10 ítems (9 "Verdadero
pero...", 1 "Inchequeable") que antes caían al valor por defecto
(`None, True` -- dudosa) por accidente y ahora quedan mapeados a propósito
al mismo resultado, documentado.
