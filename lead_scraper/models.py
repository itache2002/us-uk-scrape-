from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Job:
    country: str
    city: str
    category: str
    limit: int

    def __post_init__(self) -> None:
        country = self.country.upper().strip()
        if country not in {"US", "UK"}:
            raise ValueError("country must be US or UK")
        if not self.city.strip() or not self.category.strip():
            raise ValueError("city and category are required")
        if self.limit < 1:
            raise ValueError("limit must be positive")
        object.__setattr__(self, "country", country)
        object.__setattr__(self, "city", self.city.strip())
        object.__setattr__(self, "category", self.category.strip())

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class Lead:
    name: str
    category: str
    city: str
    country: str
    website: str = ""
    address: str = ""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    facebook: str = ""
    instagram: str = ""
    linkedin: str = ""
    source_url: str = ""
    quality_score: int = 0
    status: str = "discovered"
    error: str = ""
