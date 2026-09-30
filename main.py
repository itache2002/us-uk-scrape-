from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lead_scraper.checkpoint import Checkpoint
from lead_scraper.config import AppConfig, load_config
from lead_scraper.models import Job
from lead_scraper.runner import run


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Scrape US/UK small-business leads to Excel")
    source = value.add_mutually_exclusive_group(required=True)
    source.add_argument("--config", help="JSON batch job file")
    source.add_argument("--resume", action="store_true", help="resume output/checkpoint.json")
    source.add_argument("--country", choices=("US", "UK"))
    value.add_argument("--city")
    value.add_argument("--category")
    value.add_argument("--limit", type=int)
    value.add_argument("--output", default="output/leads.xlsx")
    value.add_argument("--checkpoint", default="output/checkpoint.json")
    value.add_argument("--concurrency", type=int, default=5)
    value.add_argument("--retries", type=int, default=3)
    value.add_argument("--timeout", type=float, default=20)
    return value


def make_config(args: argparse.Namespace) -> tuple[AppConfig, dict | None]:
    if args.config:
        return load_config(args.config), None
    if args.resume:
        state = Checkpoint(args.checkpoint).load()
        settings = state.get("settings", {})
        config = AppConfig(
            jobs=[Job(**item) for item in state["jobs"]],
            output=Path(settings.get("output", args.output)),
            checkpoint=Path(args.checkpoint),
            concurrency=int(settings.get("concurrency", args.concurrency)),
            retries=int(settings.get("retries", args.retries)),
            timeout=float(settings.get("timeout", args.timeout)),
        )
        return config, state
    if not args.city or not args.category or args.limit is None:
        raise ValueError("--country requires --city, --category, and --limit")
    return AppConfig(
        jobs=[Job(args.country, args.city, args.category, args.limit)],
        output=Path(args.output), checkpoint=Path(args.checkpoint),
        concurrency=args.concurrency, retries=args.retries, timeout=args.timeout,
    ), None


def main() -> int:
    try:
        args = parser().parse_args()
        config, state = make_config(args)
        if state is None:
            state = {
                "jobs": [job.to_dict() for job in config.jobs],
                "job_index": 0,
                "processed": [],
                "done": False,
                "settings": {
                    "output": str(config.output),
                    "concurrency": config.concurrency,
                    "retries": config.retries,
                    "timeout": config.timeout,
                },
            }
        count = run(config, state)
        print(f"Saved {count} new leads to {config.output}")
        return 0
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
