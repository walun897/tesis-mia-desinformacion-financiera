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
