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
- Comunicados oficiales: Banco de la República (verificado, sin
  restricciones), Superintendencia Financiera de Colombia (sin
  restricciones, pero la sección de prensa es un menú de subcategorías —
  falta mapear la URL exacta), DANE (sin restricciones, spider pendiente
  de construir).
- **Halcones y Palomas** (halconesypalomas.com) — agregada 2026-09-22,
  sin bloqueo en robots.txt. Incluida por recomendación de un experto que
  trabajó en la BVC (decisión del usuario). Nota: también publica
  contenido no financiero (Cannabis, Gadgets) — se apoya en
  `DomainFilterPipeline` para quedarse solo con lo relevante.
- **Valora Analitik** (valoraanalitik.com) — agregada 2026-09-22, sin
  bloqueo en robots.txt (solo bloquea herramientas de descarga masiva).
  Incluida por la misma recomendación. Medio especializado en
  economía/mercados, credibilidad editorial comparable a Portafolio.

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
- AFP Factual Colombia — **pendiente de verificar**: no fue posible
  acceder al dominio (`factcheck.afp.com`) con las herramientas
  disponibles en esta sesión para confirmar robots.txt/ToS. No construir
  el spider hasta verificarlo manualmente.

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
