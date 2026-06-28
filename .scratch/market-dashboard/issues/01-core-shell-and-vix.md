Status: ready-for-agent

## Parent

[PRD.md](file:///c:/Users/c_jue/OneDrive/Dokumente/Personal/projects/stock_market_state/docs/PRD.md)

## What to build

Scaffold the initial repository structure for both the data pipeline and frontend code. Initialize Poetry to manage Python dependencies, build the first end-to-end tracer bullet that retrieves volatility data (VIX) using Poetry, saves it to a static JSON file, and displays it in a responsive dark-themed dashboard shell using ApexCharts.

This slice establishes the fundamental pipeline architecture.

## Acceptance criteria

- [ ] Project directory structure is created with a `pyproject.toml` configuration mapping dependencies (`requests`, `yfinance`, `beautifulsoup4`, `lxml`), `scripts/update_data.py`, and frontend files `index.html`, `style.css`, and `app.js`.
- [ ] Dependencies install cleanly via `poetry install`.
- [ ] Running the Python script via `poetry run python scripts/update_data.py` retrieves historical VIX data (`^VIX` index via `yfinance`) and outputs a structured `data/market_data.json` containing the data points and a `last_updated` timestamp.
- [ ] The dashboard `index.html` loads the JSON file dynamically.
- [ ] The dashboard UI has a modern, premium dark-themed layout (slate/zinc styling) with ApexCharts loaded via CDN.
- [ ] A line chart for the VIX index is rendered on the page, showing historical data with interactive tooltips and entry animations.
- [ ] The page can be viewed locally without any node compile/build steps (e.g., using a simple HTTP server).

## Blocked by

None - can start immediately
