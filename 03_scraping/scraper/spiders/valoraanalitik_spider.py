"""Spider de Valora Analitik (valoraanalitik.com), medio de referencia.

Verificado el 2026-09-22: robots.txt permisivo (solo bloquea herramientas
de descarga masiva tipo HTTrack/wget, no bots de IA). Las URLs de artículo
son slugs planos en la raíz del dominio (`/{slug}/`), indistinguibles de
páginas no-artículo (`/boletin/`, `/avisos-de-ley/`, etc.) por URL sola —
por eso se restringe la extracción a las tarjetas reales del listado
(`<article class="elementor-post ... type-post ...">`, tema Elementor/
Astra de WordPress), no a un regex de URL. La página de detalle sí expone
`<meta property="article:published_time">` correctamente.

Sección usada como punto de entrada: `/noticias-economicas-importantes/`
(paginada en `/page/{N}/`), la categoría explícita de noticias económicas
destacadas del sitio.
"""

import re

import scrapy

from ..extraction import extract_article
from ..items import NoticiaItem
from ..utils import make_id, parse_date_safe, today_iso

# Clase verificada contra el HTML real: solo las tarjetas de artículo real
# (widget "Posts" de Elementor) usan esta clase en el link de la miniatura.
CARD_LINK_RE = re.compile(r'class="elementor-post__thumbnail__link"\s+href="(?P<url>[^"]+)"')


class ValoraAnalitikSpider(scrapy.Spider):
    name = "valoraanalitik"
    allowed_domains = ["valoraanalitik.com"]

    def __init__(self, max_pages: int = 10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = int(max_pages)

    async def start(self):
        yield scrapy.Request(
            "https://www.valoraanalitik.com/noticias-economicas-importantes/",
            callback=self.parse_listing,
            cb_kwargs={"page_num": 1},
        )

    def parse_listing(self, response, page_num: int):
        for match in CARD_LINK_RE.finditer(response.text):
            yield response.follow(match.group("url"), callback=self.parse_article)

        if page_num < self.max_pages:
            yield response.follow(
                f"https://www.valoraanalitik.com/noticias-economicas-importantes/page/{page_num + 1}/",
                callback=self.parse_listing,
                cb_kwargs={"page_num": page_num + 1},
            )

    def parse_article(self, response):
        extracted = extract_article(response.text, response.url)
        if extracted is None:
            return

        item = NoticiaItem()
        item["id"] = make_id(response.url)
        item["titulo"] = extracted.titulo
        item["texto"] = extracted.texto
        item["url"] = response.url
        item["fuente"] = "Valora Analitik"
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
