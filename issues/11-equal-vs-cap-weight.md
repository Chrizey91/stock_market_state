Status: ready-for-agent

## Parent

[PRD_phase2.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD_phase2.md)

## What to build

Fetch the S&P 500 Equal Weight ETF (`RSP`) and the S&P 500 ETF (`SPY`) via yfinance, compute their rolling 3-month returns, and calculate the performance spread. Write the comparison data to the JSON contract and render a dual-line chart showing both ETF returns with the spread highlighted. Add a scorecard entry that evaluates whether the 3-month spread is within ±5%.

## Acceptance criteria

- [ ] Python script fetches 1 year of daily closing prices for `RSP` and `SPY` via `yfinance`.
- [ ] Script computes rolling 3-month (63 trading days) returns for both ETFs.
- [ ] Data is written to `indicators.equal_vs_cap_weight` as `{date, rsp_return, spy_return, spread}`.
- [ ] Scorecard entry for `equal_vs_cap_weight` evaluates healthy when the latest spread is within ±5%.
- [ ] UI renders a dual-line chart in the "Price & Trend" tab showing RSP and SPY 3-month returns, with the spread area shaded.
- [ ] Educational tooltip explains that a large negative spread (RSP lagging SPY) indicates dangerous market concentration in mega-cap stocks.

## Blocked by

None — can start immediately
