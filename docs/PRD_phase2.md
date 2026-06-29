Status: ready-for-agent

# Phase 2 — S&P 500 Health Scorecard

## Problem Statement

The existing Stock Market Indicators Dashboard provides a useful overview of 10 macroeconomic and sentiment indicators, but it answers a general "is the market stressed?" question rather than the specific question a long-term ETF investor actually asks: **"Is the S&P 500 healthy?"**

The current Market Regime Index is computed from only 4 inputs (VIX, HY Spread, M2 Growth, Breadth), missing critical dimensions of market health: price trend, earnings fundamentals, valuation, and sector leadership. The dashboard also enforces a hard "no API keys" constraint that blocks access to freely available earnings and valuation data, leaving the Fundamentals & Valuation layer — arguably the most important for long-term investors — entirely absent.

## Solution

Expand the dashboard with a **12-metric Health Scorecard** that evaluates S&P 500 health across four layers: Price Health, Participation, Fundamental Health, and Valuation. Each metric is evaluated against a concrete threshold and displayed as a pass/fail row in a scorecard table in the hero section, alongside a radial gauge showing the overall Health Score (healthy count / available count × 100).

The data pipeline is extended with three free-tier API keys (FRED, Financial Modeling Prep, Nasdaq Data Link) using a **layered fallback** strategy: FRED data falls back to keyless CSV scraping if the key is absent; FMP and Nasdaq Data Link indicators are skipped gracefully with "unavailable" status. The dashboard remains fully forkable — a fork without keys still gets ~8 of 12 scorecard metrics.

The UI is reorganized from 3 tabs to 5 tabs aligned with the four-layer framework plus a sentiment section.

## User Stories

1. As an ETF investor, I want a Health Scorecard showing 12 pass/fail metrics at a glance, so that I can immediately see which dimensions of the S&P 500 are healthy and which are flashing warnings.
2. As an ETF investor, I want a radial gauge showing the overall Health Score (e.g., "9 of 12 healthy"), so that I get a single-number summary of market conditions.
3. As a user, I want to see whether the S&P 500 is above or below its 200-day moving average, so that I can assess the long-term price trend.
4. As a user, I want to see whether the 50-day MA is above or below the 200-day MA (Golden Cross / Death Cross), so that I can assess momentum direction.
5. As a user, I want to see the S&P 500 Advance-Decline Line computed from S&P 500 components, so that I can detect divergences between the index and underlying participation.
6. As a user, I want to see the count of S&P 500 stocks making 52-week highs vs. 52-week lows, so that I can assess internal market health.
7. As a user, I want to compare Equal-Weight (RSP) vs. Cap-Weight (SPY) S&P 500 performance, so that I can detect dangerous market concentration in a few mega-cap stocks.
8. As a user, I want to see S&P 500 aggregate EPS growth (year-over-year), so that I can assess whether corporate earnings are expanding.
9. As a user, I want to see S&P 500 aggregate revenue growth (year-over-year), so that I can assess top-line growth which is harder to manipulate than earnings.
10. As a user, I want to see the S&P 500 Forward P/E ratio, so that I can judge whether the market is fairly valued relative to expected earnings.
11. As a user, I want to see the Shiller CAPE ratio as a supplementary valuation chart, so that I can gauge long-term valuation context.
12. As a user, I want to see which of the 11 SPDR sector ETFs are above their 200-day MA, so that I can assess whether market leadership is broad or narrow.
13. As a user, I want a sector performance heatmap showing returns across multiple time windows (1W, 1M, 3M), so that I can spot sector rotation patterns.
14. As a user, I want the Investment Grade credit spread alongside the existing High Yield spread, so that I can get a fuller picture of credit market conditions.
15. As a user, I want to see the Fed Balance Sheet (WALCL) and Bank Lending (TOTLL) time series, so that I can monitor liquidity conditions beyond M2 alone.
16. As a user, I want scorecard metrics that depend on API keys to show a helpful "Configure API key to enable" message when the key is absent, so that I know what I'm missing and how to fix it.
17. As a user, I want the Health Score gauge to only count metrics that have data (excluding "unavailable" ones), so that a fork without API keys still shows a meaningful score like "7 of 7 healthy" rather than "7 of 12 healthy."
18. As a developer, I want the scorecard evaluation logic to live entirely in Python, so that there is a single source of truth for health thresholds with no business logic duplicated in JavaScript.
19. As a developer, I want the FRED data fetching to try the FRED API first and fall back to keyless CSV scraping if `FRED_API_KEY` is absent, so that existing functionality is never degraded.
20. As a developer, I want required GitHub secrets and setup instructions documented in the README, so that contributors know exactly which keys to add and where.
21. As a mobile user, I want the 5-tab layout and scorecard table to be fully responsive, so that I can check market health on my phone.
22. As a user, I want the tabs reorganized into 5 sections (Price & Trend, Market Breadth, Fundamentals & Valuation, Credit & Liquidity, Sentiment), so that indicators are grouped by the four-layer health framework.

## Implementation Decisions

### API Keys and Layered Fallback (ADR 0001)

Three free-tier API keys are introduced, stored as GitHub Actions secrets and documented in the README:

- `FRED_API_KEY` — FRED API (free, 120 req/min). Falls back to existing keyless CSV scraping if absent.
- `FMP_API_KEY` — Financial Modeling Prep (free, 250 req/day). Indicators skipped gracefully if absent.
- `NASDAQ_DATA_LINK_API_KEY` — Nasdaq Data Link (free, 50 req/day). Indicators skipped gracefully if absent.

When a gated API key is missing, the corresponding scorecard metrics are marked "unavailable" and excluded from the Health Score denominator. The frontend renders a subtle configuration hint in the chart card.

### Health Scorecard — Metrics and Thresholds

The scorecard is an array computed in Python and written to the JSON data contract. Each entry has `id`, `label`, `category`, `status` (healthy | unhealthy | unavailable), and a display `value`.

| # | ID | Category | Metric | Healthy Threshold | Source |
|---|---|---|---|---|---|
| 1 | `sp500_trend` | Trend | S&P 500 vs 200-day MA | Above | yfinance `^GSPC` |
| 2 | `sp500_momentum` | Momentum | 50-day vs 200-day MA | 50 > 200 (Golden Cross) | yfinance `^GSPC` |
| 3 | `sp500_breadth` | Breadth | % above 200-day MA | >70% | yfinance (existing) |
| 4 | `sp500_ad_line` | Breadth | S&P 500 A/D Line | 20-day slope positive | yfinance (computed) |
| 5 | `equal_vs_cap_weight` | Breadth | Equal-Weight vs Cap-Weight | 3-month spread within ±5% | yfinance RSP vs SPY |
| 6 | `eps_growth` | Earnings | S&P 500 EPS Growth | YoY > 0% | FMP API |
| 7 | `revenue_growth` | Earnings | S&P 500 Revenue Growth | YoY > 0% | FMP API |
| 8 | `forward_pe` | Valuation | Forward P/E | Between 14 and 22 | FMP API |
| 9 | `vix` | Volatility | VIX | ≤20 | yfinance (existing) |
| 10 | `hy_spread` | Credit | HY Credit Spread | <500 bps | FRED (existing) |
| 11 | `m2_growth` | Liquidity | M2 YoY Growth | ≥0% | FRED (existing) |
| 12 | `sector_leadership` | Leadership | Sector MA Breadth | ≥8/11 above 200-day MA | yfinance sector ETFs |

The CAPE Ratio is displayed as a supplementary chart under Fundamentals & Valuation but is NOT a scorecard row (it moves too slowly for weekly monitoring).

### Health Score Gauge

The radial gauge in the hero section displays `health_score / health_total × 100`. Only metrics with status "healthy" or "unhealthy" are counted in `health_total`; "unavailable" metrics are excluded.

### Data Contract Extension

```json
{
  "last_updated": "2026-06-29T22:00:00Z",
  "health_score": 9,
  "health_total": 12,
  "scorecard": [
    {"id": "sp500_trend", "label": "S&P 500 vs 200-day MA", "category": "Trend", "status": "healthy", "value": "Above"},
    {"id": "vix", "label": "VIX", "category": "Volatility", "status": "unhealthy", "value": 24.3},
    {"id": "eps_growth", "label": "EPS Growth", "category": "Earnings", "status": "unavailable", "value": null}
  ],
  "indicators": {
    "vix": [{"date": "...", "value": 14.5}],
    "sp500_trend": [{"date": "...", "value": 5200, "ma200": 5050}],
    "sp500_ad_line": [{"date": "...", "value": 142}],
    "sp500_new_highs_lows": [{"date": "...", "highs": 45, "lows": 12}],
    "equal_vs_cap_weight": [{"date": "...", "rsp_return": 4.2, "spy_return": 6.1, "spread": -1.9}],
    "sector_leadership": {"above_200d": 9, "total": 11, "sectors": [{"name": "XLK", "above": true}, ...]},
    "sector_heatmap": [{"sector": "XLK", "1w": 2.1, "1m": 5.3, "3m": 12.4}, ...],
    "eps_growth": [{"date": "...", "value": 8.5}],
    "revenue_growth": [{"date": "...", "value": 5.2}],
    "forward_pe": [{"date": "...", "value": 21.3}],
    "cape_ratio": [{"date": "...", "value": 33.1}],
    "ig_spread": [{"date": "...", "value": 1.2}],
    "fed_balance_sheet": [{"date": "...", "value": 7800000}],
    ...existing indicators...
  }
}
```

### Tab Structure (5 Tabs)

| Tab | Charts / Indicators |
|---|---|
| Price & Trend | S&P 500 vs 200-day MA, 50/200 MA cross, VIX, Equal-Weight vs Cap-Weight |
| Market Breadth | % above 200-day MA, S&P 500 A/D Line, New Highs vs Lows, Sector Leadership bar chart, Sector Performance heatmap |
| Fundamentals & Valuation | EPS Growth, Revenue Growth, Forward P/E, CAPE Ratio |
| Credit & Liquidity | HY Spread, IG Spread, M2 Growth, Fed Balance Sheet, Fed Funds Rate, 10Y Treasury, Yield Curve |
| Sentiment | Fear & Greed Index, Insider Buy/Sell Ratio |

### S&P 500-Scoped Proxies

The Advance-Decline Line and New Highs/Lows are computed exclusively from S&P 500 component stocks (data already fetched for breadth). These are proxies for the traditional NYSE-wide metrics and are labeled "S&P 500 Advance-Decline" and "S&P 500 New Highs/Lows" in the UI.

### Sector Leadership

Primary metric: count of 11 SPDR sector ETFs (XLK, XLF, XLI, XLV, XLY, XLP, XLE, XLU, XLC, XLRE, XLB) above their 200-day MA. Visualized as a horizontal bar chart colored green/red per sector.

Secondary visualization: performance heatmap grid (sector × time period: 1W, 1M, 3M returns).

### GitHub Actions Workflow

The workflow is extended to pass API keys from secrets as environment variables to the Python script. The script reads them via `os.environ.get()`.

## Testing Decisions

Tests verify external behavior through the public interface of the data pipeline module — the same seam used by existing tests.

### Scorecard Evaluation (Pure Functions)

Test `evaluate_scorecard(indicators)` with synthetic indicator data. Verify:
- Each threshold produces the correct healthy/unhealthy status.
- Missing indicator data produces "unavailable" status.
- `health_score` and `health_total` are computed correctly, excluding unavailable metrics.

Prior art: `test_regime.py` — tests pure normalisation functions with known inputs and expected outputs.

### New Fetchers

Test new fetch functions (FMP earnings, Nasdaq Data Link CAPE, sector ETFs, A/D computation) via `main()` with mocked network calls. Verify:
- Successful fetch writes correct data structure to the JSON output.
- Network failure triggers appropriate fallback (FRED → CSV; FMP/Nasdaq → graceful skip).
- Missing API key environment variable triggers graceful skip without error.

Prior art: `test_fallback.py` — mocks all fetch functions and verifies `main()` output.

### Layered FRED Fallback

Test that when `FRED_API_KEY` is absent, the existing CSV scraping path is used. Test that when `FRED_API_KEY` is present but the API returns an error, it falls back to CSV. Both paths should produce identical output structure.

## Out of Scope

- **Earnings Revisions**: No free data source for analyst estimate data.
- **ETF Fund Flows**: No free data source for inflow/outflow data.
- **Profit Margins**: Cut from the scorecard (could be revisited if FMP data supports it).
- **Real-time / intraday data**: Only daily updates are supported (unchanged from Phase 1).
- **Customizable thresholds**: Users cannot adjust what constitutes "healthy" (unchanged from Phase 1).
- **NYSE-wide Advance-Decline**: Only S&P 500-scoped proxy is implemented.

## Further Notes

- The Phase 1 Market Regime Index (`market_regime_score`) is superseded by the new Health Score (`health_score` / `health_total`). The old field may be retained for backward compatibility but the hero gauge should display the new Health Score.
- The CAPE Ratio is intentionally not a scorecard row because it moves too slowly (monthly data) to be useful for the weekly review cadence the scorecard targets.
- All domain terms used in this PRD are defined in `CONTEXT.md`. The API key decision is documented in `docs/adr/0001-api-keys-with-layered-fallback.md`.
