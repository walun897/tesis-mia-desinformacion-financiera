"""Spider de Halcones y Palomas (halconesypalomas.com), medio de referencia.

Verificado el 2026-09-22: robots.txt totalmente abierto (`Disallow:` vacío,
sin bloqueo a bots de IA). WordPress estándar: artículos en
`/{YYYY}/{MM}/{DD}/{slug}/`, con `<meta property="article:published_time">`
en la página de detalle (a diferencia de BanRep, Trafilatura sí la
encuentra sola). Listado paginado en `/category/colombia/page/{N}/`.

Nota de credibilidad (no técnica, para quien revise el corpus): el sitio
también publica secciones no financieras (Cannabis, Gadgets) — se incluye
por recomendación de un experto de la BVC (decisión del usuario,
2026-09-22), pero su alcance editorial es más amplio que Portafolio/La
República. El DomainFilterPipeline es el único filtro real de relevancia
temática aquí.
"""

import re

import scrapy

from ..extraction import extract_article
from ..items import NoticiaItem
from ..utils import make_id, parse_date_safe, today_iso

ARTICLE_URL_RE = re.compile(r"/\d{4}/\d{2}/\d{2}/[\w-]+/$")


class HalconesYPalomasSpider(scrapy.Spider):
    name = "halconesypalomas"
    allowed_domains = ["halconesypalomas.com"]

    def __init__(self, max_pages: int = 10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = int(max_pages)

    async def start(self):
        yield scrapy.Request(
            "https://www.halconesypalomas.com/category/colombia/",
            callback=self.parse_listing,
            cb_kwargs={"page_num": 1},
        )

    def parse_listing(self, response, page_num: int):
        for href in response.css("a::attr(href)").getall():
            if href and ARTICLE_URL_RE.search(href):
                yield response.follow(href, callback=self.parse_article)

        if page_num < self.max_pages:
            yield response.follow(
                f"https://www.halconesypalomas.com/category/colombia/page/{page_num + 1}/",
                callback=self.parse_listing,
                cb_kwargs={"page_num": page_num + 1},
            )

    def parse_article(self, response):
        extracted = extract_article(response.text, response.url)
        if extracted is None:
            return

        # El <title> de la página trae " - Halcones y Palomas" al final
        # (patrón típico de plugin SEO de WordPress); se recorta porque no
        # es parte del titular real.
        titulo = extracted.titulo or ""
        titulo = titulo.removesuffix(" - Halcones y Palomas")

        item = NoticiaItem()
        item["id"] = make_id(response.url)
        item["titulo"] = titulo
        item["texto"] = extracted.texto
        item["url"] = response.url
        item["fuente"] = "Halcones y Palomas"
        item["tipo_fuente"] = "medio_referencia"
        item["fecha_publicacion"] = parse_date_safe(extracted.fecha_publicacion)
        item["fecha_recoleccion"] = today_iso()
        item["categoria_tematica"] = "otro"  # se ajusta en la calibración inicial
        item["idioma"] = "es-CO"
        item["fact_checker_url"] = None
        item["fact_checker_rating_original"] = None
        item["label_fuente"] = "verdadera"
        item["es_candidata_dudosa"] = False
        item["pii_revisado"] = False
        yield item
