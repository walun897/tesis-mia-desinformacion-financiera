# 03_scraping — Recolección del corpus

Proyecto Scrapy (`scraper/`) + Trafilatura para extracción de texto.
Complementa `02_corpus/criterios_seleccion_fuentes.md` (qué se recolecta) y
`02_corpus/guia_anotacion.md` (cómo se etiqueta). Todo lo listado aquí como
"verificado" se comprobó contra el HTML/robots.txt real de cada sitio el
2026-09-22 — no está inferido del anteproyecto ni adivinado.

## Estado de cumplimiento por fuente (robots.txt / ToS)

| Fuente | robots.txt | Estado | Spider |
|---|---|---|---|
| ColombiaCheck | Sin bloqueo a bots de IA | ✅ Incluida | `colombiacheck_spider.py` |
| La República | Sin bloqueo a bots de IA | ✅ Incluida | `larepublica_spider.py` |
| Banco de la República | Sin bloqueo a bots de IA | ✅ Incluida | `banrep_spider.py` |
| Halcones y Palomas | Sin bloqueo a bots de IA (`Disallow:` vacío) | ✅ Incluida — agregada 2026-09-22 para compensar la exclusión de Portafolio/El Tiempo, por recomendación de un experto de la BVC (decisión del usuario). Ver nota de credibilidad en `halconesypalomas_spider.py`: también publica contenido no financiero (Cannabis, Gadgets). | `halconesypalomas_spider.py` |
| Valora Analitik | Sin bloqueo a bots de IA (solo bloquea herramientas de descarga masiva) | ✅ Incluida — agregada 2026-09-22, misma razón que arriba. Medio especializado en economía/mercados, credibilidad comparable a Portafolio. | `valoraanalitik_spider.py` |
| Superintendencia Financiera | Sin restricciones (`Allow: /`) | ✅ Incluida | `superfinanciera_spider.py` — cubre el año en curso vía la tabla de `/10102692`; falta el histórico (otro enlace, otra estructura) |
| DANE | Sin bloqueo a bots de IA | ⏳ Pendiente — no es un problema de permisos | Sus comunicados son mayormente **PDF**, no HTML. El feed RSS de la categoría existe (`comunicados-y-boletines?format=feed&type=rss`) pero está vacío al verificar. Necesita extracción de PDF (pipeline distinto a Trafilatura), no construido |
| **Portafolio** | **Bloquea explícitamente `anthropic-ai`, `ClaudeBot`, `GPTBot`, etc.** | ❌ **Excluida** | No se construye — violaría la propia regla del proyecto de respetar robots.txt |
| **El Tiempo** (incluye sección Economía) | **Bloquea bots de IA + ToS prohíbe explícitamente uso para "machine learning, artificial intelligence (AI), and/or large language models"** | ❌ **Excluida** | No se construye |
| AFP Factual | `factcheck.afp.com` bloquea activamente a nivel de CDN (Akamai "Access Denied" incluso para `/robots.txt`) | ❌ **Excluida** — bloqueo técnico activo, no una política declarada; evadirlo violaría el mismo principio de no burlar restricciones de acceso | No construido |

**Impacto en `criterios_seleccion_fuentes.md`**: ese documento listaba
Portafolio y El Tiempo como 2 de las 3 fuentes de referencia para la clase
"verdadera". Al quedar excluidas, la clase "verdadera" depende más de La
República y de comunicados oficiales (BanRep, y pendiente Superfinanciera/
DANE) de lo que el documento original asumía. Revisar si el volumen
alcanza el rango objetivo (300-400) solo con estas fuentes.

## Estructuras verificadas (para quien extienda los spiders)

- **ColombiaCheck**: tarjetas de listado en `/chequeos?page=N` son
  `<div class="Chequeo Chequeo-fila">` con link a `/chequeos/{slug}` y
  badge de calificación en clase `Chequeo-picture-bandera-text-{rating}`.
  Taxonomía real (de `/metodologia`, no asumida): **Verdadero, Verdadero
  pero, Cuestionable, Falso** (categorías antiguas Aproximado/Ligero/
  Inflado fueron consolidadas). "Chequeo Múltiple" es un formato, no una
  calificación — se marca para revisión manual. Ver `rating_maps.py`.
- **La República**: artículos en `/economia/{slug}-{id}`. **No hay
  paginación verificable** (`?page=2` devuelve casi el mismo contenido que
  `?page=1`) — la cobertura histórica depende de correr el spider
  periódicamente (GitHub Actions), no de paginar hacia atrás en una sola
  corrida.
- **Banco de la República**: comunicados en `/es/noticias/{slug}`, sin
  filtro temático en la URL — se apoya en `DomainFilterPipeline` para
  quedarse solo con lo financiero. **La fecha se toma del listado, no de
  la página de detalle**: se verificó corriendo el spider que la página de
  detalle no expone metadatos de fecha, y Trafilatura devolvía la misma
  fecha incorrecta para los 23 comunicados de una corrida de prueba. La
  tarjeta del listado sí tiene `<time datetime="...">` real por ítem.
- **Halcones y Palomas**: WordPress estándar, artículos en
  `/{YYYY}/{MM}/{DD}/{slug}/`, con `article:published_time` correcto en la
  página de detalle (Trafilatura lo toma solo, sin rodeos). Listado
  paginado en `/category/colombia/page/{N}/`. El `<title>` trae un sufijo
  `" - Halcones y Palomas"` que se recorta en el spider.
- **Valora Analitik**: slugs planos en la raíz (`/{slug}/`), indistinguibles
  de páginas no-artículo por URL sola — se restringe a las tarjetas reales
  del listado (`<article class="elementor-post ... type-post ...">`, tema
  Elementor/Astra) en vez de un regex de URL. Punto de entrada:
  `/noticias-economicas-importantes/`, paginado en `/page/{N}/`.
  `article:published_time` correcto en la página de detalle.

## Pipeline (orden de ejecución, ver `scraper/settings.py`)

1. `DomainFilterPipeline` — descarta ítems fuera del dominio financiero
   (misma lista de palabras clave que `criterios_seleccion_fuentes.md`,
   ver `domain_filter.py` — si se edita una, editar la otra).
2. `DeduplicationPipeline` — similitud de n-gramas, umbral 0.85 (`dedup.py`).
3. `SchemaValidationPipeline` — valida campos obligatorios y la
   consistencia `label_fuente`/`es_candidata_dudosa` contra el esquema de
   `02_corpus/README.md`.
4. `ParquetWriterPipeline` — escribe a `02_corpus/raw/{spider}.parquet`
   (excluido de git, ver `.gitignore`).

## Nota de compatibilidad (verificada corriendo el spider, no solo leyendo docs)

Probado en Python 3.14 / Scrapy 2.19.0. Scrapy ≥2.13 reemplazó
`start_requests()` (síncrono) por `async def start()` — el spider de
ColombiaCheck usa `start()` por eso. Si se corre con una versión de Scrapy
anterior a 2.13, hay que revertir a `start_requests()`.

## Cómo correrlo

```bash
cd 03_scraping
pip install -r ../config/requirements.txt
scrapy crawl colombiacheck -a max_pages=20
scrapy crawl larepublica
scrapy crawl banrep
scrapy crawl halconesypalomas -a max_pages=10
scrapy crawl valoraanalitik -a max_pages=10
```

`ROBOTSTXT_OBEY = True` está fijo en `settings.py` — si un sitio bloquea,
Scrapy lo respeta automáticamente. No se debe desactivar esa opción para
"resolver" un bloqueo: la fuente se excluye, no se evade el bloqueo.

## Pendiente

- Verificar manualmente AFP Factual Colombia (el fetch automatizado no
  pudo acceder al dominio) antes de decidir si se incluye.
- Mapear la URL exacta de comunicados de prensa de la Superintendencia
  Financiera (es un menú de subcategorías, no una lista cronológica
  directa) y la sección de comunicados del DANE.
- Confirmar que ColombiaCheck y AFP Factual siguen certificados IFCN al
  momento del scraping a escala (ya señalado en `criterios_seleccion_fuentes.md`).
- Falta el mecanismo de "Datasets públicos" (FakeDeS/IberLEF) y el
  "Pipeline periódico" (GitHub Actions) — no se construyeron en esta
  sesión, quedan fuera del alcance de este primer commit.
- `categoria_tematica` se deja en `"otro"` para todos los ítems — su
  asignación real (tasas_interes/creditos/sistema_pensional/etc.) no
  estaba definida como regla automática en `criterios_seleccion_fuentes.md`;
  se asigna en la etapa de curación, no en el scraper.
