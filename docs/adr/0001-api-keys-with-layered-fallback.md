# ADR 0001: Introduce Free-Tier API Keys with Layered Fallback

**Date**: 2026-06-29
**Status**: Accepted

## Context

The Phase 1 PRD established a hard constraint: "No API Keys." All data was fetched from keyless public endpoints (FRED CSV exports, yfinance, web scraping). This made the project zero-maintenance and fully forkable.

Phase 2 adds indicators that have no keyless public source: S&P 500 aggregate earnings (EPS, Revenue) from Financial Modeling Prep, and the Shiller CAPE Ratio from Nasdaq Data Link. Additionally, the FRED API (which requires a free key) is faster and more reliable than the keyless CSV scraping currently used.

## Decision

Allow free-tier API keys, stored as GitHub Actions secrets, with a **layered fallback** strategy:

1. **FRED data**: Try the `FRED_API_KEY` first. If the key is absent, fall back to the existing keyless CSV scraping. No data is lost — the dashboard works identically either way.
2. **FMP data** (`FMP_API_KEY`): If the key is absent, skip those indicators gracefully. Log a warning. The corresponding scorecard metrics are marked "unavailable" and excluded from the Health Score denominator.
3. **Nasdaq Data Link data** (`NASDAQ_DATA_LINK_API_KEY`): Same graceful-skip behavior as FMP.

Required secrets and setup instructions are documented in the project README.

## Alternatives Considered

- **Keep the "no keys" constraint**: Would block all earnings and valuation indicators entirely. The Health Scorecard would be missing its "Fundamentals & Valuation" layer, which the design doc identifies as "arguably most important."
- **Hard-fail if keys are missing**: Would break forkability — the original design principle that made the project attractive.

## Consequences

- The project remains fully forkable. A fork without API keys gets a working dashboard with ~8 of 12 scorecard metrics.
- A configured deployment gets the full 12-metric scorecard.
- Three environment variables / GitHub secrets must be documented and maintained.
- Two code paths exist for FRED data (API vs. CSV fallback), increasing maintenance surface slightly.
