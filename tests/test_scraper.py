from __future__ import annotations

import json
import unittest
from pathlib import Path

from openpyxl import load_workbook

from lead_scraper.checkpoint import Checkpoint
from lead_scraper.config import load_config
from lead_scraper.dedupe import Deduplicator, lead_key
from lead_scraper.discovery import OpenStreetMapDiscovery
from lead_scraper.excel import ExcelStore
from lead_scraper.extractors import extract_contacts
from lead_scraper.models import Job, Lead
from lead_scraper.config import AppConfig
from lead_scraper.runner import run


class Selection(list):
    def getall(self):
        return list(self)

    def get(self):
        return self[0] if self else None


class Page:
    status = 200

    def __init__(self, results=None, text="", hrefs=None, body=b""):
        self.results = results or []
        self.text = text
        self.hrefs = hrefs or []
        self.body = body

    def css(self, selector):
        if selector == "li.b_algo":
            return self.results
        if selector == "a::attr(href)":
            return Selection(self.hrefs)
        return Selection()

    def get_all_text(self, **_):
        return self.text


class ScraperTests(unittest.TestCase):
    work = Path(__file__).parent / "test-output"

    def setUp(self):
        self.work.mkdir(exist_ok=True)
        for path in self.work.iterdir():
            if path.is_file():
                path.unlink()

    def test_config_and_validation(self):
        path = self.work / "jobs.json"
        path.write_text(json.dumps({"jobs": [{"country": "uk", "city": "London", "category": "cafe", "limit": 2}]}))
        config = load_config(path)
        self.assertEqual(config.jobs[0].country, "UK")
        self.assertEqual(config.output, self.work / "output/leads.xlsx")

    def test_discovery_maps_osm_business(self):
        class OsmClient:
            def get(self, url):
                if "nominatim" in url:
                    return Page(body=b'[{"boundingbox":["1","2","3","4"]}]')
                return Page(body=b'{"elements":[{"type":"node","id":1,"tags":{"name":"Example Plumbing","website":"example.com"}}]}')

        leads = OpenStreetMapDiscovery(OsmClient()).discover(Job("US", "Dallas", "plumber", 1))
        self.assertEqual(leads[0].website, "https://example.com")

    def test_extract_contacts(self):
        page = Page(
            text="Email HELLO@EXAMPLE.COM or call +1 (214) 555-1212",
            hrefs=["/contact", "https://instagram.com/example"],
        )
        data = extract_contacts(page, "https://example.com")
        self.assertEqual(data["emails"], ["hello@example.com"])
        self.assertIn("+12145551212", data["phones"])
        self.assertEqual(data["contact_pages"], ["https://example.com/contact"])

    def test_dedupe_by_domain(self):
        one = Lead("One", "cafe", "London", "UK", "https://www.example.com/a")
        two = Lead("Two", "cafe", "London", "UK", "http://example.com/b")
        dedupe = Deduplicator()
        self.assertTrue(dedupe.add(one))
        self.assertFalse(dedupe.add(two))
        self.assertEqual(lead_key(one), lead_key(two))

    def test_excel_and_checkpoint_persist(self):
        xlsx = self.work / "leads.xlsx"
        ExcelStore(xlsx).append(Lead("Cafe", "cafe", "London", "UK", "https://cafe.test"))
        self.assertEqual(load_workbook(xlsx)["Leads"].max_row, 2)
        checkpoint = Checkpoint(self.work / "checkpoint.json")
        checkpoint.save({"done": False})
        self.assertEqual(checkpoint.load(), {"done": False})

    def test_excel_escapes_formula_values(self):
        xlsx = self.work / "safe.xlsx"
        ExcelStore(xlsx).append(Lead("=1+1", "cafe", "London", "UK"))
        self.assertEqual(load_workbook(xlsx)["Leads"]["A2"].value, "'=1+1")

    def test_runner_writes_and_resumes(self):
        class RouterClient:
            def get(self, url):
                if "nominatim" in url:
                    return Page(body=b'[{"boundingbox":["1","2","3","4"]}]')
                if "overpass" in url:
                    return Page(body=b'{"elements":[{"type":"node","id":2,"tags":{"name":"Test Electrician","website":"https://business.test"}}]}')
                return Page(text="Contact team@business.test or +44 20 7946 0958")

        config = AppConfig(
            jobs=[Job("UK", "London", "electrician", 1)],
            output=self.work / "run.xlsx",
            checkpoint=self.work / "run.json",
            concurrency=2,
        )
        self.assertEqual(run(config, client_factory=RouterClient), 1)
        state = Checkpoint(config.checkpoint).load()
        self.assertTrue(state["done"])
        self.assertEqual(run(config, state, client_factory=RouterClient), 0)
        self.assertEqual(load_workbook(config.output)["Leads"].max_row, 2)


if __name__ == "__main__":
    unittest.main()
