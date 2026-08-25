"""
export_feed.py -- generates the WARN feed artifacts for GitHub Pages.

Called by run.py inside the scheduled GitHub Action. Produces:
  index.html      the styled embed the FMG page iframes
  warn_feed.json  machine-readable copy of the same data

Each filing dict should carry:
    company    str      employer name as filed
    county     str      PA county
    affected   str|int  number of workers, as published
    effective  str      effective date or range, as published
    type       str      "Closure" or "Layoff" (or as published)

Missing keys render as blank; a row without a company name is dropped.
"""

import datetime
import html as html_mod
import json

SOURCE_URL = (
    "https://www.pa.gov/agencies/dli/programs-services/"
    "workforce-development-home/warn-requirements/warn-notices"
)

MAX_ROWS = 8


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def _normalize(filings, limit=MAX_ROWS):
    rows = []
    for f in filings:
        row = {
            "company": _clean(f.get("company")),
            "county": _clean(f.get("county")).removesuffix(" County").strip(),
            "affected": _clean(f.get("affected")),
            "effective": _clean(f.get("effective")),
            "type": _clean(f.get("type")),
        }
        if row["company"]:
            rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def _county_label(value):
    """PA publishes 'Chester', 'Montgomery and Philadelphia', 'Various',
    and 'Various (All workers telework from home)'. Only append the word
    County where it actually reads correctly."""
    if not value:
        return ""
    if value.lower().startswith("various"):
        return value
    if " and " in value or "," in value:
        return f"{value} Counties"
    return f"{value} County"


def _affected_label(value):
    """Bare numbers get a unit; anything already descriptive
    ('7 - PA Remote Employees', 'Unknown', 'TBD') is shown as filed."""
    if not value:
        return ""
    if value.replace(",", "").isdigit():
        return f"{value} workers affected"
    return value


def _row_html(f):
    e = html_mod.escape
    meta_bits = [
        e(_county_label(f["county"])),
        e(_affected_label(f["affected"])),
        f"Effective {e(f['effective'])}" if f["effective"] else "",
        e(f["type"]) if f["type"] else "",
    ]
    meta = "&nbsp;&nbsp;&#8226;&nbsp;&nbsp;".join(b for b in meta_bits if b)
    return (
        '<div style="border-bottom:1px solid #C3BAA6;padding:16px 0;">'
        f'<div style="font-family:Oswald,Arial,sans-serif;font-size:1.15rem;'
        f'font-weight:600;text-transform:uppercase;letter-spacing:0.03em;'
        f'line-height:1.2;">{e(f["company"])}</div>'
        f'<div style="font-size:0.95rem;color:#3C4A57;margin-top:8px;'
        f'line-height:1.7;">{meta}</div>'
        "</div>"
    )


def build_html(rows, generated_utc):
    updated = generated_utc.strftime("%B %-d, %Y")
    body_rows = "\n".join(_row_html(f) for f in rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>Recent Pennsylvania WARN Filings</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  html, body {{ margin: 0; padding: 0; background: #FFFFFF; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: #16212B;
    padding: 2px 2px 12px;
  }}
  a {{ color: #A07E3F; text-decoration: none; border-bottom: 1px solid rgba(160,126,63,0.4); }}
</style>
</head>
<body>
<div style="font-family:Oswald,Arial,sans-serif;font-size:0.85rem;letter-spacing:0.2em;text-transform:uppercase;color:#A07E3F;font-weight:600;margin-bottom:14px;">Updated {updated}</div>
{body_rows}
<div style="font-size:0.95rem;margin-top:18px;line-height:1.7;"><a href="{SOURCE_URL}" target="_blank" rel="noopener">View all filings at the Pennsylvania Department of Labor &#38; Industry</a></div>
</body>
</html>
"""


def write_all(filings, html_path="index.html", json_path="warn_feed.json"):
    """Normalize filings (newest first) and write both artifacts."""
    rows = _normalize(filings)
    if not rows:
        raise SystemExit(
            "Scrape returned zero filings -- refusing to overwrite the feed. "
            "The previous feed stays live; investigate the scraper."
        )
    now = datetime.datetime.now(datetime.timezone.utc)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(
            {"generated": now.isoformat(), "source": SOURCE_URL, "filings": rows},
            fh, ensure_ascii=False, indent=2,
        )
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(build_html(rows, now))
    return html_path, json_path
