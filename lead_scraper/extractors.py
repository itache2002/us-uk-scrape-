from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from .cleaning import clean_email, clean_phone

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,24}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
CONTACT_WORDS = ("contact", "about", "location", "find-us", "get-in-touch")
SOCIAL_HOSTS = {
    "facebook": ("facebook.com",),
    "instagram": ("instagram.com",),
    "linkedin": ("linkedin.com",),
}


def extract_contacts(page: object, base_url: str) -> dict[str, object]:
    text = str(page.get_all_text(ignore_tags=("script", "style")))
    hrefs = [str(value) for value in page.css("a::attr(href)").getall()]
    emails = set(EMAIL_RE.findall(text))
    phones = {clean_phone(value) for value in PHONE_RE.findall(text)}
    socials: dict[str, str] = {}
    contact_pages: list[str] = []
    base_host = urlparse(base_url).netloc.lower().removeprefix("www.")

    for href in hrefs:
        absolute = urljoin(base_url, href.strip())
        parsed = urlparse(absolute)
        lowered = absolute.lower()
        if href.lower().startswith("mailto:"):
            emails.update(EMAIL_RE.findall(href))
        elif href.lower().startswith("tel:"):
            phone = clean_phone(href.split(":", 1)[1])
            if phone:
                phones.add(phone)
        for name, hosts in SOCIAL_HOSTS.items():
            if name not in socials and any(host in parsed.netloc.lower() for host in hosts):
                socials[name] = absolute
        host = parsed.netloc.lower().removeprefix("www.")
        if host == base_host and any(word in lowered for word in CONTACT_WORDS):
            if absolute not in contact_pages:
                contact_pages.append(absolute)

    return {
        "emails": sorted(clean_email(email) for email in emails if not email.lower().endswith((".png", ".jpg"))),
        "phones": sorted(phone for phone in phones if phone),
        "socials": socials,
        "contact_pages": contact_pages[:2],
    }
