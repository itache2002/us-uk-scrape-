from __future__ import annotations

import os
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from .dedupe import lead_key
from .models import Lead

HEADERS = [
    "Name", "Category", "City", "Country", "Website", "Address", "Emails",
    "Phones", "Facebook", "Instagram", "LinkedIn", "Source URL",
    "Quality Score", "Status", "Error",
]


class ExcelStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.workbook = load_workbook(self.path)
            self.sheet = self.workbook["Leads"]
        else:
            self.workbook = Workbook()
            self.sheet = self.workbook.active
            self.sheet.title = "Leads"
            self.sheet.append(HEADERS)
            self.sheet.freeze_panes = "A2"
            self.sheet.auto_filter.ref = f"A1:O1"
            for cell in self.sheet[1]:
                cell.font = Font(bold=True)
            self.save()

    def append(self, lead: Lead) -> None:
        self.sheet.append([safe_cell(value) for value in [
            lead.name, lead.category, lead.city, lead.country, lead.website,
            lead.address, "; ".join(lead.emails), "; ".join(lead.phones),
            lead.facebook, lead.instagram, lead.linkedin, lead.source_url,
            lead.quality_score, lead.status, lead.error,
        ]])
        self.save()

    def existing_keys(self) -> set[str]:
        keys: set[str] = set()
        for row in self.sheet.iter_rows(min_row=2, values_only=True):
            lead = Lead(
                name=str(row[0] or ""), category=str(row[1] or ""),
                city=str(row[2] or ""), country=str(row[3] or ""),
                website=str(row[4] or ""),
            )
            keys.add(lead_key(lead))
        return keys

    def save(self) -> None:
        temporary = self.path.with_name(f".{self.path.name}.tmp.xlsx")
        self.workbook.save(temporary)
        os.replace(temporary, self.path)


def safe_cell(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value
