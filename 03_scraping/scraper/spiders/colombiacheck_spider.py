"""Spider de ColombiaCheck (fact-checker, clases falsa/dudosa).

Estructura verificada contra HTML real el 2026-09-22 (curl directo, no
inferida): cada tarjeta de /chequeos es un
`<div class="Chequeo Chequeo-fila">` con un `<a href="/chequeos/slug">` y
un badge `<p class="Chequeo-picture-bandera-text-{rating}">{Rating}</p>`.
Ver rating_maps.py para el mapeo verificado contra /metodologia.
"""

import re

import scrapy

from ..categoria_tematica import clasificar_categoria_tematica
from ..extraction import extract_article
from ..items import NoticiaItem
from ..rating_maps import es_chequeo_individual, map_colombiacheck_rating
from ..utils import make_id, parse_date_safe, today_iso

CARD_RE = re.compile(
    r'<div class="Chequeo Chequeo-fila">.*?href="(?P<url>/chequeos/[^"]+)".*?'
    r'Chequeo-picture-bandera-text-[a-z-]*">(?P<rating>[^<]+)<',
    re.DOTALL,
)


class ColombiaCheckSpider(scrapy.Spider):
    name = "colombiacheck"
    allowed_domains = ["colombiacheck.com"]

    # max_pages es un argumento de spider (scrapy crawl colombiacheck -a max_pages=20)
    # porque no se verificó un mecanismo para descubrir el total de páginas
    # de forma confiable — se deja explícito en vez de adivinar un límite.
    def __init__(self, max_pages: int = 20, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = int(max_pages)

    async def start(self):
        # Scrapy >=2.13 reemplazó start_requests() (síncrono) por start()
        # (async); ver 03_scraping/README.md.
        for page in range(self.max_pages):
            yield scrapy.Request(
                f"https://colombiacheck.com/chequeos?page={page}",
                callback=self.parse_listing,
            )

    def parse_listing(self, response):
        # Se parsea sobre el HTML crudo con regex (no response.css) porque
        # la estructura verificada anida el link y el badge en el mismo
        # bloque de forma poco selector-friendly; el patrón está anclado al
        # marcado real observado, no es un intento genérico.
        for match in CARD_RE.finditer(response.text):
            yield response.follow(
                match.group("url"),
                callback=self.parse_chequeo,
                cb_kwargs={"rating_raw": match.group("rating").strip()},
            )

    def parse_chequeo(self, response, rating_raw: str):
        if not es_chequeo_individual(rating_raw):
            # ej. "Podcast": no es un chequeo individual con veredicto,
            # no encaja en la taxonomía trinaria -- se descarta, no se
            # fuerza. Ver REGISTRO_CORRECCIONES.md #2.
            return

        extracted = extract_article(response.text, response.url)
        if extracted is None:
            return

        label_fuente, es_candidata_dudosa = map_colombiacheck_rating(rating_raw)

        item = NoticiaItem()
        item["id"] = make_id(response.url)
        item["titulo"] = extracted.titulo
        item["texto"] = extracted.texto
        item["url"] = response.url
        item["fuente"] = "ColombiaCheck"
        item["tipo_fuente"] = "fact_checker"
        item["fecha_publicacion"] = parse_date_safe(extracted.fecha_publicacion)
        item["fecha_recoleccion"] = today_iso()
        item["categoria_tematica"] = clasificar_categoria_tematica(f"{item['titulo']} {item['texto']}")
        item["idioma"] = "es-CO"
        item["fact_checker_url"] = response.url
        item["fact_checker_rating_original"] = rating_raw
        item["label_fuente"] = label_fuente
        item["es_candidata_dudosa"] = es_candidata_dudosa
        item["pii_revisado"] = False
        yield item
