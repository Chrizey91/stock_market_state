Status: completed

## Parent

[PRD.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD.md)

## What to build

Implement web scraping logic to collect market sentiment indices. Fetch the CNN Fear & Greed Index and compute the Insider Buying vs. Selling Ratio by parsing transaction data from OpenInsider. Output these datasets to the JSON file and visualize them under the "Sentiment & Volatility" tab.

## Acceptance criteria

- [x] Python script scrapes CNN's public JSON endpoint (`https://production.dataviz.cnn.io/index/fearandgreed/current`) using custom headers (browser spoofing) to get the latest Fear & Greed Index score.
- [x] Python script scrapes OpenInsider's cluster transaction tables (e.g., `http://openinsider.com/`) to extract the sum of insider buying vs. selling transactions for the recent month, calculating the Buy-to-Sell transaction ratio.
- [x] Historical records for both sentiment metrics are populated in the JSON output.
- [x] Tabbed UI renders the Fear & Greed timeline and the Insider Buying/Selling ratio timeline under the "Sentiment & Volatility" tab.
- [x] Tooltips describe market sentiment zones (e.g., Fear & Greed values < 25 represent extreme fear, and insider buying spikes represent corporate confidence).

## Blocked by

- [01-core-shell-and-vix.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/.scratch/market-dashboard/issues/01-core-shell-and-vix.md)
