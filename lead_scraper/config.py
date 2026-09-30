from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Job


@dataclass(frozen=True)
class AppConfig:
    jobs: list[Job]
    output: Path = Path("output/leads.xlsx")
    checkpoint: Path = Path("output/checkpoint.json")
    concurrency: int = 5
    retries: int = 3
    timeout: float = 20

    def __post_init__(self) -> None:
        if not self.jobs:
            raise ValueError("at least one job is required")
        if not 1 <= self.concurrency <= 20:
            raise ValueError("concurrency must be between 1 and 20")
        if not 0 <= self.retries <= 10:
            raise ValueError("retries must be between 0 and 10")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})
    raw_jobs = data.get("jobs") or ([data["job"]] if "job" in data else [])
    jobs = [Job(**(defaults | item)) for item in raw_jobs]
    base = config_path.parent.parent if config_path.parent.name == "config" else config_path.parent

    def resolved(value: str, fallback: str) -> Path:
        candidate = Path(value or fallback)
        return candidate if candidate.is_absolute() else base / candidate

    return AppConfig(
        jobs=jobs,
        output=resolved(data.get("output", ""), "output/leads.xlsx"),
        checkpoint=resolved(data.get("checkpoint", ""), "output/checkpoint.json"),
        concurrency=int(data.get("concurrency", 5)),
        retries=int(data.get("retries", 3)),
        timeout=float(data.get("timeout", 20)),
    )
