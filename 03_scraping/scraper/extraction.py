"""Extracción de texto limpio con Trafilatura.

Centraliza el uso de Trafilatura para que los spiders no dependan de
selectores CSS frágiles por sitio: Trafilatura detecta el contenido
principal del artículo de forma genérica a partir del HTML crudo.
"""

import logging
import re
from dataclasses import dataclass

import trafilatura

logger = logging.getLogger(__name__)

# Verificado en colombiacheck.com el 2026-09-22: algunos sitios tienen
# banners/cintas decorativas (ej. `<p class="Portada-franja-texto">`) que
# repiten una palabra muchas veces para efecto visual (ribbon de
# calificación sobre la imagen destacada) y quedan pegadas al contenedor
# principal, así que Trafilatura las incluye como si fueran texto del
# artículo. Se colapsan repeticiones consecutivas de la misma palabra
# (>=3 veces) en vez de dejarlas — es una limpieza genérica, no específica
# de un sitio.
_REPEATED_WORD_RE = re.compile(r"\b(\w+)\b(?:\s+\1\b){2,}", re.IGNORECASE)


def _collapse_repeated_words(text: str) -> str:
    return _REPEATED_WORD_RE.sub(r"\1", text)


@dataclass
class ExtractedArticle:
    texto: str
    titulo: str | None
    fecha_publicacion: str | None


def extract_article(html: str, url: str) -> ExtractedArticle | None:
    """Extrae texto y metadatos de un artículo a partir de su HTML crudo.

    Devuelve None si Trafilatura no logra extraer contenido (página vacía,
    paywall, estructura no reconocida) — el spider debe descartar el ítem
    en ese caso, no inventar un texto vacío.
    """
    result = trafilatura.extract(
        html,
        url=url,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if not result:
        logger.warning("Trafilatura no pudo extraer contenido de %s", url)
        return None

    import json

    data = json.loads(result)
    texto = _collapse_repeated_words((data.get("text") or "").strip())
    if not texto:
        logger.warning("Trafilatura devolvió texto vacío para %s", url)
        return None

    return ExtractedArticle(
        texto=texto,
        titulo=data.get("title"),
        fecha_publicacion=data.get("date"),
    )
