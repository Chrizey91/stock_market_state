Status: ready-for-agent

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Reorganize the dashboard from 3 tabs (Sentiment & Volatility, Monetary & Liquidity, Economy & Internals) to 5 tabs (Price & Trend, Market Breadth, Fundamentals & Valuation, Credit & Liquidity, Sentiment). Move all existing charts to their new tab locations and integrate the new charts created by previous issues. Ensure the responsive layout works on mobile and tablet screens.

This is a pure UI restructuring issue — all indicator data and charts should already exist from prior issues.

## Acceptance criteria

- [ ] Tab bar displays 5 tabs: "Price & Trend", "Market Breadth", "Fundamentals & Valuation", "Credit & Liquidity", "Sentiment".
- [ ] **Price & Trend** tab contains: S&P 500 vs 200-day MA chart, VIX chart, Equal-Weight vs Cap-Weight chart.
- [ ] **Market Breadth** tab contains: % above 200-day MA chart, S&P 500 A/D Line chart, New Highs vs Lows chart, Sector Leadership bar chart, Sector Performance heatmap.
- [ ] **Fundamentals & Valuation** tab contains: EPS Growth chart, Revenue Growth chart, Forward P/E chart, CAPE Ratio chart (with "Configure API key" placeholders if data is unavailable).
- [ ] **Credit & Liquidity** tab contains: HY Spread, IG Spread, M2 Growth, Fed Balance Sheet, Fed Funds Rate, 10Y Treasury, Yield Curve charts.
- [ ] **Sentiment** tab contains: Fear & Greed Index chart, Insider Buy/Sell Ratio chart.
- [ ] Tab switching works correctly — selecting a tab shows only its charts.
- [ ] Responsive layout: tabs wrap or scroll horizontally on small screens, charts stack vertically on mobile.
- [ ] No existing chart functionality is broken during the reorganization.

## Blocked by

- [09-sp500-trend-momentum.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/09-sp500-trend-momentum.md)
- [10-sp500-ad-line-highs-lows.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/10-sp500-ad-line-highs-lows.md)
- [11-equal-vs-cap-weight.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/11-equal-vs-cap-weight.md)
- [12-sector-leadership-heatmap.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/12-sector-leadership-heatmap.md)
