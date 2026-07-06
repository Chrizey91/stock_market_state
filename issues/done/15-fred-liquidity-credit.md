Status: ready-for-agent

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Fetch three additional FRED series using the FRED API (with CSV fallback, as established in issue #08): Investment Grade Credit Spread (`BAMLC0A4CBBB`), Fed Balance Sheet (`WALCL`), and Bank Lending (`TOTLL`). Write them to the JSON contract and render charts in the "Credit & Liquidity" tab alongside the existing HY Spread, M2 Growth, Fed Funds Rate, 10Y Treasury, and Yield Curve charts.

## Acceptance criteria

- [ ] Python script fetches 5 years of historical data for `BAMLC0A4CBBB` (IG Spread), `WALCL` (Fed Balance Sheet), and `TOTLL` (Bank Lending) using the FRED API with CSV fallback.
- [ ] Data is written to `indicators.ig_spread`, `indicators.fed_balance_sheet`, and `indicators.bank_lending` as `{date, value}` arrays.
- [ ] UI renders three additional line/area charts in the "Credit & Liquidity" tab.
- [ ] IG Spread chart includes annotations explaining that widening IG spreads signal broader credit stress beyond just junk bonds.
- [ ] Fed Balance Sheet and Bank Lending charts include tooltips explaining their relationship to market liquidity.
- [ ] Existing Credit & Liquidity charts (HY Spread, M2, Fed Funds, 10Y Treasury, Yield Curve) continue to render correctly.

## Blocked by

- [08-fred-api-fallback.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/08-fred-api-fallback.md) — uses the FRED API/CSV fallback layer
