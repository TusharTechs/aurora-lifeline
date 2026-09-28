"""Downloads IMD RSMC New Delhi archive products for one storm window (BUILD_PLAN task 1.4a).

The IMD archive lists products newest first, 30 per page, per year. This walks the pages for each
product type, keeps items listed inside [--from, --to] (the archive's own date column, timezone
unverified; the bulletin header is the authoritative issue time), and saves them under
data/raw/imd/<storm>/<product>/ with sha256sums.txt and an index.csv of source URLs.

IMD redistribution terms are unverified: files stay in the git-ignored data/ cache (and later a
private bucket). They are never committed or re-hosted; the app links to IMD instead.

Usage:
    python -m aurora_pipelines.imd_archive --storm montha_2025 --year 2025 \
        --from 2025-10-22 --to 2025-10-30
"""

import argparse
import base64
import csv
import hashlib
import html
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

BASE = "https://rsmcnewdelhi.imd.gov.in/"
USER_AGENT = "aurora-lifeline-research/0.1 (open-source disaster-planning prototype)"

# product name -> (internal_menu id, menu_id), as linked from the RSMC archive pages.
PRODUCTS: dict[str, tuple[int, int]] = {
    "national_bulletin": (1, 4),
    "rsmc_bulletin": (2, 4),
    "quadrant_wind_bulletin": (4, 4),
    "observed_forecast_track": (6, 5),
    "storm_surge_guidance": (7, 5),
    "heavy_rainfall": (8, 5),
    "press_release": (21, 2),
}

ROW_RE = re.compile(
    r"<tr>\s*<td>\d+</td>\s*<td>(?P<title>.*?)</td>\s*<td[^>]*>(?P<listed>.*?)</td>\s*<td>(?P<file>.*?)</td>",
    re.S,
)
HREF_RE = re.compile(r'href="([^"]+)"')


@dataclass(frozen=True)
class Item:
    product: str
    title: str
    listed_at: datetime  # archive's 'Issue Date & Time' column; timezone unverified
    url: str


def b64(n: int | str) -> str:
    return base64.b64encode(str(n).encode()).decode()


def fetch(url: str, *, retries: int = 3, timeout: int = 180) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body: bytes = resp.read()
                return body
        except OSError as err:
            if attempt == retries:
                raise
            print(f"  retry {attempt} after {err}", file=sys.stderr)
            time.sleep(5 * attempt)
    raise AssertionError("unreachable")


def list_page(product: str, year: int, page: int) -> list[Item]:
    internal, menu = PRODUCTS[product]
    query = urllib.parse.urlencode(
        {
            "internal_menu": b64(internal),
            "pageno": page,
            "menu_id": b64(menu),
            "search_year": b64(year),
        }
    )
    text = fetch(f"{BASE}archive-information.php?{query}").decode("utf-8", errors="replace")
    items = []
    for m in ROW_RE.finditer(text):
        href = HREF_RE.search(m["file"])
        if not href:
            continue
        listed = datetime.strptime(re.sub(r"\s+", " ", m["listed"]).strip(), "%d-%m-%Y %H:%M:%S")
        title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m["title"]))).strip()
        items.append(
            Item(product, title, listed, urllib.parse.urljoin(BASE, html.unescape(href.group(1))))
        )
    return items


def collect(product: str, year: int, start: date, end: date, max_pages: int) -> list[Item]:
    found: list[Item] = []
    for page in range(1, max_pages + 1):
        items = list_page(product, year, page)
        if not items:
            break
        found += [i for i in items if start <= i.listed_at.date() <= end]
        if min(i.listed_at.date() for i in items) < start:
            break  # pages are newest first; everything further back is older
    return sorted(found, key=lambda i: (i.listed_at, i.url))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--storm", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--from", dest="start", type=date.fromisoformat, required=True)
    ap.add_argument("--to", dest="end", type=date.fromisoformat, required=True)
    ap.add_argument("--products", nargs="*", default=list(PRODUCTS))
    ap.add_argument("--max-pages", type=int, default=15)
    ap.add_argument("--out", type=Path, default=Path("data/raw/imd"))
    args = ap.parse_args()

    for product in args.products:
        items = collect(product, args.year, args.start, args.end, args.max_pages)
        out = args.out / args.storm / product
        out.mkdir(parents=True, exist_ok=True)
        print(f"{product}: {len(items)} items")
        rows = []
        for item in items:
            name = item.url.rsplit("/", 1)[-1]
            path = out / name
            if not path.exists():
                path.write_bytes(fetch(item.url))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append([item.listed_at.isoformat(), item.title, item.url, name, digest])
        with (out / "index.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["listed_at", "title", "source_url", "file", "sha256"])
            w.writerows(rows)
        (out / "sha256sums.txt").write_text("".join(f"{r[4]}  {r[3]}\n" for r in rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
