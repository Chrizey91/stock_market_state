Status: completed

## Parent

[PRD.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD.md)

## What to build

Extend the Python data pipeline and frontend interface to integrate primary interest rate and treasury yield indicators. Fetch key macroeconomic indicators from FRED public CSV endpoints, write them to the JSON contract, and implement a functional tabbed layout in the UI to display them in the newly created "Monetary & Liquidity" section.

## Acceptance criteria

- [x] Python script fetches 5 years of historical data for the Fed Funds Rate (`FEDFUNDS`), 10-Year Treasury Yield (`DGS10`), and the 10-Year vs 2-Year Treasury Spread (`T10Y2Y`) via public, keyless FRED CSV graph URLs.
- [x] Script aggregates this new data into `data/market_data.json` without breaking the VIX data structure.
- [x] UI features a functional tab navigation bar (Sentiment & Volatility, Monetary & Liquidity, Economy & Internals).
- [x] Selecting the "Monetary & Liquidity" tab reveals line/area charts for the three macroeconomic indicators.
- [x] Each chart includes educational tooltips explaining the series (e.g. interpreting a negative 10Y-2Y spread as a yield curve inversion).

## Blocked by

- [01-core-shell-and-vix.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/.scratch/market-dashboard/issues/01-core-shell-and-vix.md)
