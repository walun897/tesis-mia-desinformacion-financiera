"""Spider de Bloomberg Línea, sección Colombia, medio de referencia.

Verificado el 2026-09-22: robots.txt permisivo (solo bloquea PetalBot y
algunas rutas internas: /test/, /anuncios/, /account-bl/). Existe un feed
RSS específico de la sección Colombia con fecha real por ítem
(`<pubDate>`), mucho más simple y confiable que parsear HTML:
`bloomberglinea.com/arc/outboundfeeds/rss/latinoamerica/colombia.xml`.
El feed trae ~50-100 ítems recientes; no tiene paginación histórica
profunda, así que la cobertura de más largo plazo depende de correr el
spider periódicamente (mismo patrón que La República).
"""

import re

import scrapy

from ..extraction import extract_article
from ..items import NoticiaItem
from ..utils import make_id, today_iso

RSS_URL = "https://www.bloomberglinea.com/arc/outboundfeeds/rss/latinoamerica/colombia.xml"
ITEM_RE = re.compile(
    r"<link>(?P<url>https://www\.bloomberglinea\.com/latinoamerica/colombia/[^<]+)</link>"
    r"(?:(?!<link>).)*?"  # el resto del <item> (guid, dc:creator, description) antes de pubDate; no cruza al siguiente <link>
    r"<pubDate>(?P<pubdate>[^<]+)</pubDate>",
    re.DOTALL,
)


def _parse_rfc822_date(raw: str) -> str | None:
    """Convierte una fecha RFC 822 de RSS ('Tue, 22 Sep 2026 14:56:23 +0000') a ISO 8601."""
    from email.utils import parsedate_to_datetime

    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except (TypeError, ValueError):
        return None


class BloombergLineaSpider(scrapy.Spider):
    name = "bloomberglinea"
    allowed_domains = ["bloomberglinea.com"]

    async def start(self):
        yield scrapy.Request(RSS_URL, callback=self.parse_feed)

    def parse_feed(self, response):
        for m in ITEM_RE.finditer(response.text):
            fecha = _parse_rfc822_date(m.group("pubdate"))
            if fecha is None:
                continue  # sin fecha parseable, se omite en vez de adivinar
            yield response.follow(
                m.group("url"),
                callback=self.parse_article,
                cb_kwargs={"fecha_publicacion": fecha},
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
        item["fuente"] = "Bloomberg Línea"
        item["tipo_fuente"] = "medio_referencia"
        item["fecha_publicacion"] = fecha_publicacion
        item["fecha_recoleccion"] = today_iso()
        item["categoria_tematica"] = "otro"
        item["idioma"] = "es-CO"
        item["fact_checker_url"] = None
        item["fact_checker_rating_original"] = None
        item["label_fuente"] = "verdadera"
        item["es_candidata_dudosa"] = False
        item["pii_revisado"] = False
        yield item
