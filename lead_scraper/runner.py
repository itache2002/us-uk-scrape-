from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from .checkpoint import Checkpoint
from .config import AppConfig
from .dedupe import Deduplicator, lead_key
from .discovery import OpenStreetMapDiscovery
from .enrichment import WebsiteEnricher
from .excel import ExcelStore
from .fetching import ScraplingClient


def run(
    config: AppConfig,
    resume_state: dict | None = None,
    client_factory: Callable[[], object] | None = None,
) -> int:
    store = ExcelStore(config.output)
    checkpoint = Checkpoint(config.checkpoint)
    dedupe = Deduplicator(store.existing_keys())
    state = resume_state or {
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
    processed = set(state.get("processed", []))
    written = 0
    factory = client_factory or (lambda: ScraplingClient(config.retries, config.timeout))

    for job_index in range(int(state.get("job_index", 0)), len(config.jobs)):
        job = config.jobs[job_index]
        leads = OpenStreetMapDiscovery(factory()).discover(job)
        pending = [lead for lead in leads if lead_key(lead) not in processed and dedupe.add(lead)]

        with ThreadPoolExecutor(max_workers=config.concurrency) as pool:
            futures = {pool.submit(WebsiteEnricher(factory()).enrich, lead): lead for lead in pending}
            for future in as_completed(futures):
                lead = future.result()
                store.append(lead)
                processed.add(lead_key(lead))
                written += 1
                state.update(job_index=job_index, processed=sorted(processed), done=False)
                checkpoint.save(state)

        state.update(job_index=job_index + 1, processed=[], done=False)
        processed.clear()
        checkpoint.save(state)

    state["done"] = True
    checkpoint.save(state)
    return written
