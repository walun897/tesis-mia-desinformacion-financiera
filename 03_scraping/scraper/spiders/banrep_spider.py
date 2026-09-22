"""Spider del Banco de la República (comunicado oficial, clase verdadera).

Verificado el 2026-09-22: /es/noticias lista comunicados con enlaces
`https://www.banrep.gov.co/es/noticias/{slug}`. No se filtra por dominio
financiero en la URL (BanRep publica de todo, desde cultura hasta política
monetaria) — el DomainFilterPipeline se encarga de descartar lo que no
mencione temas financieros, igual que con las otras fuentes.

IMPORTANTE: las páginas de detalle de BanRep no exponen metadatos de fecha
(sin `<meta>` de fecha ni JSON-LD) — se comprobó que Trafilatura devolvía
la misma fecha para los 23 comunicados de una corrida de prueba, claramente
incorrecta. La fecha real sí está en la tarjeta del listado:
`<p class="date"><time datetime="2025-07-03T12:00:00Z">`. Por eso este
spider toma la fecha del listado, no de la página de detalle.
"""

import re

import scrapy

from ..extraction import extract_article
from ..items import NoticiaItem
from ..utils import make_id, today_iso

# Se parsea tarjeta por tarjeta (split en "views-row") en vez de un único
# regex global sobre toda la página, para evitar patrones con backtracking
# costoso sobre HTML largo.
CARD_LINK_RE = re.compile(r'href="(?P<url>/es/noticias/[\w-]+)"')
CARD_DATE_RE = re.compile(r'<time datetime="(?P<date>\d{4}-\d{2}-\d{2})')


class BanRepSpider(scrapy.Spider):
    name = "banrep"
    allowed_domains = ["banrep.gov.co"]
    start_urls = ["https://www.banrep.gov.co/es/noticias"]

    def parse(self, response):
        for card in response.text.split("views-row")[1:]:
            link_match = CARD_LINK_RE.search(card)
            date_match = CARD_DATE_RE.search(card)
            if not link_match or not date_match:
                continue  # tarjeta sin el formato esperado, se omite en vez de adivinar
            yield response.follow(
                link_match.group("url"),
                callback=self.parse_article,
                cb_kwargs={"fecha_publicacion": date_match.group("date")},
            )

    def parse_article(self, response, fecha_publicacion: str):
        extracted = extract_article(response.text, response.url)
        if extracted is None:
            return

        item = NoticiaItem()
        item["id"] = make_id(response.url)
        item["titulo"] = extracted.titulo
        item["texto"] = extracted.texto
        item["url"] = response.url
        item["fuente"] = "Banco de la República"
        item["tipo_fuente"] = "comunicado_oficial"
        item["fecha_publicacion"] = fecha_publicacion  # del listado, no de la página de detalle (ver docstring)
        item["fecha_recoleccion"] = today_iso()
        item["categoria_tematica"] = "otro"  # se ajusta en la calibración inicial
        item["idioma"] = "es-CO"
        item["fact_checker_url"] = None
        item["fact_checker_rating_original"] = None
        item["label_fuente"] = "verdadera"
        item["es_candidata_dudosa"] = False
        item["pii_revisado"] = False
        yield item
