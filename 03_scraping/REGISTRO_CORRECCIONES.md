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

**Resultado verificado (2026-09-22, tras regenerar ColombiaCheck con
`max_pages=400` y Halcones y Palomas, y correr
`02_corpus/consolidar_corpus.py`)**: confirmado, coincide con lo esperado.

- ColombiaCheck: 721 ítems (725 - 4 podcasts). 0 ocurrencias de
  "Chequeo Múltiple Chequeo Múltiple" sin colapsar (verificado por
  búsqueda directa en `texto`). `fact_checker_rating_original` muestra
  ahora "Verdadero pero..." (9) e "Inchequeable" (1) como categorías
  propias, ya no absorbidas en el valor por defecto sin declarar.
- Halcones y Palomas: 232 ítems, sin pérdida (se confirma que la
  corrección #4 resolvió el falso-positivo de deduplicación).
- Resto de fuentes (Valora Analitik 111, Bloomberg Línea 62,
  Superintendencia Financiera 52, La República 50, Banco de la
  República 18): conteos sin cambio, como se esperaba.
- `corpus_consolidado.parquet`/`.csv`: 1.246 ítems totales, 0 IDs
  duplicados. Por clase: verdadera 536, falsa 410, dudosa 300.

### 5. Widgets de "artículo relacionado" / "boletín" incrustados en el texto (Valora Analitik, Banco de la República)

- **Encontrado**: en una segunda auditoría del `corpus_consolidado.parquet`
  ya regenerado (correcciones 1-4), más profunda que la primera --
  búsqueda de patrones de boilerplate genéricos ("publicidad",
  "suscríbete", "lea también", etc.) sobre las 7 fuentes completas, no
  solo sobre ColombiaCheck/Halcones y Palomas. La entrada anterior de este
  registro (arriba) daba a Valora Analitik y Banco de la República por
  correctos porque su CONTEO no cambiaba tras las correcciones 1-4 -- pero
  el conteo no cambiaba porque el problema nunca fue de conteo, sino de
  contenido, y no se había buscado.
- **Causa raíz**: valoraanalitik.com inyecta widgets de "artículo
  relacionado" y de suscripción al boletín DENTRO del contenedor principal
  del artículo (no en un `<aside>` separado que Trafilatura descartaría
  por defecto), así que quedan pegados en medio del texto extraído, entre
  dos párrafos reales del artículo. A diferencia del widget de La
  República (corrección previa, no registrada aquí por ser de la sesión
  anterior), este no está anclado al inicio del texto, así que la limpieza
  de prefijo existente no lo detectaba.
- **Alcance**: 101 de 111 ítems de Valora Analitik (91 %) tenían al menos
  uno de estos patrones incrustados:
  - "Recibe nuestro boletín en tu correo" (frase fija exacta, sin
    variantes): 97 ítems.
  - "Lea también: `<titular de otro artículo>`": 13 ítems.
  - "Recomendado: `<titular de otro artículo>`": 9 ítems.
  - "Le puede interesar: `<titular de otro artículo>`": 1 ítem en Valora
    Analitik y, además, 1 ítem de Banco de la República (al final del
    texto, resto de un widget de enlaces relacionados que Trafilatura
    recortó dejando solo la etiqueta) -- por eso la corrección se aplica
    de forma genérica a ambas fuentes, no solo a Valora Analitik.
- **Corrección**: se agregó `_strip_related_content_widgets()` en
  `03_scraping/scraper/extraction.py`, aplicada a todas las fuentes
  (verificado contra el corpus completo que ninguno de los 4 patrones
  aparece como texto legítimo en otra fuente distinta a estas dos).
- **Incidente durante la regeneración (nota de transparencia)**: el primer
  intento de regenerar `valoraanalitik.parquet` fue un `scrapy crawl
  valoraanalitik -a max_pages=10` normal, apoyado en HTTPCACHE. Ese intento
  SOBRESCRIBIÓ el Parquet con solo 21 ítems (en vez de 111): el sitio en
  vivo ya mostraba, el mismo día, un conjunto de artículos distinto en sus
  páginas de listado al que había el día de la recolección original, así
  que el redescubrimiento de URLs vía paginación ya no reproducía el mismo
  conjunto -- no es un efecto de la corrección de código. El error se
  detectó de inmediato (conteo cayó de 111 a 21) y se corrigió recuperando
  las 111 filas originales desde `corpus_consolidado.parquet` (que
  todavía no había sido tocado por este intento fallido) antes de que se
  regenerara el consolidado con el dato dañado. No se perdió información:
  el Parquet dañado nunca llegó a propagarse al consolidado. Para evitar
  depender de un redescubrimiento por listado (inestable en el tiempo) se
  escribió en su lugar `03_scraping/reextraer_desde_cache.py`: toma las
  URLs YA registradas en el Parquet existente (el conjunto de ítems no
  cambia) y reextrae `texto`/`titulo` desde el HTML ya cacheado por
  Scrapy, sin re-descubrir nada. Ver docstring de ese script para el
  detalle técnico (incluye la descompresión Brotli del cuerpo cacheado,
  que tampoco se hacía en el primer intento).
- **Resultado verificado**: `valoraanalitik.parquet` y `banrep.parquet`
  mantienen 111 y 18 ítems respectivamente (mismos IDs/URLs que antes), 0
  ocurrencias residuales de los 4 patrones, 0 ítems con texto vacío o
  anormalmente corto tras la limpieza. `texto` modificado en 101/111
  ítems de Valora Analitik y 1/18 de Banco de la República; el resto de
  los campos (id, url, fecha, label_fuente, etc.) no se tocó.

### 6. Tres widgets adicionales específicos de fuente (Halcones y Palomas, Superintendencia Financiera, La República)

- **Encontrado**: misma segunda auditoría que la corrección #5, buscando
  líneas EXACTAS que se repiten idénticas en muchos artículos distintos de
  una misma fuente (señal de artefacto de plantilla, más robusta que
  adivinar frases).
- **Halcones y Palomas -- "Ir a inicio"**: enlace de navegación "volver al
  inicio" pegado al final del contenedor principal. 228/232 ítems (98 %).
  Verificado: en el 100 % de los casos es literalmente lo último del
  texto extraído -- se recorta como sufijo.
- **Superintendencia Financiera -- "Consulte:"**: etiqueta de un widget de
  enlaces relacionados sin el texto del enlace (Trafilatura lo perdió,
  dejando solo la etiqueta, a veces seguida de una lista de otras
  etiquetas igual de vacías). 46/52 ítems (88 %). Verificado: en el 100 %
  de los casos es lo último del texto -- se recorta la etiqueta y todo lo
  que la sigue.
- **La República -- "Síganos y léanos en Google Discover"**: invitación a
  seguir el medio, insertada entre el copete y el cuerpo del artículo
  (mismo patrón que Valora Analitik, corrección #5). 3/50 ítems. Frase
  fija exacta, sin variantes.
- **Verificado en el corpus completo** que cada uno de los tres patrones es
  exclusivo de su fuente (no aparece en ninguna de las otras 6), así que
  la corrección no se aplica a ciegas de forma universal aunque esté en el
  mismo módulo de limpieza.
- **Corrección**: `_strip_source_specific_trailing_widgets()` en
  `03_scraping/scraper/extraction.py`. Regenerado con
  `reextraer_desde_cache.py` (mismo método que la corrección #5, sin
  re-crawl). Resultado: 232/232, 52/52 y 50/50 ítems preservados, texto
  modificado en 228, 46 y 3 respectivamente, 0 ocurrencias residuales, 0
  ítems con texto vacío o anormalmente corto.

### Hallazgo pendiente de decisión: bloques "Acerca de [Empresa]" en Halcones y Palomas

- **Encontrado**: 108 de 232 ítems de Halcones y Palomas (47 %) contienen
  uno o más bloques "Acerca de `<Empresa>`" -- boilerplate corporativo tipo
  "quiénes somos", común en comunicados de prensa (se identificaron más de
  100 empresas distintas: BID Invest, Bancolombia, Grupo Aval, Avianca,
  Nu Holdings, etc.).
- **Diferencia clave con las correcciones 1-6**: verificado contra el HTML
  crudo cacheado (no es una hipótesis) que este bloque **no es un widget
  de plantilla del sitio que se cuela en la extracción** -- es un
  `<p><strong>Acerca de...</strong></p>` dentro del MISMO contenedor
  `<div>` que el resto del artículo, es decir, es contenido que
  halconesypalomas.com publicó como parte del cuerpo del artículo (el
  comunicado de prensa original incluye su propio párrafo de "quiénes
  somos"). No es un error de extracción que corregir con las mismas
  herramientas que las correcciones anteriores.
- **Por qué no se corrigió automáticamente**: en la mayoría de los casos
  revisados el bloque es la cola final del texto (después de él no hay
  nada más), pero se encontraron al menos 2 casos donde el bloque aparece
  A MITAD del artículo y le sigue contenido real y relevante (ej. ítem
  `67b39928b512c19e`: tras "Acerca de IPA Capital Markets" y "Acerca de
  Marcus & Millichap, Inc." continúan párrafos reales sobre la operación
  de Conconcreto en Miami). Un recorte "desde la primera aparición hasta
  el final del texto" habría borrado contenido legítimo en esos casos --
  exactamente el tipo de edición no trazable que este registro existe
  para evitar. No se aplicó ninguna corrección automática sobre este
  hallazgo.
- **Pendiente**: decisión del usuario sobre cómo tratarlo -- opciones
  discutidas: (a) dejarlo como está, documentado como limitación
  metodológica (es contenido genuinamente publicado por la fuente, no un
  bug); (b) un recorte dirigido solo a los casos verificados como cola
  segura (similar a la corrección #5 pero con una lista de nombres de
  empresa conocida, no un patrón genérico); (c) excluir del corpus los
  ítems de Halcones y Palomas de formato "comunicado de prensa".

**Resultado verificado en el consolidado (2026-09-22, tras las
correcciones 5 y 6 y volver a correr `02_corpus/consolidar_corpus.py`)**:
1.246 ítems totales (sin cambio de conteo, como se esperaba -- estas
correcciones solo tocan `texto`, no agregan ni quitan ítems), 0 IDs y 0
URLs duplicadas, 0 ocurrencias residuales de los 7 patrones corregidos
(correcciones 5 y 6) en las 7 fuentes. Por clase: verdadera 536, falsa
410, dudosa 300 -- sin cambio. El hallazgo de "Acerca de [Empresa]" sigue
presente y pendiente de decisión (no se tocó).

### 7. `categoria_tematica` nunca se asignó (fijo en "otro") y `label_fuente` vacío sin explicación visible

- **Encontrado**: el usuario reportó que "en label fuente veo valores
  vacíos y no es clara la etiqueta dada para los registros". Al revisar:
  - `label_fuente` vacío (NaN) es, por diseño, cómo se representa
    "dudosa" (ver `guia_anotacion.md`) -- verificado que coincide 100 %
    con `es_candidata_dudosa=True` y con un `fact_checker_rating_original`
    real en los 300 casos (todos ColombiaCheck). No es una inconsistencia
    de datos, pero en el CSV se ve como una celda en blanco sin ninguna
    columna que diga la clase final en una palabra -- hay que cruzar dos
    columnas para entenderlo. Es un problema real de claridad, aunque no
    de integridad.
  - `categoria_tematica` estaba fijo en `"otro"` en el 100 % de los 1.246
    ítems. Causa raíz: los 7 spiders escribían `item["categoria_tematica"]
    = "otro"` con el comentario "se ajusta en la calibración inicial",
    pero la calibración inicial (ver `criterios_seleccion_fuentes.md`)
    solo registró decisiones de exclusión por relevancia, nunca asignó
    categorías temáticas -- el campo quedó huérfano. Debía decidirse en
    la extracción, no diferirse a una fase que nunca lo iba a llenar.
- **Corrección**:
  - `03_scraping/scraper/categoria_tematica.py` (nuevo): clasificación por
    palabras clave con lista de prioridad (igual criterio que
    `domain_filter.py` -- por reglas, no por LLM, para no introducir una
    dependencia circular con el sistema evaluado en Fase 2). Los 7 spiders
    ahora llaman `clasificar_categoria_tematica(titulo + texto)` en vez de
    fijar `"otro"`.
  - `03_scraping/scraper/utils.py::derivar_clase()` (nuevo): traduce
    `label_fuente` a una columna `clase` explícita (siempre uno de
    `verdadera`\|`falsa`\|`dudosa`, nunca vacía), agregada JUNTO a
    `label_fuente`, no en su reemplazo -- `label_fuente` sigue siendo la
    fuente de verdad para el pipeline (`SchemaValidationPipeline`, etc.).
    Se aplica tanto en `ParquetWriterPipeline` (futuras corridas) como en
    `consolidar_corpus.py` (consolidado).
  - Aplicado retroactivamente a los 1.246 ítems ya recolectados: la
    categoría se deriva solo de `titulo`+`texto`, que ya están correctos,
    así que no hace falta HTML cacheado -- ver
    `03_scraping/reclasificar_categoria_tematica.py` (reclasificación
    pura sobre datos ya extraídos, mismo principio de trazabilidad que
    `reextraer_desde_cache.py`: código + regeneración, no edición manual).
- **Resultado verificado**: `clase` sin ningún valor vacío en 1.246/1.246
  ítems, 100 % consistente con `label_fuente` (0 inconsistencias).
  `categoria_tematica` distribuida así en el consolidado: tributario 321,
  sistema_pensional 283, banca 245, creditos 218, cambiario 123,
  tasas_interes 32, otro 24 (1,9 % -- items genuinamente sin ninguna
  palabra clave de las 6 categorías, no un fallo del clasificador).
  **Limitación reconocida y documentada** en el módulo: es una heurística
  de una sola etiqueta por ítem con orden de prioridad fijo: un artículo
  que toque más de un tema (ej. "impuestos a créditos hipotecarios") se
  clasifica en la categoría de mayor prioridad, no en todas las que
  aplican.

### 8. Resolución del hallazgo "Acerca de [Empresa]" (Halcones y Palomas) -- recorte dirigido, decisión del usuario

- **Decisión del usuario (2026-09-22)**: opción "recorte dirigido a los
  casos verificados como cola segura", no dejar el hallazgo sin tocar ni
  excluir los ítems del corpus.
- **Verificación real de los 108 ítems afectados** (no una heurística
  automática sola -- se intentó primero por longitud del bloque y por
  conteo de líneas, ninguna de las dos separaba con confianza los casos
  seguros de los inseguros: el rango de longitud se superponía por
  completo entre ambos grupos). Se leyó el contenido real de cada uno de
  los 108 cierres de texto (los que no eran obvios a primera vista, con
  contexto extendido de hasta 500 caracteres) y se clasificó cada ítem
  como:
  - **Seguro (86 ítems)**: el bloque "Acerca de `<Empresa>`" es
    genuinamente lo último del artículo -- cifras, historial corporativo,
    "para más información visite...", sin ningún contenido narrativo del
    artículo después.
  - **No seguro (22 ítems, lista completa abajo)**: después del bloque
    "Acerca de..." sigue contenido real y específico del artículo --
    cargos penales, cifras de una negociación en curso, detalles de un
    contrato de concesión, u otro widget distinto ("También puede leer:
    ...", el mismo patrón "artículo relacionado" que Valora Analitik/La
    República, encontrado aquí también de forma incidental). IDs:
    `aea05b92982954f1`, `c28f824a0e36f23d`, `6af049b877c86d2c`,
    `a0a1889d67749e83`, `4c49a7e477a7130e`, `b40751b94698e8d4`,
    `a18efc7f1135144d`, `873bd68fde2850d9`, `7fd73cfca6a19731`,
    `69d1df0ba13ec320`, `92aa8afaa023ddb1`, `44be281e7e5ecdaf`,
    `39be967ee1e59a06`, `52d75b43b6ff9fa7`, `b6817ad6c92a5ff6`,
    `e775a322443902a4`, `55abab4c8de54513`, `c31209ee5da342b1`,
    `c567efbbe64d2405`, `3ffd5a1ced3c916c`, `67b39928b512c19e` (el caso
    Conconcreto que originó el hallazgo), `da91507659fd54bb` (el caso
    Wenia).
- **Corrección**: `03_scraping/tmp/recortar_acerca_de.py` (script de
  aplicación única, no parte del pipeline reutilizable -- la lista de 22
  IDs "no seguros" es producto de lectura manual, no de una regla
  generalizable a futuras corridas). Para ítems con más de un bloque
  "Acerca de" encadenado, el recorte se extiende hacia atrás mientras el
  hueco entre dos headers consecutivos sea ≤1.000 caracteres (el tamaño
  máximo observado de un bloque individual verificado como seguro); un
  hueco mayor detiene la extensión, dejando esa parte anterior intacta por
  la misma razón conservadora que los 22 casos no seguros.
- **Resultado verificado**: 86 ítems modificados, 22 dejados exactamente
  intactos (verificado que el conjunto de IDs con "Acerca de" residual
  tras la corrección incluye a los 22 -- coincide). 0 ítems con texto
  vacío o menor a 200 caracteres tras el recorte. **Nota**: 5 de los 86
  ítems modificados (`b5956c3e3292128c`, `f8909dfa5ebd4fbf`,
  `a6f106392eb9afac`, `433d17d9431a8098`, `a7a13a97e1e9ec53`) tenían DOS
  bloques "Acerca de" con más de 1.000 caracteres de distancia entre
  ellos -- se recortó solo el segundo (verificado seguro), el primero
  queda intacto a mitad de artículo por no haber sido verificado
  individualmente (mismo criterio conservador, no un error). Se
  verificó que los 5 textos resultantes terminan de forma coherente, sin
  truncar contenido a mitad de oración.
  aplican.
