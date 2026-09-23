"""Clasificación temática por palabras clave (enum de 02_corpus/README.md).

Corregido 2026-09-22 (REGISTRO_CORRECCIONES.md #7): el campo
`categoria_tematica` quedaba fijo en `"otro"` en los 7 spiders, con un
comentario que decía "se ajusta en la calibración inicial" -- pero la
calibración inicial (ver criterios_seleccion_fuentes.md) solo registró
decisiones de exclusión por relevancia, nunca categorías temáticas, así
que el campo nunca se pobló de verdad. Debía decidirse en la extracción,
no diferirse.

Igual que domain_filter.py: por palabras clave, no un clasificador
aparte, para no introducir una dependencia circular con el sistema que se
está construyendo (evaluado en la Fase 2).

Limitación reconocida: es una heurística de una sola etiqueta por ítem.
Un artículo puede mencionar más de un tema (ej. "impuestos a los créditos
hipotecarios" toca tributario Y crédito); se resuelve con la lista de
prioridad de abajo (categorías más específicas primero, "banca" al final
por ser la más genérica -- muchos artículos mencionan "banco" de forma
incidental sin ser realmente sobre el sistema bancario).
"""

import re

# Orden de prioridad: se evalúa de arriba hacia abajo y se devuelve la
# primera categoría cuyo patrón coincide. Los patrones no son mutuamente
# excluyentes en el texto -- el orden decide cuál gana en caso de que
# varios coincidan.
CATEGORIA_KEYWORDS: list[tuple[str, list[str]]] = [
    (
        "sistema_pensional",
        [
            r"sistema pensional",
            r"pensi[oó]n(es)?",
            r"colpensiones",
            r"\bRAIS\b",
            r"prima media",
            r"fondo(s)? de pensiones",
            r"reforma pensional",
        ],
    ),
    (
        "tributario",
        [
            r"impuesto",
            r"reforma tributaria",
            r"\bDIAN\b",
            r"\bIVA\b",
            r"declaraci[oó]n de renta",
            r"tributari[oa]",
        ],
    ),
    (
        "cambiario",
        [
            r"d[oó]lar",
            r"\bTRM\b",
            r"tasa de cambio",
            r"peso colombiano",
            r"divisa",
            r"mercado cambiario",
        ],
    ),
    (
        "tasas_interes",
        [
            r"tasas? de inter[eé]s",
            r"\bDTF\b",
            r"tasa de usura",
            r"tasa de intervenci[oó]n",
            r"tasa repo",
        ],
    ),
    (
        "creditos",
        [
            r"cr[eé]dito",
            r"hipoteca",
            r"pr[eé]stamo",
            r"tarjeta de cr[eé]dito",
            r"libranza",
            r"cartera (vencida|de cr[eé]dito)",
        ],
    ),
    (
        "banca",
        [
            r"banco",
            r"bancari[oa]",
            r"entidad financiera",
            r"superintendencia financiera",
            r"\bSFC\b",
            r"banco de la rep[uú]blica",
            r"\bBanRep\b",
        ],
    ),
]

_COMPILED = [
    (categoria, re.compile("|".join(patrones), re.IGNORECASE))
    for categoria, patrones in CATEGORIA_KEYWORDS
]


def clasificar_categoria_tematica(texto: str) -> str:
    """Devuelve la primera categoría del enum cuyo patrón coincide, u "otro"."""
    if not texto:
        return "otro"
    for categoria, pattern in _COMPILED:
        if pattern.search(texto):
            return categoria
    return "otro"
