"""Detección de duplicados por similitud de n-gramas.

Umbral 0.85 tomado de `02_corpus/criterios_seleccion_fuentes.md`
(criterios de exclusión), que a su vez lo toma de M06-Methodology.tex.
"""

DUPLICATE_THRESHOLD = 0.85


def char_ngrams(text: str, n: int = 5) -> set[str]:
    """N-gramas de caracteres, normalizado a minúsculas y espacios colapsados."""
    normalized = " ".join(text.lower().split())
    if len(normalized) < n:
        return {normalized} if normalized else set()
    return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


class DuplicateIndex:
    """Índice en memoria de n-gramas ya vistos, para deduplicar durante una corrida.

    Nota: es un índice O(n) por comparación — suficiente para el volumen
    objetivo del corpus (800-1.000 ítems). Si el corpus crece
    significativamente, reemplazar por un índice de similitud aproximada
    (ej. MinHash/LSH).
    """

    def __init__(self, threshold: float = DUPLICATE_THRESHOLD) -> None:
        self.threshold = threshold
        self._seen: list[tuple[str, set[str]]] = []  # (id, ngrams)

    def max_similarity(self, text: str) -> float:
        """Máxima similitud contra cualquier ítem ya indexado (para poblar similitud_ngramas_max)."""
        candidate = char_ngrams(text)
        if not self._seen:
            return 0.0
        return max(jaccard_similarity(candidate, existing) for _, existing in self._seen)

    def is_duplicate(self, text: str) -> bool:
        return self.max_similarity(text) > self.threshold

    def add(self, item_id: str, text: str) -> None:
        self._seen.append((item_id, char_ngrams(text)))
