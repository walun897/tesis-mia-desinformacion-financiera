"""Mapeo de calificaciones de fact-checkers a la taxonomía trinaria del proyecto.

Verificado contra el HTML real de colombiacheck.com el 2026-09-22 (no
inventado): la página /metodologia describe la escala vigente como
Verdadero / Verdadero, pero / Cuestionable / Falso (categorías previas
Aproximado, Ligero e Inflado fueron consolidadas). El badge de calificación
en las tarjetas de /chequeos usa las clases CSS
`Chequeo-picture-bandera-text-{verdadero,cuestionable,falso,multiple}`.

"Chequeo Múltiple" no es una calificación de verdad sino un formato de
artículo con varias afirmaciones verificadas por separado — no mapea
limpio a la taxonomía trinaria de un solo ítem, se marca para revisión
manual en vez de asumir un valor.
"""

# (label_fuente, es_candidata_dudosa) — ver guia_anotacion.md para la
# justificación de cada categoría.
COLOMBIACHECK_RATING_MAP: dict[str, tuple[str | None, bool]] = {
    "verdadero": ("verdadera", False),
    "verdadero, pero": (None, True),  # mezcla elementos verdaderos y falsos -> dudosa
    "cuestionable": (None, True),
    "falso": ("falsa", False),
}

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
