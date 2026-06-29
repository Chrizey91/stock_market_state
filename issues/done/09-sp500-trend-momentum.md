Status: completed

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Fetch S&P 500 index price data (`^GSPC`) and compute the 50-day and 200-day simple moving averages. Write the price and MA time series to the JSON data contract. Create the new "Price & Trend" tab in the UI and render a chart showing the S&P 500 close price with 50-day and 200-day MA overlays. Add two scorecard metric entries: one for whether the price is above the 200-day MA (Trend), and one for whether the 50-day MA is above the 200-day MA (Momentum / Golden Cross).

## Acceptance criteria

- [x] Python script fetches 1 year of daily `^GSPC` closing prices via `yfinance`.
- [x] Script computes 50-day and 200-day SMAs from the fetched data (fetching additional history as needed for the 200-day window).
- [x] Data is written to `indicators.sp500_trend` in the JSON contract as an array of `{date, value, ma50, ma200}`.
- [x] Scorecard entries for `sp500_trend` (Above/Below 200-day MA) and `sp500_momentum` (Golden Cross / Death Cross) are computed with correct thresholds.
- [x] A new "Price & Trend" tab is added to the UI.
- [x] A line chart renders the S&P 500 close price with 50-day and 200-day MA overlaid, using distinct colors and a legend.
- [x] Educational tooltips explain the significance of the 200-day MA and Golden/Death Cross patterns.

## Blocked by

None — can start immediately
