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
# repiten una palabra o frase corta muchas veces para efecto visual (ribbon
# de calificación sobre la imagen destacada) y quedan pegadas al
# contenedor principal, así que Trafilatura las incluye como si fueran
# texto del artículo. Se colapsan repeticiones consecutivas (>=3 veces) de
# frases de 1 a 4 palabras -- limpieza genérica, no específica de un sitio.
# Corregido 2026-09-22: la versión original solo colapsaba una palabra
# repetida ("Cuestionable Cuestionable..."), pero se encontraron 86 items
# de ColombiaCheck con el mismo problema para una frase de DOS palabras
# ("Chequeo Múltiple Chequeo Múltiple..."), que no coincidía con el patrón
# de una sola palabra.
_REPEATED_PHRASE_PATTERNS = [
    re.compile(r"((?:\S+\s+){" + str(n - 1) + r"}\S+)(?:\s+\1\b){2,}", re.IGNORECASE)
    for n in (4, 3, 2, 1)
]


def _collapse_repeated_words(text: str) -> str:
    # Se prueba de frases largas a cortas: si no se colapsara primero la
    # frase de 4 palabras, el patrón de 1 palabra podría "morder" solo una
    # parte de la repetición y dejar residuos.
    for pattern in _REPEATED_PHRASE_PATTERNS:
        text = pattern.sub(r"\1", text)
    return text


# Verificado en larepublica.co el 2026-09-22 (encontrado en el 100% de los
# 11 ítems ya recolectados, vía la auditoría de calidad del 10%): un
# widget de "seleccionar noticias personalizadas" queda pegado al inicio
# del contenedor principal del artículo. Se recorta si aparece al inicio
# del texto extraído — es un prefijo fijo conocido, no una heurística
# genérica como la de arriba.
_LAREPUBLICA_WIDGET_PREFIX_RE = re.compile(
    r"^MI SELECCIÓN DE NOTICIAS\s*\n\s*Noticias personalizadas,? de acuerdo a sus temas de interés\s*\n",
    re.IGNORECASE,
)


def _strip_known_boilerplate(text: str) -> str:
    return _LAREPUBLICA_WIDGET_PREFIX_RE.sub("", text)


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
    texto = _strip_known_boilerplate(_collapse_repeated_words((data.get("text") or "").strip()))
    if not texto:
        logger.warning("Trafilatura devolvió texto vacío para %s", url)
        return None

    return ExtractedArticle(
        texto=texto,
        titulo=data.get("title"),
        fecha_publicacion=data.get("date"),
    )
