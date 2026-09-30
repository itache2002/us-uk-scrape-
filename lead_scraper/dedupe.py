from __future__ import annotations

import re
from urllib.parse import urlparse

from .models import Lead


def lead_key(lead: Lead) -> str:
    host = urlparse(lead.website).netloc.lower().split(":", 1)[0].removeprefix("www.")
    if host:
        return f"site:{host}"
    clean = lambda value: re.sub(r"[^a-z0-9]", "", value.lower())
    return f"name:{clean(lead.name)}:{clean(lead.city)}:{lead.country.lower()}"


class Deduplicator:
    def __init__(self, keys: set[str] | None = None) -> None:
        self.keys = keys or set()

    def add(self, lead: Lead) -> bool:
        key = lead_key(lead)
        if key in self.keys:
            return False
        self.keys.add(key)
        return True
