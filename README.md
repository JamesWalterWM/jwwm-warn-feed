# jwwm-warn-feed

Self-updating PA WARN filings feed for the "Laid Off in Pennsylvania" page.

A scheduled GitHub Action scrapes the PA Department of Labor & Industry
WARN notices page twice a week, rebuilds `index.html`, and commits it.
GitHub Pages serves that file; the FMG page shows it in an iframe.
No manual steps after setup.

## Files

| File | What it does |
|---|---|
| `warn_scraper.py` | Fetches and parses the PA DLI notices page |
| `export_feed.py` | Renders `index.html` (the embed) and `warn_feed.json` |
| `run.py` | Ties the two together; run by the Action |
| `.github/workflows/update.yml` | The schedule |
| `tests/fixture.html` | Sample of the real page structure, for testing |

## One-time setup

1. Create this repo as **public**, push these files.
2. Settings -> Pages -> Source: "Deploy from a branch" -> `main` / `/ (root)`.
3. Actions tab -> "Update WARN feed" -> "Run workflow".
4. When the run is green, open
   `https://<your-username>.github.io/jwwm-warn-feed/` and confirm real
   filings appear.
5. In the FMG page, set the iframe `src` to that URL (search the page
   source for `YOUR-GITHUB-USERNAME`; it appears once).

## Testing locally

    pip install requests beautifulsoup4 lxml
    python -c "import warn_scraper; print(warn_scraper.parse(open('tests/fixture.html').read()))"
    python run.py    # hits the live site

## Failure behavior

The run aborts without publishing if the scrape fails, returns zero
filings, or the page structure changes enough that nothing parses. The
previous feed stays live with its date stamp, and GitHub emails you.

If PA redesigns the page, `warn_scraper.py` is the only file to fix --
the parser keys off `<h2>`/`<h3>` headings for year, month, and employer,
then regexes `COUNTY:`, `# AFFECTED:`, `EFFECTIVE DATE:`, and
`CLOSURE OR LAYOFF:` out of the text beneath each employer.
