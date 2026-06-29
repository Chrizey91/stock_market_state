Status: ready-for-agent

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Implement the `evaluate_scorecard()` function in Python that takes all indicator data and produces the 12-metric Health Scorecard array with healthy/unhealthy/unavailable status per metric. Compute `health_score` (count of healthy) and `health_total` (count of healthy + unhealthy, excluding unavailable). Write these to the JSON data contract, replacing the legacy `market_regime_score`.

Redesign the hero section to display both the scorecard table (12 rows with green/red/amber status dots) and the radial gauge (now driven by `health_score / health_total × 100`). The gauge replaces the legacy Market Regime Index gauge.

## Acceptance criteria

- [ ] Python function `evaluate_scorecard(indicators)` evaluates all 12 metrics against their defined thresholds and returns a scorecard array.
- [ ] Each scorecard entry has `id`, `label`, `category`, `status` (healthy | unhealthy | unavailable), and `value`.
- [ ] Metrics with empty/missing indicator data are marked "unavailable".
- [ ] `health_score` counts metrics with status "healthy".
- [ ] `health_total` counts metrics with status "healthy" or "unhealthy" (excludes "unavailable").
- [ ] JSON contract includes `scorecard`, `health_score`, and `health_total` at the top level.
- [ ] Hero section displays a compact scorecard table with colored status indicators (green dot = healthy, red dot = unhealthy, grey dot = unavailable).
- [ ] Hero section displays a radial gauge showing `health_score / health_total × 100` as a percentage.
- [ ] The legacy `market_regime_score` field is retained for backward compatibility but the gauge displays the new Health Score.
- [ ] Scorecard table and gauge are responsive on mobile screens.
- [ ] Unit tests verify `evaluate_scorecard()` with synthetic data: all healthy, all unhealthy, mixed, and various "unavailable" combinations.
- [ ] Tests verify `health_score` and `health_total` are correct when some metrics are unavailable.

## Blocked by

- [09-sp500-trend-momentum.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/09-sp500-trend-momentum.md)
- [10-sp500-ad-line-highs-lows.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/10-sp500-ad-line-highs-lows.md)
- [11-equal-vs-cap-weight.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/11-equal-vs-cap-weight.md)
- [12-sector-leadership-heatmap.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/12-sector-leadership-heatmap.md)
- [13-sp500-earnings-fmp.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/13-sp500-earnings-fmp.md)
- [14-valuation-pe-cape.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/14-valuation-pe-cape.md)
- [15-fred-liquidity-credit.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/15-fred-liquidity-credit.md)
- [16-ui-tab-reorganization.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/issues/16-ui-tab-reorganization.md)
