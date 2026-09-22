"""Spider de la Superintendencia Financiera de Colombia (comunicado oficial, clase verdadera).

Verificado el 2026-09-22: la sección de prensa es un menú de
subcategorías (no una lista cronológica directa, como se documentó como
pendiente en criterios_seleccion_fuentes.md). El enlace real de
"Comunicados generales" es `https://www.superfinanciera.gov.co/10102692`
(id numérico, redirige con 301 a una URL con slug). Esa página tiene una
tabla `<td>{Mes Día}</td><td><a href="/{id}">{título}</a></td>` con los
comunicados del año en curso.

Limitación conocida: solo se cubre el año que muestra esta página (2026 al
momento de verificar) — hay un enlace separado de "Histórico de
comunicados de prensa por industria" (id 10892) con otra estructura, no
mapeado en este spider. Ver README de 03_scraping.
"""

import re

import scrapy

from ..extraction import extract_article
from ..items import NoticiaItem
from ..utils import make_id, today_iso

ROW_RE = re.compile(
    r'<td>(?P<mes>\w+) (?P<dia>\d{1,2})</td>\s*'
    r'<td><a href="(?P<url>/\d+)">',
)

MESES_ES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
}


class SuperfinancieraSpider(scrapy.Spider):
    name = "superfinanciera"
    allowed_domains = ["superfinanciera.gov.co"]
    start_urls = ["https://www.superfinanciera.gov.co/10102692"]

    def parse(self, response):
        anio_match = re.search(r"Comunicados de prensa (\d{4})", response.text)
        anio = anio_match.group(1) if anio_match else None
        if anio is None:
            self.logger.warning("No se pudo determinar el año de la página %s; se omite.", response.url)
            return

        for match in ROW_RE.finditer(response.text):
            mes_num = MESES_ES.get(match.group("mes").lower())
            if mes_num is None:
                continue  # texto inesperado en la celda de fecha, se omite en vez de adivinar
            fecha = f"{anio}-{mes_num}-{int(match.group('dia')):02d}"
            yield response.follow(
                match.group("url"),
                callback=self.parse_comunicado,
                cb_kwargs={"fecha_publicacion": fecha},
            )

    def parse_comunicado(self, response, fecha_publicacion: str):
        extracted = extract_article(response.text, response.url)
        if extracted is None:
            return

        item = NoticiaItem()
        item["id"] = make_id(response.url)
        item["titulo"] = extracted.titulo
        item["texto"] = extracted.texto
        item["url"] = response.url
        item["fuente"] = "Superintendencia Financiera de Colombia"
        item["tipo_fuente"] = "comunicado_oficial"
        item["fecha_publicacion"] = fecha_publicacion  # del listado, ver docstring
        item["fecha_recoleccion"] = today_iso()
        item["categoria_tematica"] = "otro"
        item["idioma"] = "es-CO"
        item["fact_checker_url"] = None
        item["fact_checker_rating_original"] = None
        item["label_fuente"] = "verdadera"
        item["es_candidata_dudosa"] = False
        item["pii_revisado"] = False
        yield item
