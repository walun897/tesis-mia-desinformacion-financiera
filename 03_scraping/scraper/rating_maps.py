"""Mapeo de calificaciones de fact-checkers a la taxonomía trinaria del proyecto.

Verificado contra el HTML real de colombiacheck.com el 2026-09-22 (no
inventado): la página /metodologia describe la escala vigente como
Verdadero / Verdadero, pero / Cuestionable / Falso (categorías previas
Aproximado, Ligero e Inflado fueron consolidadas). El badge de calificación
en las tarjetas de /chequeos usa las clases CSS
`Chequeo-picture-bandera-text-{verdadero,cuestionable,falso,multiple}`.

Corregido 2026-09-22 (ver 03_scraping/REGISTRO_CORRECCIONES.md #2): al
revisar el `fact_checker_rating_original` real de los 725 ítems ya
recolectados (no solo la muestra de calibración), aparecieron valores no
contemplados en la primera versión de este mapa:
- "Verdadero pero..." (con puntos suspensivos) en vez de "Verdadero, pero"
  -- la clave anterior nunca coincidía con el texto real del sitio.
- "Inchequeable" -- calificación real ("no se puede verificar"), ausente
  del mapa original.
- "Podcast" -- no es una calificación de verdad, son episodios de un
  pódcast temático (4 ítems), se excluyen del corpus (ver spider).
- "Chequeo Múltiple" sigue sin mapear a propósito: no es una calificación
  de verdad sino un formato de artículo con varias afirmaciones
  verificadas por separado -- no mapea limpio a la taxonomía trinaria de
  un solo ítem, se marca para revisión manual en vez de asumir un valor.
"""

# (label_fuente, es_candidata_dudosa) — ver guia_anotacion.md para la
# justificación de cada categoría.
COLOMBIACHECK_RATING_MAP: dict[str, tuple[str | None, bool]] = {
    "verdadero": ("verdadera", False),
    "verdadero pero...": (None, True),  # mezcla elementos verdaderos y falsos -> dudosa
    "cuestionable": (None, True),
    "falso": ("falsa", False),
    "inchequeable": (None, True),  # "no se puede verificar" -> dudosa
}

# Calificaciones que indican que el ítem NO es un chequeo individual con
# veredicto (formato de artículo distinto) -- se excluyen del corpus en
# vez de forzarlas a la taxonomía trinaria.
NO_ES_CHEQUEO_INDIVIDUAL = {"podcast"}

# Se marca explícitamente como no resuelto en vez de forzar un mapeo.
UNRESOLVED_RATING_SENTINEL = "requiere_revision_manual"


def map_colombiacheck_rating(rating_raw: str) -> tuple[str | None, bool]:
    """Devuelve (label_fuente, es_candidata_dudosa) para una calificación cruda de ColombiaCheck.

    Si la calificación no está en el mapa verificado (ej. "Chequeo Múltiple"
    u otra categoría nueva no vista al momento de escribir este módulo), se
    marca como candidata a dudosa para revisión manual en vez de asumir.
    """
    key = rating_raw.strip().lower()
    return COLOMBIACHECK_RATING_MAP.get(key, (None, True))


def es_chequeo_individual(rating_raw: str) -> bool:
    """False si la calificación indica que el ítem no es un chequeo individual (ej. Podcast)."""
    return rating_raw.strip().lower() not in NO_ES_CHEQUEO_INDIVIDUAL
