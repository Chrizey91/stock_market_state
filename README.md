# Stock Market Indicators Dashboard

A clean, modern, high-level overview of the stock market based on key macroeconomic, sentiment, and liquidity indicators.

## Running Locally

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Configure API Keys (Optional but Recommended):**
   Create a `.env` file in the root directory and add your API keys (see [API Configuration](#api-configuration-layered-fallback) below for details):
   ```bash
   FRED_API_KEY="your_fred_api_key"
   FMP_API_KEY="your_fmp_api_key"
   NASDAQ_DATA_LINK_API_KEY="your_nasdaq_data_link_api_key"
   ```

3. **Fetch Market Data:**
   Run the backend pipeline to generate the latest `market_data.json`:
   ```bash
   poetry run python scripts/update_data.py
   ```

4. **Run Local Server:**
   Serve the static frontend files locally:
   ```bash
   python -m http.server 8000
   ```
   *Then open `http://localhost:8000` in your browser.*

5. **Run Tests:**
   Execute the test suite to ensure the data pipeline is functioning correctly:
   ```bash
   poetry run python -m unittest discover tests
   ```

## Architecture & Codebase

The backend data pipeline is built using a modular, "deep module" architecture, separating side-effects (fetching data) from pure logic (calculations).

The core logic lives in `scripts/pipeline/`:
- **`adapters/`**: Network interfaces for fetching data from yfinance, FRED, FMP, and CNN Fear & Greed.
- **`indicators.py`**: Pure calculation functions for market breadth, A/D lines, etc.
- **`regime.py`**: Calculates the overall market regime index based on yields and volatility.
- **`scorecard.py`**: Evaluates individual indicators against thresholds to compute a Health Scorecard.
- **`fallback.py`**: Provides robust fallback policies (e.g. duplicate last value) if APIs fail.
- **`registry.py`**: The central orchestrator that iterates through all adapters to build the final JSON.

`scripts/update_data.py` acts as a thin CLI wrapper around the pipeline package.

## API Configuration (Layered Fallback)

To enable the full S&P 500 Health Scorecard and macroeconomic indicators, configure the following optional free-tier API keys. If a key is missing, the data pipeline falls back gracefully (either scraping keyless public endpoints or skipping the metric) so the dashboard remains fully functional.

| Environment Variable / GitHub Secret | Provider | Free-Tier Signup Link | Fallback Behavior if Absent |
| :--- | :--- | :--- | :--- |
| `FRED_API_KEY` | St. Louis Fed (FRED) | [FRED API Keys](https://fredaccount.stlouisfed.org/apikeys) | Falls back to keyless CSV scraping exports (no data lost). |
| `FMP_API_KEY` | Financial Modeling Prep | [FMP Developer Portal](https://site.financialmodelingprep.com/register) | Gracefully skips earnings growth and forward P/E metrics. |
| `NASDAQ_DATA_LINK_API_KEY` | Nasdaq Data Link | [Nasdaq Data Link Sign Up](https://data.nasdaq.com/sign-up) | Gracefully skips the Shiller CAPE Ratio metric. |

### Setup Instructions

#### GitHub Actions Deployment
1. Navigate to your repository on GitHub.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Add each secret with the exact name listed above and paste your API key as the value.
