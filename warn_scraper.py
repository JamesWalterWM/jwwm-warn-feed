"""
warn_scraper.py -- pulls WARN filings from the PA DLI notices page.

The page is a single flat document, newest first:

    <h2>2026</h2>
    <h2>August</h2>
    <h3>Grede, LLC</h3>
    <p>18771 Mill Street, Meadville, PA 16335</p>
    <p>COUNTY: Crawford<br># AFFECTED: 170<br>
       EFFECTIVE DATE: 10/10/26<br>CLOSURE OR LAYOFF: Closure</p>

Quirks this handles, all present on the live page:
  - month headings are <h2> in recent years but <h3> in older ones
  - "COUNTY:" vs "COUNTIES:"; "# AFFECTED:" vs "AFFECTED:"
  - "EFFECTIVE DATE:" vs "EFFECTIVE DATES:"
  - trailing zero-width spaces after values (U+200B)
  - multi-site entries where the fields repeat; we take the first set
  - entries with no parseable fields at all (rare, irregular formatting)
"""

import re

import requests
from bs4 import BeautifulSoup

URL = (
    "https://www.pa.gov/agencies/dli/programs-services/"
    "workforce-development-home/warn-requirements/warn-notices"
)

# Identify ourselves rather than pretending to be a browser.
HEADERS = {
    "User-Agent": (
        "JWWM-WARN-Feed/1.0 (public resource page; "
        "contact: james-walter-wealth-management)"
    )
}

MONTHS = {
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}

FIELD_PATTERNS = {
    "county": re.compile(r"COUNT(?:Y|IES)\s*:\s*(.+)", re.I),
    "affected": re.compile(r"#?\s*AFFECTED\s*:\s*(.+)", re.I),
    "effective": re.compile(r"EFFECTIVE\s+DATES?\s*:\s*(.+)", re.I),
    "type": re.compile(r"CLOSURE\s+OR\s+LAYOFF\s*:\s*(.+)", re.I),
}

# Headings that are page furniture, not employers.
SKIP_HEADINGS = re.compile(
    r"^(top services|pa\.gov|the \.gov means|was this page helpful)", re.I
)


def _clean(text):
    """Strip whitespace, zero-width spaces, and non-breaking spaces."""
    return re.sub(r"[\u200b\u200e\ufeff\xa0]", " ", text or "").strip()


def _block_text(heading):
    """Concatenate the text between this heading and the next heading."""
    parts = []
    for sib in heading.next_siblings:
        name = getattr(sib, "name", None)
        if name in ("h1", "h2", "h3", "h4"):
            break
        text = sib.get_text("\n") if name else str(sib)
        if text:
            parts.append(text)
    return _clean("\n".join(parts))


def _parse_fields(block):
    """Pull the first occurrence of each field out of a filing block."""
    out = {}
    for key, pattern in FIELD_PATTERNS.items():
        match = pattern.search(block)
        out[key] = _clean(match.group(1)) if match else ""
    return out


def parse(html):
    """Return filings in page order (newest first)."""
    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup.body or soup

    filings = []
    year = month = ""

    for heading in root.find_all(["h2", "h3"]):
        label = _clean(heading.get_text())
        if not label or SKIP_HEADINGS.match(label):
            continue

        if re.fullmatch(r"20\d{2}", label):
            year, month = label, ""
            continue
        if label.lower().strip() in MONTHS:
            month = label
            continue
        if not year:
            continue  # heading above the listing; not a filing

        fields = _parse_fields(_block_text(heading))
        if not any(fields.values()):
            continue  # nav item or irregular entry with no data

        fields["company"] = label
        fields["filed"] = f"{month} {year}".strip()
        filings.append(fields)

    return filings


def get_filings(timeout=30):
    """Fetch and parse the live page. Raises on network or HTTP failure."""
    response = requests.get(URL, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    filings = parse(response.text)
    if not filings:
        raise RuntimeError(
            "Parsed zero filings -- the page structure likely changed. "
            "Inspect the DLI page before trusting the feed."
        )
    return filings


if __name__ == "__main__":
    for f in get_filings()[:5]:
        print(f)
