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
from .exclusiones_manuales import EXCLUSIONES_MANUALES

logger = logging.getLogger(__name__)


class ManualCalibrationExclusionPipeline:
    """Descarta ítems ya revisados y rechazados manualmente en la calibración inicial.

    Ver 02_corpus/criterios_seleccion_fuentes.md y exclusiones_manuales.py.
    Solo cubre URLs ya vistas antes — no reemplaza futuras rondas de
    calibración sobre contenido nuevo.
    """

    def process_item(self, item, spider):
        if item.get("url") in EXCLUSIONES_MANUALES:
            raise DropItem(f"Excluido por calibración manual: {item.get('url')}")
        return item

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
    """Calcula similitud_ngramas_max y descarta duplicados exactos (>umbral).

    El índice se siembra con el texto de TODAS las fuentes ya recolectadas
    (no solo la que está corriendo ahora) — si no, la misma noticia
    reportada por dos medios distintos no se detecta como duplicado, ya
    que cada spider escribe su propio Parquet. Se excluye el Parquet del
    propio spider en curso porque se reescribe completo al final de esta
    corrida (ver ParquetWriterPipeline).
    """

    def open_spider(self, spider):
        self.index = DuplicateIndex()
        if not OUTPUT_DIR.exists():
            return
        for path in OUTPUT_DIR.glob("*.parquet"):
            if path.stem == spider.name:
                continue
            try:
                df = pd.read_parquet(path)
            except Exception:
                logger.warning("No se pudo leer %s para deduplicación cruzada, se omite.", path)
                continue
            for item_id, texto in zip(df["id"], df["texto"]):
                self.index.add(item_id, texto)
        logger.info(
            "DeduplicationPipeline: índice sembrado con %d ítems de otras fuentes ya recolectadas.",
            len(self.index._seen),
        )

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

        parquet_path = OUTPUT_DIR / f"{self.spider_name}.parquet"
        df.to_parquet(parquet_path, index=False)

        # CSV en paralelo, solo para inspección humana (abrir en Excel,
        # mostrar avance) -- Parquet sigue siendo el formato de trabajo del
        # pipeline (ver M06-Methodology.tex, justificación de tipos/eficiencia).
        csv_path = OUTPUT_DIR / f"{self.spider_name}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")  # BOM para que Excel detecte UTF-8 solo

        logger.info("Escritos %d ítems en %s y %s", len(df), parquet_path, csv_path)
