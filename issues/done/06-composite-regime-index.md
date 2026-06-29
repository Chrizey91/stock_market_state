Status: ready-for-agent

## Parent

[PRD.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD.md)

## What to build

Implement the mathematical formula to combine our collected indicators into a single, normalized, weighted **Market Regime Index** (0 to 100) representing general market risk conditions. Build the top hero section of the UI to showcase this score in a large, interactive radial gauge alongside summary cards for key indicator values.

## Acceptance criteria

- [ ] Python script normalizes the collected raw metrics (VIX, Yield Spread, HY Spread, S&P 500 Breadth, and M2 Growth) to a standardized 0-100 scale (where 100 is optimal/Risk-On and 0 is high stress/Risk-Off).
- [ ] Script computes a weighted average of these normalized values to produce the final daily composite Market Regime Index score.
- [ ] The current score is written to `data/market_data.json` along with its historical timeline.
- [ ] UI hero section displays a large radial gauge chart (via ApexCharts) showing the current composite score (with visual color indicators ranging from deep red for panic to bright green for healthy expansion).
- [ ] Hero section displays three sidebar summary cards summarizing:
  - Volatility Status (VIX and category)
  - Bond Market Status (10Y-2Y spread inversion state)
  - Retail Sentiment (Fear & Greed index zone)
- [ ] Responsive grid rearranges the hero section layout cleanly for mobile/tablet screens.

## Blocked by

- [02-macro-yields.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/.scratch/market-dashboard/issues/02-macro-yields.md)
- [03-economic-credit-internals.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/.scratch/market-dashboard/issues/03-economic-credit-internals.md)
- [04-market-breadth.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/.scratch/market-dashboard/issues/04-market-breadth.md)
- [05-sentiment-scrapes.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/.scratch/market-dashboard/issues/05-sentiment-scrapes.md)
