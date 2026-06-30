Status: ready-for-agent

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Add `FMP_API_KEY` environment variable support and fetch S&P 500 aggregate earnings data from Financial Modeling Prep's free-tier API: year-over-year EPS growth and year-over-year revenue growth. When the key is absent, skip gracefully — mark the corresponding scorecard metrics as "unavailable" and log a warning. Write earnings data to the JSON contract and render charts in the new "Fundamentals & Valuation" tab. Show a "Configure FMP_API_KEY to enable" placeholder when data is unavailable.

## Acceptance criteria

- [ ] Python script reads `FMP_API_KEY` from `os.environ.get()`.
- [ ] When key is present, script fetches S&P 500 aggregate quarterly EPS and revenue data from FMP's free API.
- [ ] Script computes year-over-year growth rates for both EPS and revenue.
- [ ] Data is written to `indicators.eps_growth` and `indicators.revenue_growth` as `{date, value}` arrays.
- [ ] When key is absent, script logs a warning and writes empty arrays for both indicators.
- [ ] Scorecard entries for `eps_growth` (healthy when YoY > 0%) and `revenue_growth` (healthy when YoY > 0%) are computed. Both are set to "unavailable" when key is absent.
- [ ] A new "Fundamentals & Valuation" tab is added to the UI.
- [ ] UI renders line charts for EPS Growth and Revenue Growth in the new tab.
- [ ] When data is unavailable, chart cards show a subtle "Configure FMP_API_KEY to enable this chart" hint.
- [ ] GitHub Actions workflow passes `FMP_API_KEY` from secrets to the Python script.
- [ ] Tests verify graceful skip when `FMP_API_KEY` is absent (no crash, empty data, "unavailable" scorecard status).

## Blocked by

- [08-fred-api-fallback.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/08-fred-api-fallback.md) — follows the layered fallback pattern established there
