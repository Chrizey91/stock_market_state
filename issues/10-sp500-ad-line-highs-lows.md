Status: ready-for-agent

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Extend the existing S&P 500 component download (already fetched for breadth calculation) to compute two additional metrics: an S&P 500-scoped Advance-Decline Line and a daily count of 52-week Highs vs. Lows. Write both to the JSON data contract and render charts in the "Market Breadth" tab. Add a scorecard entry for the A/D Line (healthy when 20-day slope is positive).

These are S&P 500-only proxies, not NYSE-wide. They must be labeled as "S&P 500 Advance-Decline" and "S&P 500 New Highs/Lows" in the UI.

## Acceptance criteria

- [ ] Python script computes a daily cumulative Advance-Decline value from the existing S&P 500 component closing prices (advancers minus decliners each day, cumulated).
- [ ] Script computes daily counts of S&P 500 stocks making 52-week highs and 52-week lows.
- [ ] A/D data is written to `indicators.sp500_ad_line` as `{date, value}`.
- [ ] Highs/Lows data is written to `indicators.sp500_new_highs_lows` as `{date, highs, lows}`.
- [ ] Scorecard entry for `sp500_ad_line` evaluates whether the 20-day slope of the A/D line is positive.
- [ ] UI renders the A/D Line chart and a dual-bar or area chart for Highs vs. Lows in the "Market Breadth" tab.
- [ ] Charts are labeled "S&P 500 Advance-Decline" and "S&P 500 New Highs/Lows" (not NYSE-wide).
- [ ] Tooltips explain that a rising A/D line diverging from a falling index is a warning signal.

## Blocked by

None — reuses the existing S&P 500 component download from the breadth calculation
