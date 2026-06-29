Status: completed

## Parent

[PRD.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD.md)

## What to build

Create the automated data collection pipeline using GitHub Actions to run the Python script once daily. Implement a resilient data fallback mechanism in `update_data.py` so that a failure or layout change in one of the external web scrapers (like CNN or OpenInsider) does not crash the script or prevent other indicators from updating.

## Acceptance criteria

- [x] A GitHub Actions workflow `.github/workflows/update_data.yml` is created, scheduled to run daily at `22:00 UTC` (cron `0 22 * * *`), and triggers manually on `workflow_dispatch`.
- [x] Workflow steps: set up Python, install dependencies (`requests`, `yfinance`, `beautifulsoup4`), run the data script, and commit `data/market_data.json` back to the repository.
- [x] Script loading logic: Before running, the script reads `data/market_data.json` if it exists.
- [x] Resiliency check: If fetching an individual indicator (e.g. CNN Fear & Greed API) fails or times out, the script catches the exception, prints a detailed warning log, and duplicates the latest historical data point for that day from the previously loaded JSON.
- [x] Initialization check: If `data/market_data.json` is missing entirely (such as on first-time local setup), the script runs successfully and builds a new file.

## Blocked by

- [01-core-shell-and-vix.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/.scratch/market-dashboard/issues/01-core-shell-and-vix.md)
