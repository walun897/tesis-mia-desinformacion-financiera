# Criterios de selección de fuentes — Corpus de desinformación financiera colombiana

Basado en `Documentacion/v2/anteproyecto/MainMatter/M06-Methodology.tex`
(Universo y muestra, Adquisición). Este documento operacionaliza esos
criterios para el scraping y la curación del corpus.

## Universo

Noticias y contenido financiero/bancario en español colombiano, publicado
en medios digitales colombianos, que cumpla al menos una de:
- Fue verificado por un fact-checker certificado por la IFCN.
- Fue publicado por un medio con credibilidad editorial verificable en la
  sección de economía/finanzas.
- Es contenido viral (redes sociales, cadenas de WhatsApp reportadas por
  fact-checkers) sobre temas financieros, sin verificación institucional.

**Filtro de dominio** (para separar "financiero" de noticias generales):
el texto debe mencionar al menos uno de estos temas — tasas de interés,
créditos/hipotecas, bancos o entidades vigiladas por la SFC, el sistema
pensional, impuestos/reforma tributaria con impacto financiero, el peso
colombiano/TRM, inflación, o el Banco de la República. Se aplica como
lista de palabras clave + revisión manual en la calibración inicial (no
un clasificador aparte, para no introducir una dependencia circular con
el sistema que se está construyendo).

## Muestra objetivo (800-1.000 noticias)

| Clase | Rango | Fuente de la etiqueta |
|---|---|---|
| Verdadera | 300-400 | Medio de referencia o comunicado oficial |
| Falsa | 300-400 | Fact-checker IFCN (etiqueta "falsa"/"engañosa") |
| Dudosa | 200-300 | Fact-checker IFCN ("parcialmente cierta"/"sin evidencia suficiente"/"descontextualizada") o contenido viral sin verificación institucional |

## Fuentes incluidas

**Verificado 2026-09-22 contra robots.txt real (ver `03_scraping/README.md`
para el detalle completo) — esto reemplaza la lista original, que no
había sido verificada:**

**Verdaderas / comunicados oficiales:**
- ~~Portafolio (portafolio.co)~~ — **excluida**: su `robots.txt` bloquea
  explícitamente bots de IA (`anthropic-ai`, `ClaudeBot`, `GPTBot`, etc.).
  Incluirla violaría la regla de este mismo documento de respetar
  robots.txt.
- La República (larepublica.co), sección Economía — sin bloqueo, incluida.
- ~~El Tiempo, sección Economía~~ — **excluida**: bloquea bots de IA y
  además sus términos de servicio prohíben explícitamente el uso del
  contenido para "development of any software, machine learning,
  artificial intelligence (AI), and/or large language models (LLMs)" sin
  autorización previa.
- Comunicados oficiales: Banco de la República (verificado, spider
  construido), Superintendencia Financiera de Colombia (verificado
  2026-09-22, spider construido — tabla de comunicados en
  `superfinanciera.gov.co/10102692`, cubre solo el año en curso, falta el
  histórico). DANE: sin restricciones de robots.txt, pero sus comunicados
  son mayormente **PDF**, no HTML (`M06-Methodology.tex` no lo anticipó) —
  el feed RSS de la categoría de comunicados (`?format=feed&type=rss`)
  existe pero está vacío al momento de verificar. Necesita un pipeline de
  extracción de PDF distinto a Trafilatura — no construido en esta sesión.
- **Halcones y Palomas** (halconesypalomas.com) — agregada 2026-09-22,
  sin bloqueo en robots.txt. Incluida por recomendación de un experto que
  trabajó en la BVC (decisión del usuario). Nota: también publica
  contenido no financiero (Cannabis, Gadgets) — se apoya en
  `DomainFilterPipeline` para quedarse solo con lo relevante.
- **Valora Analitik** (valoraanalitik.com) — agregada 2026-09-22, sin
  bloqueo en robots.txt (solo bloquea herramientas de descarga masiva).
  Incluida por la misma recomendación. Medio especializado en
  economía/mercados, credibilidad editorial comparable a Portafolio.

## Balance de clases: no es automático

El scraper no garantiza el balance 300-400/300-400/200-300 por sí solo —
cada spider recolecta lo que existe y pasa el filtro de dominio, sin
detenerse por cuota. Estado al 2026-09-22 tras la primera recolección real
(no de prueba): 288 ítems totales (verdadera=176, falsa=73, dudosa=39).
"Verdadera" avanza mucho más rápido porque hay 5 fuentes para esa clase
contra 1 sola (ColombiaCheck) para falsa/dudosa, y en ColombiaCheck solo
~14% del contenido es financiero (ver `03_scraping/README.md`).

**Regla operativa mientras no se resuelva de otra forma**: una vez que
"verdadera" se acerque a 300-400, pausar las fuentes de esa clase y
concentrar las corridas en ColombiaCheck (falsa/dudosa) hasta parejar. Si
ColombiaCheck agota su archivo relevante antes de llegar a la cuota, hace
falta un fact-checker adicional (AFP Factual está excluido, ver arriba) —
pendiente sin resolver.

## Verificación de calidad de los datos ya recolectados

No es solo "confiar" en el scraper — esto es lo que ya se verificó
contra los datos reales (no contra el código, contra el resultado):
- **Deduplicación cruzada entre fuentes**: corregido 2026-09-22 — el
  índice de deduplicación originalmente solo comparaba dentro de una
  misma corrida de un spider; se corrigió para sembrarse con todo lo ya
  recolectado de las demás fuentes (ver `pipelines.py`). Sobre los 288
  ítems ya recolectados: 0 duplicados cruzados encontrados.
- **Longitud de texto**: sin textos vacíos ni truncados sospechosamente
  (mínimos entre 296 y 2399 caracteres según la fuente, consistente con
  el tipo de contenido — comunicados cortos vs. artículos largos).
- **Lo que falta verificar y es responsabilidad humana, no del código**:
  el etiquetado automático `label_fuente="verdadera"` para medios de
  referencia asume que lo que publican es cierto, sin verificar cada
  afirmación — por diseño (ver `guia_anotacion.md`). Esto se valida con
  el control de calidad del 10% ya definido en `guia_anotacion.md`.

**Ejecutado 2026-09-22 — control de calidad del 10% (muestra de 25 ítems,
estratificada por fuente, semilla=42)**: revisión manual del usuario sobre
atribución de fuente y calidad de extracción — **0 errores de 25 (0%)**,
muy por debajo del umbral de 5% definido en `guia_anotacion.md`. Valida
que el mecanismo de scraping/extracción funciona correctamente.

**Ejecutado 2026-09-22 — calibración inicial del filtro de dominio**: al
revisar la muestra, el usuario identificó un patrón de falso positivo real
no relacionado con la extracción: coincidencias incidentales de una sola
palabra clave (ej. "impuestos" citado en un insulto dentro de una nota
sobre una protesta política) dejaban pasar contenido sin relación
financiera real. Se probó una regla automática (exigir ≥2 menciones o
coincidencia en el título) pero **se descartó por evidencia empírica**:
sobre los 114 ítems de ColombiaCheck de ese momento, la regla habría
descartado 58 (51%), incluyendo casos legítimos con una sola mención (ej.
"inflación" en una nota sobre pobreza). Se optó por revisión manual en vez
de automatizar un juicio semántico que un regex no puede hacer bien — los
58 candidatos se revisaron uno por uno (ver metodología: fragmento de
contexto de cada coincidencia, no el artículo completo). Resultado: 53
excluidos por ruido temático (mayormente política sin relación
financiera), 5 mantenidos por relación financiera real (estafa de
inversión con IA, salario mínimo, peajes/Sarmiento, administración de
riqueza del Estado, entre otros). `colombiacheck.parquet` pasó de 114 a
61 ítems tras esta calibración. El filtro de dominio automático
(`domain_filter.py`) **no se modificó** — sigue siendo de recall amplio a
propósito; esta calibración fue un paso manual puntual sobre los datos ya
recolectados, no un cambio de regla permanente.

**Impacto**: al perder Portafolio y El Tiempo, la clase "verdadera" se
compensó agregando Halcones y Palomas y Valora Analitik — ya no depende
solo de La República + comunicados oficiales. Las 5 fuentes de "verdadera"
(La República, BanRep, Superfinanciera, Halcones y Palomas, Valora
Analitik) ya están verificadas técnicamente; falta correr los spiders a
escala para confirmar que el volumen combinado alcanza 300-400.

**Falsas / dudosas (fact-checking):**
- ColombiaCheck (colombiacheck.com) — verificado, sin bloqueo a bots de
  IA. Señalado como verificador certificado IFCN en el anteproyecto;
  confirmar vigencia del sello en el momento del scraping, ya que las
  certificaciones IFCN se renuevan periódicamente. Taxonomía de
  calificación real (verificada en `/metodologia`, no la genérica asumida
  antes en este documento): **Verdadero, Verdadero pero, Cuestionable,
  Falso** — ver `guia_anotacion.md` y `03_scraping/scraper/rating_maps.py`.
- ~~AFP Factual Colombia~~ — **excluida** (verificado 2026-09-22): el
  dominio `factcheck.afp.com` bloquea activamente las solicitudes
  automatizadas a nivel de CDN (Akamai devuelve "Access Denied" incluso al
  pedir `/robots.txt` con un User-Agent identificado honestamente). No es
  una política declarada como la de El Tiempo, es un bloqueo técnico
  activo — no se puede scrapear sin evadirlo, y evadirlo violaría el
  mismo principio de no burlar restricciones de acceso.

**Impacto en falsa/dudosa**: con AFP Factual excluida, ColombiaCheck queda
como el único fact-checker scrapeable — mismo riesgo de volumen que ya se
señaló para "verdadera", y **se agrava** tras la calibración manual del
2026-09-22 (arriba): de 114 ítems de ColombiaCheck quedaron 61 reales
(falsa=34, dudosa=26) tras sacar el ruido político. La tasa de relevancia
financiera real de ColombiaCheck es más baja de lo que sugería el
filtro automático sin calibrar. El dataset FakeDeS/IberLEF (abajo) es el
único respaldo si ColombiaCheck solo no alcanza 300-400 falsas + 200-300
dudosas; si tampoco alcanza, hace falta buscar otro fact-checker IFCN
colombiano scrapeable (pendiente, no resuelto en esta sesión).

**Datasets públicos complementarios:**
- FakeDeS / IberLEF 2021 (Corpus de noticias falsas en español, 971 items,
  9 dominios incluyendo Economía) — re-etiquetado según la taxonomía
  trinaria propuesta cuando el ítem pertenezca al dominio financiero.
  No sustituye el corpus propio: es un complemento para robustez, ya que
  cubre español general, no específicamente colombiano ni financiero.
- Google Fact Check Tools API (`claims:search`, endpoint
  `https://factchecktools.googleapis.com/v1alpha1/claims:search`) — para
  traer metadatos ClaimReview de verificaciones adicionales indexadas por
  Google, filtrando por publisher colombiano cuando sea posible.

## Criterios de exclusión

- Contenido no financiero/bancario (aplicar filtro de dominio).
- Noticias financieras de otros países sin relación con el sistema
  financiero colombiano (a menos que sean el objeto directo de una
  desinformación que circula en Colombia).
- Contenido duplicado: similitud de n-gramas > 0.85 respecto a un ítem ya
  incluido (umbral tomado de `M06-Methodology.tex`).
- Contenido que no se pueda atribuir a una fecha de publicación verificable.
- Información personal identificable en el cuerpo del texto (se anonimiza
  o se excluye si no es anonimizable sin perder el sentido de la noticia).

## Ventana temporal

Sin restricción estricta de fecha de origen (las verificaciones de
fact-checkers pueden referirse a desinformación de cualquier momento),
pero se prioriza contenido de los últimos 3-5 años para mantener
relevancia del contexto regulatorio/económico. Se documenta la fecha de
publicación de cada ítem como metadato obligatorio (ver esquema de datos).

## Mecanismos de adquisición

1. **Scraping automatizado** (Scrapy + Trafilatura) — respetando
   `robots.txt` y términos de servicio de cada sitio.
2. **Datasets públicos** — FakeDeS/IberLEF, re-etiquetado selectivo.
3. **Pipeline periódico** — GitHub Actions para recolección incremental
   (definir en la Tarea de scraping, no en este documento).

## Decisiones resueltas

- **Bolsa de Valores de Colombia / DIAN**: no se suman como fuente
  institucional (Tema 3 de `proyecto_investigacion_enfoque_v2.txt`,
  resuelto 2026-09-21). El DANE, ya incluido como fuente oficial, cubre las
  cifras económicas relevantes para el dominio financiero del corpus.

## Pendiente de validar

- Verificar en el momento del scraping que ColombiaCheck y AFP Factual
  Colombia sigan activos como signatarios IFCN (el estado se verificó en
  esta sesión — ver conversación — pero puede cambiar).
