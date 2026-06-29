Status: completed

## Parent

[PRD.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD.md)

## What to build

Retrieve S&P 500 component tickers, batch download their historical price data, calculate the percentage of stocks trading above their 200-day simple moving average (SMA) for each day over the past year, and render this market breadth indicator in the UI.

To prevent rate limiting, the script must query the tickers in batch groups rather than making 500 separate API calls.

## Acceptance criteria

- [x] Python script fetches the list of active S&P 500 tickers by parsing the Wikipedia article "List of S&P 500 companies".
- [x] Script uses `yfinance.download()` in batch mode to retrieve the last ~300 trading days of closing prices for all tickers in a single or small number of multi-ticker requests.
- [x] For each business day in the last 1 year, the script calculates the 200-day SMA for each stock and computes the percentage of stocks whose close is greater than their 200-day SMA.
- [x] The breadth time series is saved under the `sp500_breadth` field in the JSON file.
- [x] UI renders the S&P 500 Breadth chart under the "Economy & Internals" tab.
- [x] Educational tooltips note that values > 70% indicate broad-based bullish support, while values < 30% suggest major capitulation or severe weakness.

## Blocked by

- [01-core-shell-and-vix.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/.scratch/market-dashboard/issues/01-core-shell-and-vix.md)
