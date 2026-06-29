Status: completed

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Fetch the 11 SPDR sector ETFs (XLK, XLF, XLI, XLV, XLY, XLP, XLE, XLU, XLC, XLRE, XLB) via yfinance and compute two visualizations: (1) a sector MA breadth metric counting how many sectors are above their 200-day MA, and (2) a performance heatmap showing 1-week, 1-month, and 3-month returns for each sector.

Write both datasets to the JSON contract. Render a horizontal bar chart (green/red per sector) for the MA breadth and a heatmap grid for the performance data in the "Market Breadth" tab. Add a scorecard entry that evaluates healthy when ≥8 of 11 sectors are above their 200-day MA.

## Acceptance criteria

- [x] Python script fetches 1 year of daily closing prices for all 11 SPDR sector ETFs via `yfinance`.
- [x] Script computes the 200-day SMA for each sector and determines whether each is currently above or below.
- [x] Script computes 1-week, 1-month, and 3-month returns for each sector.
- [x] Sector leadership data is written to `indicators.sector_leadership` as `{above_200d, total, sectors: [{name, above}]}`.
- [x] Heatmap data is written to `indicators.sector_heatmap` as `[{sector, 1w, 1m, 3m}]`.
- [x] Scorecard entry for `sector_leadership` evaluates healthy when ≥8 of 11 sectors are above their 200-day MA.
- [x] UI renders a horizontal bar chart in the "Market Breadth" tab with each sector colored green (above MA) or red (below MA).
- [x] UI renders a secondary heatmap grid showing sector returns across 1W, 1M, 3M time windows with a green-to-red color scale.
- [x] Tooltips explain that narrow leadership (few sectors above MA) often precedes market weakness.

## Blocked by

None — can start immediately
