"""
Orchestrator run by the GitHub Action.

Scrapes the PA DLI WARN notices page and writes index.html + warn_feed.json.
Nothing here needs editing.
"""

from export_feed import write_all
from warn_scraper import get_filings

if __name__ == "__main__":
    filings = get_filings()
    html_path, json_path = write_all(filings)
    print(f"Parsed {len(filings)} filings; wrote {html_path} and {json_path}")
