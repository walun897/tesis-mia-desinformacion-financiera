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


# Corregido 2026-09-22 (REGISTRO_CORRECCIONES.md #5), encontrado en una
# segunda auditoría del corpus_consolidado ya regenerado (no en la
# calibración inicial): valoraanalitik.com inyecta widgets de "artículo
# relacionado" / "suscríbete al boletín" DENTRO del contenedor principal
# del artículo (no en un <aside> separado que Trafilatura descartaría), así
# que quedan pegados en medio del texto extraído, entre dos párrafos
# reales. A diferencia del widget de La República, este no está anclado al
# inicio del texto -- puede aparecer en cualquier posición, y a veces más
# de una vez por ítem. Verificado contra el corpus completo: el patrón
# "Recibe nuestro boletín en tu correo" es una frase fija exacta (sin
# variantes) que aparece en 97/111 ítems de Valora Analitik; "Lea también:"
# y "Recomendado:" seguidos de un titular en la misma línea aparecen solo
# en Valora Analitik (13 y 9 ítems); "Le puede interesar:" aparece en
# Valora Analitik (1) y también en Banco de la República (1, al final del
# texto, como resto de un widget de enlaces relacionados que Trafilatura
# recortó dejando solo la etiqueta) -- se aplica de forma genérica, no solo
# a Valora Analitik, porque se verificó que en ningún caso del corpus
# actual es texto legítimo del artículo.
_RELATED_CONTENT_WIDGET_RE = re.compile(
    r"(?:Recib[ei]\w* nuestro bolet[ií]n en tu correo"
    r"|Lea tambi[eé]n:[^\n]*"
    r"|Recomendado:[^\n]*"
    r"|Le puede interesar:[^\n]*)\n?",
    re.IGNORECASE,
)


def _strip_related_content_widgets(text: str) -> str:
    return _RELATED_CONTENT_WIDGET_RE.sub("", text)


# Corregido 2026-09-22 (REGISTRO_CORRECCIONES.md #6), misma segunda
# auditoría que la corrección #5. Tres patrones adicionales, cada uno
# verificado como exclusivo de una sola fuente en el corpus completo (no
# se aplican a ciegas de forma universal, se restringe cada uno a su
# fuente real):
#
# - halconesypalomas.com: "Ir a inicio" es el enlace de navegación "volver
#   al inicio del sitio" que queda pegado al final del contenedor
#   principal. Verificado: en el 100% de los 228/232 ítems donde aparece,
#   es literalmente lo último del texto extraído (nunca en medio) -- se
#   recorta como sufijo.
# - superfinanciera.gov.co: "Consulte:" es la etiqueta de un widget de
#   enlaces relacionados cuyo texto de enlace Trafilatura no capturó,
#   dejando solo la etiqueta. Verificado: en el 100% de los 46/52 ítems
#   donde aparece, es lo último del texto (a veces seguido de una lista de
#   otras etiquetas de enlaces igual de vacías, ej. "- Comunicado de
#   prensa"). Se recorta la etiqueta y todo lo que la sigue.
# - larepublica.co: "Síganos y léanos en Google Discover" es una invitación
#   a seguir el medio en Google Discover, insertada entre el copete y el
#   cuerpo del artículo (patrón igual al de Valora Analitik, corrección
#   #5). Verificado: frase fija exacta, sin variantes, en 3/50 ítems.
_HALCONESYPALOMAS_NAV_SUFFIX_RE = re.compile(r"\s*Ir a inicio\s*\Z")
_SUPERFINANCIERA_CONSULTE_TAIL_RE = re.compile(r"\n?Consulte:.*\Z", re.DOTALL)
_LAREPUBLICA_GOOGLE_DISCOVER_RE = re.compile(
    r"S[ií]ganos y l[eé]anos en Google Discover\n?", re.IGNORECASE
)


def _strip_source_specific_trailing_widgets(text: str) -> str:
    text = _HALCONESYPALOMAS_NAV_SUFFIX_RE.sub("", text)
    text = _SUPERFINANCIERA_CONSULTE_TAIL_RE.sub("", text)
    text = _LAREPUBLICA_GOOGLE_DISCOVER_RE.sub("", text)
    return text


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
    texto = _strip_source_specific_trailing_widgets(
        _strip_related_content_widgets(
            _strip_known_boilerplate(_collapse_repeated_words((data.get("text") or "").strip()))
        )
    )
    if not texto:
        logger.warning("Trafilatura devolvió texto vacío para %s", url)
        return None

    return ExtractedArticle(
        texto=texto,
        titulo=data.get("title"),
        fecha_publicacion=data.get("date"),
    )
