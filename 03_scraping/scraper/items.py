"""Esquema del ítem recolectado, alineado a 02_corpus/README.md.

Solo incluye los campos que el scraping puede poblar. Los campos de
anotación (label_humano, label_llm_segunda_opinion, label_final, etc.) se
agregan en una fase posterior (etiquetado), no aquí.
"""

import scrapy


class NoticiaItem(scrapy.Item):
    id = scrapy.Field()
    titulo = scrapy.Field()
    texto = scrapy.Field()
    url = scrapy.Field()
    fuente = scrapy.Field()
    # medio_referencia | comunicado_oficial | fact_checker | viral_no_verificado | dataset_publico
    tipo_fuente = scrapy.Field()
    fecha_publicacion = scrapy.Field()
    fecha_recoleccion = scrapy.Field()
    categoria_tematica = scrapy.Field()
    idioma = scrapy.Field()
    fact_checker_url = scrapy.Field()
    fact_checker_rating_original = scrapy.Field()
    # verdadera | falsa | None (None si es candidata a "dudosa")
    label_fuente = scrapy.Field()
    es_candidata_dudosa = scrapy.Field()
    pii_revisado = scrapy.Field()
    similitud_ngramas_max = scrapy.Field()  # poblado por DeduplicationPipeline, no por el spider
