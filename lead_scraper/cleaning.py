from __future__ import annotations

import re
from urllib.parse import urlparse


def clean_email(value: str) -> str:
    return value.strip().lower().removeprefix("mailto:").split("?", 1)[0]


def clean_phone(value: str) -> str:
    value = value.strip()
    prefix = "+" if value.startswith("+") else ""
    digits = re.sub(r"\D", "", value)
    return prefix + digits if 8 <= len(digits) <= 15 else ""


def clean_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return parsed._replace(fragment="").geturl()
