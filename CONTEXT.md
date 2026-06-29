# Domain Glossary

## Indicator
A single time-series metric fetched from an external data source (e.g., VIX, Fed Funds Rate, ISM PMI). Stored as an array of `{date, value}` objects under `indicators.<key>` in the data contract.

## Health Scorecard
A table of 12 scorecard metrics, each evaluated against a concrete threshold to produce a healthy/unhealthy/unavailable status. Computed in Python and written to `market_data.json`. The scorecard is the primary summary view in the dashboard hero section.

## Scorecard Metric
A single row in the Health Scorecard. Each has an `id`, `label`, `category`, `status` (healthy | unhealthy | unavailable), and a display `value`. A metric is "unavailable" when its data source requires an API key that is not configured.

## Health Score
The count of scorecard metrics with status "healthy" divided by the count of metrics with status "healthy" or "unhealthy" (excluding "unavailable"). Expressed as a percentage (0–100) and displayed in the radial gauge.

## Market Regime Index
Legacy name for the composite health score. In Phase 1, this was a weighted average of 4 normalized indicators. In Phase 2, it is replaced by the Health Score derived from the 12-metric scorecard.

## Layered Fallback
The data pipeline's strategy for handling missing API keys:
- **FRED data**: Try the FRED API first; if `FRED_API_KEY` is absent, fall back to keyless CSV scraping.
- **Gated APIs** (FMP, Nasdaq Data Link): Skip gracefully — log a warning, return empty data, and mark the corresponding scorecard metrics as "unavailable."

## Sector Leadership
A breadth metric measuring how many of the 11 SPDR sector ETFs (XLK, XLF, XLI, XLV, XLY, XLP, XLE, XLU, XLC, XLRE, XLB) are trading above their own 200-day moving average. Healthy threshold: ≥8 of 11.

## S&P 500 A/D Line (Advance-Decline)
A proxy for the traditional NYSE Advance-Decline Line, computed exclusively from S&P 500 component stocks. Measures the cumulative difference between the number of advancing and declining S&P 500 constituents each trading day. Labeled as "S&P 500 Advance-Decline" in the UI to avoid confusion with the broader NYSE metric.

## S&P 500 New Highs/Lows
Count of S&P 500 component stocks making 52-week highs vs. 52-week lows. Also an S&P 500-scoped proxy, labeled accordingly.

## Equal-Weight vs Cap-Weight Spread
The difference in 3-month returns between the S&P 500 Equal Weight ETF (RSP) and the S&P 500 ETF (SPY). A spread beyond ±5% signals dangerous market concentration. Healthy threshold: within ±5%.
