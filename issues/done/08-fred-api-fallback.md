Status: completed

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Introduce `FRED_API_KEY` environment variable support into the data pipeline, establishing the layered fallback pattern defined in ADR 0001. When the key is present, FRED data is fetched via the official FRED API (faster, more reliable). When absent, the pipeline falls back to the existing keyless CSV scraping — no data is lost. Update the GitHub Actions workflow to pass the secret as an environment variable. Document all three required API keys (`FRED_API_KEY`, `FMP_API_KEY`, `NASDAQ_DATA_LINK_API_KEY`) and their setup in the README.

This is the foundational infrastructure slice: later issues (#15, and indirectly #13/#14) depend on the patterns established here.

## Acceptance criteria

- [x] Python pipeline reads `FRED_API_KEY` from `os.environ.get()`.
- [x] When the key is present, FRED series are fetched via the official API endpoint (`https://api.stlouisfed.org/fred/series/observations`).
- [x] When the key is absent, the existing keyless CSV scraping path is used unchanged.
- [x] When the API key is present but the API returns an error, the pipeline falls back to CSV scraping and logs a warning.
- [x] The GitHub Actions workflow passes `FRED_API_KEY` from repository secrets as an environment variable to the Python script.
- [x] README documents all three API keys: name, provider, free-tier signup link, and how to add them as GitHub secrets.
- [x] Tests verify both the API path and the CSV fallback path produce identical output structure.

## Blocked by

None — can start immediately
