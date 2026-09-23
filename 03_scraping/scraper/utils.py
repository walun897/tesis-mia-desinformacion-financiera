"""Utilidades compartidas por los spiders."""

import hashlib
from datetime import date, datetime, timezone


def make_id(url: str) -> str:
    """Id determinístico a partir de la URL (mismo artículo -> mismo id entre corridas)."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def parse_date_safe(raw: str | None) -> str | None:
    """Normaliza una fecha a ISO 8601 si es posible; si no, la devuelve tal cual para revisión manual."""
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10]).isoformat()
    except ValueError:
        return raw


def derivar_clase(label_fuente: str | None) -> str:
    """Traduce `label_fuente` (verdadera|falsa|None) a la clase trinaria legible.

    Corregido 2026-09-22 (REGISTRO_CORRECCIONES.md #7): `label_fuente=None`
    representa "dudosa" por diseño (ver guia_anotacion.md), pero en el CSV
    eso se veía como una celda en blanco sin explicación -- un revisor
    humano no podía saber, solo mirando esa columna, que un vacío significa
    "dudosa" y no un dato faltante. Esta función alimenta una columna
    `clase` explícita (siempre uno de los 3 valores, nunca vacía) que se
    agrega junto a `label_fuente`, no en su reemplazo -- `label_fuente`
    sigue siendo la fuente de verdad para el pipeline.
    """
    # `label_fuente is None` cubre el caso en vivo (Scrapy, antes de pasar
    # por pandas). Tras un ciclo de lectura/escritura en Parquet, pandas
    # convierte ese None a float('nan') en una columna object -- `x != x`
    # es la forma estándar de detectar NaN sin depender de pandas/math
    # aquí (NaN es el único valor que no es igual a sí mismo).
    if label_fuente is None or label_fuente != label_fuente:
        return "dudosa"
    return label_fuente
