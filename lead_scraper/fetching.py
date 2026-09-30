from __future__ import annotations

import time
from typing import Any, Callable
from urllib.parse import urlparse


class FetchError(RuntimeError):
    pass


class ScraplingClient:
    def __init__(
        self,
        retries: int = 3,
        timeout: float = 20,
        fetch: Callable[..., Any] | None = None,
    ) -> None:
        if fetch is None:
            from scrapling.fetchers import Fetcher

            fetch = Fetcher.get
        self.fetch = fetch
        self.retries = retries
        self.timeout = timeout

    def get(self, url: str) -> Any:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                public_api = urlparse(url).netloc in {
                    "nominatim.openstreetmap.org", "overpass-api.de"
                }
                headers = {"User-Agent": "BusinessLeadScraper/1.0"} if public_api else None
                page = self.fetch(
                    url,
                    timeout=self.timeout,
                    retries=0,
                    follow_redirects=True,
                    stealthy_headers=not public_api,
                    headers=headers,
                )
                status = int(getattr(page, "status", 200))
                if status < 400:
                    return page
                raise FetchError(f"HTTP {status} for {url}")
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(2**attempt, 4))
        raise FetchError(str(last_error)) from last_error
