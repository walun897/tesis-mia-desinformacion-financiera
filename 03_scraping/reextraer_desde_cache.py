"""Reextrae `texto`/`titulo` de ítems ya recolectados usando el HTML ya
cacheado por Scrapy (HTTPCACHE), sin volver a golpear el sitio ni volver a
descubrir URLs desde las páginas de listado.

Por qué existe este script en vez de simplemente re-correr `scrapy crawl`:
al intentar regenerar valoraanalitik.parquet con un `scrapy crawl
valoraanalitik -a max_pages=10` normal (2026-09-22), el sitio en vivo ya
mostraba un conjunto de artículos distinto en sus páginas de listado que el
día de la recolección original -- el re-crawl solo encontró 39 URLs únicas
en vez de las 111 originales, porque la fuente de descubrimiento (listado
paginado) no es estable en el tiempo. Sobrescribir el Parquet con ese
resultado habría cambiado el conteo del corpus sin una causa relacionada
con la corrección de código, exactamente lo que
`03_scraping/REGISTRO_CORRECCIONES.md` existe para evitar.

Este script en cambio: toma las URLs YA registradas en el Parquet existente
(el conjunto de ítems no cambia), busca el HTML de cada una en el HTTPCACHE
ya guardado (mismo caché usado por Scrapy, `HTTPCACHE_DIR` en settings.py),
y vuelve a correr `extract_article` (el código de extracción, ya
corregido) sobre ese HTML. Es la misma idea que "corregir el instrumento y
volver a medir con la lectura original", aplicada sin pasar por el
descubrimiento de URLs.

Uso: python reextraer_desde_cache.py <spider_name> [<spider_name> ...]
"""

import sys
from pathlib import Path

import pandas as pd
from scrapy.downloadermiddlewares.httpcompression import HttpCompressionMiddleware
from scrapy.extensions.httpcache import FilesystemCacheStorage
from scrapy.http import Request
from scrapy.utils.project import get_project_settings
from scrapy.utils.request import RequestFingerprinter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scraper.extraction import extract_article  # noqa: E402
from scraper.spiders.halconesypalomas_spider import TITLE_SUFFIX_RE as _HYP_TITLE_SUFFIX_RE  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "02_corpus" / "raw"

# Corregido 2026-09-22 (REGISTRO_CORRECCIONES.md #9): halconesypalomas_spider.py
# limpia el sufijo " - Halcones y Palomas" del título DESPUÉS de llamar a
# extract_article() (en parse_article(), no en extraction.py) -- este
# script llamaba a extract_article() directamente y usaba su titulo crudo
# sin pasar por esa limpieza, reintroduciendo el sufijo en los 232 ítems de
# Halcones y Palomas la primera vez que se usó (corrección #6). Cualquier
# post-procesamiento de titulo/texto que un spider haga FUERA de
# extraction.py debe registrarse aquí también, o este script lo pierde.
_POST_PROCESAMIENTO_TITULO = {
    "halconesypalomas": lambda t: _HYP_TITLE_SUFFIX_RE.sub("", t or ""),
}


class _FakeCrawler:
    def __init__(self, settings):
        self.request_fingerprinter = RequestFingerprinter()
        self.settings = settings
        self.stats = None


class _FakeSpider:
    def __init__(self, name, settings):
        self.name = name
        self.crawler = _FakeCrawler(settings)


def reextraer_spider(spider_name: str) -> None:
    parquet_path = OUTPUT_DIR / f"{spider_name}.parquet"
    df = pd.read_parquet(parquet_path)

    settings = get_project_settings()
    storage = FilesystemCacheStorage(settings)
    spider = _FakeSpider(spider_name, settings)
    storage.open_spider(spider)
    # El cuerpo cacheado por HTTPCACHE queda tal como llegó por la red --
    # comprimido (br/gzip) si el servidor lo envió así (valoraanalitik.com
    # usa Brotli). HttpCompressionMiddleware es la pieza que normalmente lo
    # descomprime en el pipeline normal de Scrapy; se reutiliza aquí
    # directamente porque `storage.retrieve_response` por sí solo devuelve
    # los bytes crudos aún comprimidos, no HTML.
    comp_mw = HttpCompressionMiddleware()

    no_encontrados = []
    cambios = 0
    nuevos_textos = []
    nuevos_titulos = []

    for _, row in df.iterrows():
        url = row["url"]
        request = Request(url)
        cached = storage.retrieve_response(spider, request)
        if cached is None:
            no_encontrados.append(url)
            nuevos_textos.append(row["texto"])
            nuevos_titulos.append(row["titulo"])
            continue

        html_resp = comp_mw.process_response(request, cached, spider)
        extracted = extract_article(html_resp.text, url)
        if extracted is None:
            # No se pudo reextraer (no debería pasar si ya se extrajo antes
            # con éxito) -- se conserva el dato original, no se inventa.
            no_encontrados.append(url + " (extract_article devolvió None)")
            nuevos_textos.append(row["texto"])
            nuevos_titulos.append(row["titulo"])
            continue

        titulo = extracted.titulo
        post = _POST_PROCESAMIENTO_TITULO.get(spider_name)
        if post is not None:
            titulo = post(titulo)

        if extracted.texto != row["texto"]:
            cambios += 1
        nuevos_textos.append(extracted.texto)
        nuevos_titulos.append(titulo)

    df["texto"] = nuevos_textos
    df["titulo"] = nuevos_titulos

    print(f"[{spider_name}] ítems: {len(df)}, texto modificado en: {cambios}")
    if no_encontrados:
        print(f"[{spider_name}] AVISO: {len(no_encontrados)} URLs sin caché o sin reextracción, se conservó el dato original:")
        for u in no_encontrados:
            print("   -", u)

    df.to_parquet(parquet_path, index=False)

    csv_path = OUTPUT_DIR / f"{spider_name}.csv"
    df_csv = df.copy()
    df_csv["texto"] = df_csv["texto"].str.replace(r"[\r\n]+", " ", regex=True)
    df_csv.to_csv(csv_path, index=False, encoding="utf-8-sig", sep=";")
    print(f"[{spider_name}] escrito {parquet_path} y {csv_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python reextraer_desde_cache.py <spider_name> [<spider_name> ...]")
        sys.exit(1)
    for name in sys.argv[1:]:
        reextraer_spider(name)
