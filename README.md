# Stock Market Indicators Dashboard

A clean, modern, high-level overview of the stock market based on key macroeconomic, sentiment, and liquidity indicators.

## Running Locally

1. Install Python dependencies:
   ```bash
   poetry install
   ```
2. Update market data:
   ```bash
   poetry run python scripts/update_data.py
   ```
3. Run local server:
   ```bash
   python -m http.server 8000
   ```
