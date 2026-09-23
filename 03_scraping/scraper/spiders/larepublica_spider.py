"""Spider de La República (medio de referencia, clase verdadera).

Verificado el 2026-09-22: HTML servido por el servidor (no requiere JS).
NO se encontró un mecanismo de paginación verificable dentro de una misma
sección (`?page=2` devuelve casi el mismo contenido que `?page=1`), pero sí
hay varias secciones independientes con su propio namespace de URL, cada
una con ~25-65 artículos: `/economia`, `/finanzas` y `/globoeconomia` (se
probó también `/hacienda`, pero sus artículos publican bajo `/economia/`,
no bajo `/hacienda/`, así que no aporta URLs nuevas). La cobertura
histórica adicional se logra por recolección periódica (GitHub Actions,
ya planeado en criterios_seleccion_fuentes.md), no por paginación
profunda en una sola corrida.

label_fuente="verdadera" se asigna por la regla de fuente primaria de
guia_anotacion.md. La condición de esa regla ("reporta datos/cifras
verificables") no se valida automáticamente aquí — queda cubierta por el
control de calidad del 10% ya definido en guia_anotacion.md.
"""

import scrapy
from scrapy.linkextractors import LinkExtractor

from ..categoria_tematica import clasificar_categoria_tematica
from ..extraction import extract_article
from ..items import NoticiaItem
from ..utils import make_id, parse_date_safe, today_iso

ARTICLE_LINK_EXTRACTOR = LinkExtractor(allow=r"/(?:economia|finanzas|globoeconomia)/[\w-]+-\d+$")


class LaRepublicaSpider(scrapy.Spider):
    name = "larepublica"
    allowed_domains = ["larepublica.co"]
    start_urls = [
        "https://www.larepublica.co/economia",
        "https://www.larepublica.co/finanzas",
        "https://www.larepublica.co/globoeconomia",
    ]

    def parse(self, response):
        for link in ARTICLE_LINK_EXTRACTOR.extract_links(response):
            yield response.follow(link.url, callback=self.parse_article)

    def parse_article(self, response):
        extracted = extract_article(response.text, response.url)
        if extracted is None:
            return

        item = NoticiaItem()
        item["id"] = make_id(response.url)
        item["titulo"] = extracted.titulo
        item["texto"] = extracted.texto
        item["url"] = response.url
        item["fuente"] = "La República"
        item["tipo_fuente"] = "medio_referencia"
        item["fecha_publicacion"] = parse_date_safe(extracted.fecha_publicacion)
        item["fecha_recoleccion"] = today_iso()
        item["categoria_tematica"] = clasificar_categoria_tematica(f"{item['titulo']} {item['texto']}")
        item["idioma"] = "es-CO"
        item["fact_checker_url"] = None
        item["fact_checker_rating_original"] = None
        item["label_fuente"] = "verdadera"
        item["es_candidata_dudosa"] = False
        item["pii_revisado"] = False
        yield item
