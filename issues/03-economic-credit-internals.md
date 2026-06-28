Status: ready-for-agent

## Parent

[PRD.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD.md)

## What to build

Integrate economic growth and credit market indicators into the scraping pipeline and user interface. Fetch the ISM Manufacturing PMI, High Yield Credit Spreads, and M2 Money Supply from keyless FRED feeds. Process M2 to compute year-over-year liquidity growth, write the series to JSON, and render the charts in the correct sections of the frontend tab hierarchy.

## Acceptance criteria

- [ ] Python script fetches 5 years of historical data for the ISM Manufacturing PMI (`NAPM`), High Yield Option-Adjusted Spread (`BAMLH0A0HYM2`), and M2 Money Supply (`M2SL`) from public FRED CSV endpoints.
- [ ] Script computes M2 Liquidity Growth as a Year-over-Year (YoY) percentage change from the raw monthly `M2SL` values.
- [ ] JSON contract is extended to include these three metrics.
- [ ] ISM PMI and High Yield Spread charts are displayed under the "Economy & Internals" tab.
- [ ] M2 Liquidity Growth chart is displayed under the "Monetary & Liquidity" tab.
- [ ] Charts feature explanatory overlays/tooltips detailing critical thresholds (e.g., PMI above 50 signals expansion, while widening High Yield spreads signal business distress).

## Blocked by

- [01-core-shell-and-vix.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/.scratch/market-dashboard/issues/01-core-shell-and-vix.md)
