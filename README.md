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

## API Configuration (Layered Fallback)

To enable the full S&P 500 Health Scorecard and macroeconomic indicators, configure the following optional free-tier API keys. If a key is missing, the data pipeline falls back gracefully (either scraping keyless public endpoints or skipping the metric) so the dashboard remains fully functional.

| Environment Variable / GitHub Secret | Provider | Free-Tier Signup Link | Fallback Behavior if Absent |
| :--- | :--- | :--- | :--- |
| `FRED_API_KEY` | St. Louis Fed (FRED) | [FRED API Keys](https://fredaccount.stlouisfed.org/apikeys) | Falls back to keyless CSV scraping exports (no data lost). |
| `FMP_API_KEY` | Financial Modeling Prep | [FMP Developer Portal](https://site.financialmodelingprep.com/register) | Gracefully skips earnings growth and forward P/E metrics. |
| `NASDAQ_DATA_LINK_API_KEY` | Nasdaq Data Link | [Nasdaq Data Link Sign Up](https://data.nasdaq.com/sign-up) | Gracefully skips the Shiller CAPE Ratio metric. |

### Setup Instructions

#### Local Development
Create a `.env` file or export the variables in your shell before running the update script:
```bash
export FRED_API_KEY="your_fred_api_key"
export FMP_API_KEY="your_fmp_api_key"
export NASDAQ_DATA_LINK_API_KEY="your_nasdaq_data_link_api_key"
```

#### GitHub Actions Deployment
1. Navigate to your repository on GitHub.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Add each secret with the exact name listed above and paste your API key as the value.

