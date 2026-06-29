Status: ready-for-agent

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Add `NASDAQ_DATA_LINK_API_KEY` environment variable support and fetch the Shiller CAPE Ratio from Nasdaq Data Link. Also fetch the S&P 500 Forward P/E ratio from FMP (reusing the `FMP_API_KEY` introduced in issue #13). When keys are absent, skip gracefully with "unavailable" scorecard status. Write both to the JSON contract and render charts in the "Fundamentals & Valuation" tab.

The Forward P/E is a scorecard metric (healthy between 14 and 22). The CAPE Ratio is a supplementary chart only — NOT a scorecard row — because it updates too infrequently (monthly) for weekly monitoring.

## Acceptance criteria

- [ ] Python script reads `NASDAQ_DATA_LINK_API_KEY` from `os.environ.get()`.
- [ ] When key is present, script fetches Shiller CAPE Ratio from Nasdaq Data Link (dataset `MULTPL/SHILLER_PE_RATIO_MONTH`).
- [ ] When key is absent, script logs a warning and writes an empty array for `cape_ratio`.
- [ ] Script fetches Forward P/E for S&P 500 from FMP using `FMP_API_KEY` (reusing the key from issue #13).
- [ ] Data is written to `indicators.forward_pe` and `indicators.cape_ratio` as `{date, value}` arrays.
- [ ] Scorecard entry for `forward_pe` evaluates healthy when value is between 14 and 22. Set to "unavailable" when FMP key is absent.
- [ ] CAPE Ratio has no scorecard entry — it is displayed as a supplementary chart only.
- [ ] UI renders Forward P/E and CAPE Ratio charts in the "Fundamentals & Valuation" tab.
- [ ] When data is unavailable, chart cards show configuration hints.
- [ ] GitHub Actions workflow passes `NASDAQ_DATA_LINK_API_KEY` from secrets to the Python script.
- [ ] Tests verify graceful skip when either key is absent.

## Blocked by

- [08-fred-api-fallback.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/08-fred-api-fallback.md) — follows the layered fallback pattern
- [13-sp500-earnings-fmp.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/13-sp500-earnings-fmp.md) — introduces the FMP key and "Fundamentals & Valuation" tab
