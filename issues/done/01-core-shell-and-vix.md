Status: completed

## Parent

[PRD.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD.md)

## What to build

Scaffold the initial repository structure for both the data pipeline and frontend code. Build the first end-to-end tracer bullet that retrieves volatility data (VIX), saves it to a static JSON file, and displays it in a responsive dark-themed dashboard shell using ApexCharts.

This slice establishes the fundamental pipeline architecture.

## Acceptance criteria

- [x] Project directory structure is created with `scripts/update_data.py` and frontend files `index.html`, `style.css`, and `app.js`.
- [x] Running the Python script retrieves historical VIX data (`^VIX` index via `yfinance`) and outputs a structured `data/market_data.json` containing the data points and a `last_updated` timestamp.
- [x] The dashboard `index.html` loads the JSON file dynamically.
- [x] The dashboard UI has a modern, premium dark-themed layout (slate/zinc styling) with ApexCharts loaded via CDN.
- [x] A line chart for the VIX index is rendered on the page, showing historical data with interactive tooltips and entry animations.
- [x] The page can be viewed locally without any node compile/build steps (e.g., using a simple HTTP server).

## Blocked by

None - can start immediately
