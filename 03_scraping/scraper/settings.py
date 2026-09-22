# Configuración del proyecto Scrapy. Ver 03_scraping/README.md para el
# estado de cumplimiento (robots.txt/ToS) por fuente antes de agregar spiders.

BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Cumplimiento: siempre se respeta robots.txt (regla del proyecto, ver
# criterios_seleccion_fuentes.md). No desactivar esto para "resolver" un
# bloqueo — si un sitio bloquea, la fuente se excluye, no se evade el bloqueo.
ROBOTSTXT_OBEY = True

# User-Agent honesto: se identifica el propósito real, no se hace pasar por
# un navegador para evadir bloqueos de robots.txt/ToS.
USER_AGENT = (
    "TesisDesinformacionFinancieraBot/0.1 "
    "(+contacto: pachonandrey@gmail.com; uso academico, Maestria en IA, "
    "Universidad Sergio Arboleda; respeta robots.txt)"
)

# Throttling conservador: prioridad es no sobrecargar los sitios fuente,
# no la velocidad de recolección.
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
CONCURRENT_REQUESTS_PER_DOMAIN = 1

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0  # cache indefinido en desarrollo, evita re-golpear el sitio en cada corrida de prueba
HTTPCACHE_DIR = "httpcache"

ITEM_PIPELINES = {
    "scraper.pipelines.DomainFilterPipeline": 100,
    "scraper.pipelines.DeduplicationPipeline": 200,
    "scraper.pipelines.SchemaValidationPipeline": 300,
    "scraper.pipelines.ParquetWriterPipeline": 900,
}

LOG_LEVEL = "INFO"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
