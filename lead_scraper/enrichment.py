from __future__ import annotations

from .extractors import extract_contacts
from .models import Lead


class WebsiteEnricher:
    def __init__(self, client: object) -> None:
        self.client = client

    def enrich(self, lead: Lead) -> Lead:
        if not lead.website:
            lead.status = "no_website"
            lead.quality_score = score(lead)
            return lead
        try:
            home = self.client.get(lead.website)
            found = extract_contacts(home, lead.website)
            for url in found.pop("contact_pages"):
                if found["emails"] and found["phones"]:
                    break
                extra = extract_contacts(self.client.get(url), lead.website)
                found["emails"] = sorted(set(found["emails"]) | set(extra["emails"]))
                found["phones"] = sorted(set(found["phones"]) | set(extra["phones"]))
                found["socials"].update(extra["socials"])
            lead.emails = sorted(set(lead.emails) | set(found["emails"]))
            lead.phones = sorted(set(lead.phones) | set(found["phones"]))
            lead.facebook = found["socials"].get("facebook", lead.facebook)
            lead.instagram = found["socials"].get("instagram", lead.instagram)
            lead.linkedin = found["socials"].get("linkedin", lead.linkedin)
            lead.status = "enriched"
        except Exception as exc:
            lead.status = "error"
            lead.error = str(exc)[:500]
        lead.quality_score = score(lead)
        return lead


def score(lead: Lead) -> int:
    return min(
        100,
        (40 if lead.emails else 0)
        + (30 if lead.phones else 0)
        + (15 if lead.website else 0)
        + (10 if lead.address else 0)
        + (5 if lead.facebook or lead.instagram or lead.linkedin else 0),
    )
