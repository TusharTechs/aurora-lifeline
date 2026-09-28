"""Deterministic reader for the forecast table in IMD national cyclone bulletins.

This is not the Bulletin Reader (a Gemini agent, AI_AGENTS §3). It parses the PDF text layer with
a strict pattern and serves as the independent cross-check the agent's output is compared against,
and as the source of hand-entry drafts. It never guesses: rows that do not match are skipped and
reported.
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pdfplumber

IST = timezone(timedelta(hours=5, minutes=30))

# e.g. "27.10.25/1730 13.5/84.3 85-95 gusting to 105 Cyclonic Storm"
ROW_RE = re.compile(
    r"(?P<date>\d{2}\.\d{2}\.\d{2})/(?P<time>\d{4})\s+"
    r"(?P<lat>\d{1,2}\.\d)\s*/\s*(?P<lon>\d{2,3}\.\d)\s+"
    r"(?P<lo>\d{2,3})\s*-\s*(?P<hi>\d{2,3})\s+gusting\s+to\s+(?P<gust>\d{2,3})\s+"
    r"(?P<cat>(?:Super |Extremely |Very )?(?:Severe )?"
    r"(?:Cyclonic Storm|Deep Depression|Depression))"
)
ISSUE_RE = re.compile(
    r"TIME OF ISSUE:\s*(?P<hhmm>\d{4})\s*HOURS IST DATED:\s*(?P<date>\d{2}\.\d{2}\.\d{4})"
)
NUMBER_RE = re.compile(r"National Bulletin No\.\s*(?P<no>\d+)")


@dataclass(frozen=True)
class TableRow:
    valid_utc: datetime
    valid_text: str
    lat: float
    lon: float
    msw_min_kmph: int
    msw_max_kmph: int
    gust_kmph: int
    category: str
    row_text: str


@dataclass(frozen=True)
class NationalBulletinTable:
    bulletin_no: str | None
    issued_at_utc: datetime | None
    issued_at_text: str | None
    rows: list[TableRow]
    text: str


def pdf_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return re.sub(r"\s+", " ", "\n".join((p.extract_text() or "") for p in pdf.pages))


def parse_national_bulletin(path: Path) -> NationalBulletinTable:
    """Parses the issue time, bulletin number and forecast table of an IMD national bulletin."""
    text = pdf_text(path)
    issue = ISSUE_RE.search(text)
    issued_utc = None
    if issue:
        local = datetime.strptime(f"{issue['date']} {issue['hhmm']}", "%d.%m.%Y %H%M").replace(
            tzinfo=IST
        )
        issued_utc = local.astimezone(UTC)
    number = NUMBER_RE.search(text)
    rows = []
    for m in ROW_RE.finditer(text):
        local = datetime.strptime(f"{m['date']}/{m['time']}", "%d.%m.%y/%H%M").replace(tzinfo=IST)
        rows.append(
            TableRow(
                valid_utc=local.astimezone(UTC),
                valid_text=f"{m['date']}/{m['time']} IST",
                lat=float(m["lat"]),
                lon=float(m["lon"]),
                msw_min_kmph=int(m["lo"]),
                msw_max_kmph=int(m["hi"]),
                gust_kmph=int(m["gust"]),
                category=m["cat"],
                row_text=m.group(0),
            )
        )
    return NationalBulletinTable(
        bulletin_no=number["no"] if number else None,
        issued_at_utc=issued_utc,
        issued_at_text=issue.group(0) if issue else None,
        rows=rows,
        text=text,
    )
