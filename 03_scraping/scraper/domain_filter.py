"""Filtro de dominio financiero/bancario.

Implementa el criterio de `02_corpus/criterios_seleccion_fuentes.md`:
lista de palabras clave + revisión manual en la calibración inicial. No es
un clasificador aparte a propósito, para no introducir una dependencia
circular con el sistema que se está construyendo.
"""

import re

# Misma lista que en criterios_seleccion_fuentes.md ("Filtro de dominio").
# Si se edita aquí, editar también ese documento para que no diverjan.
DOMAIN_KEYWORDS = [
    r"tasas? de inter[eé]s",
    r"cr[eé]dito",
    r"hipoteca",
    r"banco",
    r"superintendencia financiera",
    r"\bSFC\b",
    r"sistema pensional",
    r"pensi[oó]n",
    r"impuesto",
    r"reforma tributaria",
    r"\bDIAN\b",
    r"peso colombiano",
    r"\bTRM\b",
    r"inflaci[oó]n",
    r"banco de la rep[uú]blica",
    r"\bBanRep\b",
]

_PATTERN = re.compile("|".join(DOMAIN_KEYWORDS), re.IGNORECASE)


def matches_financial_domain(text: str) -> bool:
    """Devuelve True si el texto menciona al menos un tema financiero del filtro de dominio."""
    if not text:
        return False
    return bool(_PATTERN.search(text))
