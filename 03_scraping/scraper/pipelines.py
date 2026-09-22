"""Pipelines de procesamiento: filtro de dominio, deduplicación, validación
de esquema y escritura a Parquet.

Orden de ejecución definido en settings.py (ITEM_PIPELINES).
"""

import logging
from pathlib import Path

import pandas as pd
from scrapy.exceptions import DropItem

from .dedup import DuplicateIndex
from .domain_filter import matches_financial_domain

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = [
    "id",
    "titulo",
    "texto",
    "url",
    "fuente",
    "tipo_fuente",
    # fecha_publicacion es obligatoria: M06-Methodology.tex y
    # criterios_seleccion_fuentes.md excluyen contenido sin fecha
    # verificable, así que un ítem sin fecha se descarta aquí, no se
    # etiqueta con una fecha inventada.
    "fecha_publicacion",
    "fecha_recoleccion",
    "categoria_tematica",
    "idioma",
    "es_candidata_dudosa",
    "pii_revisado",
]

# 02_corpus/raw/ está excluido de git (ver .gitignore) — es la ubicación
# correcta para datos pesados/crudos.
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "02_corpus" / "raw"


class DomainFilterPipeline:
    """Descarta ítems cuyo texto no menciona ningún tema del dominio financiero."""

    def process_item(self, item, spider):
        texto = item.get("texto", "")
        titulo = item.get("titulo", "")
        if not matches_financial_domain(f"{titulo} {texto}"):
            raise DropItem(f"Fuera de dominio financiero: {item.get('url')}")
        return item


class DeduplicationPipeline:
    """Calcula similitud_ngramas_max y descarta duplicados exactos (>umbral)."""

    def open_spider(self, spider):
        self.index = DuplicateIndex()

    def process_item(self, item, spider):
        texto = item.get("texto", "")
        similitud = self.index.max_similarity(texto)
        item["similitud_ngramas_max"] = similitud
        if similitud > self.index.threshold:
            raise DropItem(f"Duplicado (similitud={similitud:.2f}): {item.get('url')}")
        self.index.add(item["id"], texto)
        return item


class SchemaValidationPipeline:
    """Verifica que el ítem tenga los campos obligatorios del esquema de 02_corpus/README.md."""

    def process_item(self, item, spider):
        faltantes = [campo for campo in REQUIRED_FIELDS if item.get(campo) in (None, "")]
        if faltantes:
            raise DropItem(f"Campos obligatorios faltantes {faltantes}: {item.get('url')}")

        # label_fuente es nullable a propósito (candidata a "dudosa"), pero
        # su consistencia con es_candidata_dudosa sí es obligatoria — ver
        # guia_anotacion.md.
        label_fuente = item.get("label_fuente")
        es_candidata_dudosa = item.get("es_candidata_dudosa")
        if label_fuente in ("verdadera", "falsa") and es_candidata_dudosa:
            raise DropItem(f"Inconsistente: label_fuente={label_fuente} pero es_candidata_dudosa=True: {item.get('url')}")
        if label_fuente is None and not es_candidata_dudosa:
            raise DropItem(f"Inconsistente: label_fuente=None pero es_candidata_dudosa=False: {item.get('url')}")
        if label_fuente not in ("verdadera", "falsa", None):
            raise DropItem(f"label_fuente inválido: {label_fuente!r}: {item.get('url')}")

        return item


class ParquetWriterPipeline:
    """Acumula los ítems válidos de la corrida y los escribe a Parquet al cerrar el spider."""

    def open_spider(self, spider):
        self.items: list[dict] = []
        self.spider_name = spider.name

    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item

    def close_spider(self, spider):
        if not self.items:
            logger.warning("Spider %s no produjo ítems válidos, no se escribe Parquet.", self.spider_name)
            return
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(self.items)
        output_path = OUTPUT_DIR / f"{self.spider_name}.parquet"
        df.to_parquet(output_path, index=False)
        logger.info("Escritos %d ítems en %s", len(df), output_path)
