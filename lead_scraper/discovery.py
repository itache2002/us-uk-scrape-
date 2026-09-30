from __future__ import annotations

import json
import re
from urllib.parse import quote_plus

from .cleaning import clean_email, clean_phone, clean_url
from .models import Job, Lead

CATEGORY_TAGS = {
    "plumber": (("craft", "plumber"),),
    "plumbing": (("craft", "plumber"),),
    "cafe": (("amenity", "cafe"),),
    "coffee shop": (("amenity", "cafe"),),
    "electrician": (("craft", "electrician"),),
    "hvac": (("craft", "hvac"),),
    "roofer": (("craft", "roofer"),),
    "cleaner": (("craft", "cleaning"),),
    "cleaning": (("craft", "cleaning"),),
    "restaurant": (("amenity", "restaurant"),),
    "bakery": (("shop", "bakery"),),
    "hairdresser": (("shop", "hairdresser"),),
}


class OpenStreetMapDiscovery:
    geocoder = "https://nominatim.openstreetmap.org/search"
    overpass = "https://overpass-api.de/api/interpreter"

    def __init__(self, client: object) -> None:
        self.client = client

    def discover(self, job: Job) -> list[Lead]:
        location_url = (
            f"{self.geocoder}?city={quote_plus(job.city)}&country={job.country}"
            "&format=jsonv2&limit=1"
        )
        locations = _json(self.client.get(location_url))
        if not locations:
            return []
        south, north, west, east = locations[0]["boundingbox"]
        bbox = f"{south},{west},{north},{east}"
        selectors = CATEGORY_TAGS.get(job.category.lower().strip())
        if selectors:
            clauses = "".join(f'nwr["{key}"="{value}"]["name"]({bbox});' for key, value in selectors)
        else:
            term = re.escape(job.category.strip())
            clauses = f'nwr["name"~"{term}",i]({bbox});'
        query = f"[out:json][timeout:30];({clauses});out center {job.limit};"
        data = _json(self.client.get(f"{self.overpass}?data={quote_plus(query)}"))
        return [self._lead(item, job) for item in data.get("elements", [])[: job.limit]]

    @staticmethod
    def _lead(item: dict, job: Job) -> Lead:
        tags = item.get("tags", {})
        website = tags.get("website") or tags.get("contact:website") or tags.get("url") or ""
        if website and "://" not in website:
            website = "https://" + website
        address = " ".join(
            str(tags.get(key, ""))
            for key in ("addr:housenumber", "addr:street", "addr:city", "addr:postcode")
            if tags.get(key)
        )
        email = clean_email(tags.get("email") or tags.get("contact:email") or "")
        phone = clean_phone(tags.get("phone") or tags.get("contact:phone") or "")
        osm_type = item.get("type", "node")
        source = f"https://www.openstreetmap.org/{osm_type}/{item.get('id', '')}"
        return Lead(
            name=tags.get("name") or f"Unnamed {job.category}",
            category=job.category,
            city=job.city,
            country=job.country,
            website=clean_url(website),
            address=address,
            emails=[email] if email else [],
            phones=[phone] if phone else [],
            facebook=tags.get("contact:facebook", ""),
            instagram=tags.get("contact:instagram", ""),
            linkedin=tags.get("contact:linkedin", ""),
            source_url=source,
        )


def _json(page: object):
    body = getattr(page, "body", b"")
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    return json.loads(body)
