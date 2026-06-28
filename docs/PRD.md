Status: ready-for-agent

# Product Requirements Document (PRD) - Stock Market Indicators Dashboard

## Problem Statement

As a long-term, ETF-oriented investor, the user needs a clean, modern, high-level overview of the stock market based on key macroeconomic, sentiment, and liquidity indicators. Existing market dashboards are typically noisy, filled with short-term day-trading chatter, require paid subscriptions, or require setting up complex API keys that are difficult to manage securely on static web hosts. The user needs a simple, reliable, and visually stunning dashboard that runs for free on GitHub Pages and highlights the fundamental drivers of long-term cycles.

## Solution

We will build a static client-side dashboard deployable to GitHub Pages. 
1. A Python-based data collection script will run daily via GitHub Actions. It will retrieve all indicators from public, keyless data streams (FRED and Yahoo Finance), process them, calculate a composite **Market Regime Index**, and commit the output to a static `data/market_data.json` file in the repository.
2. The frontend will be a single-page application built with vanilla HTML, vanilla CSS (using modern CSS variables, responsive design, and glassmorphism styling), and vanilla JavaScript. It will load ApexCharts via CDN to render interactive, animated charts without a compile-time build step.
3. The dashboard will categorize the 10 core indicators into distinct tabs and display an overall market sentiment dial in the hero section.

## User Stories

1. As an ETF-oriented investor, I want a composite **Market Regime Index** score (0–100) presented in a radial gauge, so that I can immediately tell if the market environment is currently Risk-On or Risk-Off.
2. As a user, I want the dashboard to load a dark-themed visual interface, so that it looks professional, modern, and is comfortable to read.
3. As a user, I want indicators grouped into clear tabs (Sentiment & Volatility, Monetary & Liquidity, Economy & Internals), so that I can easily browse related indicators together.
4. As a user, I want interactive charts, so that I can hover over data points to inspect precise values and timestamps.
5. As a user, I want an educational tooltip next to each indicator, so that I can understand what the metric is and how to interpret it for my investments.
6. As a user, I want the system to update automatically daily after the market close, so that I don't have to manually pull data or trigger updates.
7. As a developer, I want the data scraping pipeline to run without API keys, so that the project has zero maintenance costs, no API signup overhead, and is fully forkable.
8. As a developer, I want the data collector to gracefully fall back to the last known historical values if a site scrape (e.g., CNN or OpenInsider) fails, so that a temporary external outage does not break the entire build pipeline or dashboard.
9. As a mobile user, I want the layout to be fully responsive, so that I can check the market state on my phone or tablet.
10. As a user, I want to see the last update timestamp, so that I can verify the currency and freshness of the displayed data.
11. As a user, I want to see up to 5 years of historical data for macro indicators (rates, M2, spreads) and 1 year for sentiment/internal indicators, so that I can analyze current trends in the context of historical cycles.

## Implementation Decisions

### Modules and Architecture
- **Data Scraping Pipeline (`update_data.py`)**: Written in Python. Scheduled to run daily via GitHub Actions. It reads the existing output JSON to carry over previous states, fetches new values from public endpoints, recalculates the indicators, and outputs a formatted JSON.
- **Frontend Dashboard (`index.html`, `style.css`, `app.js`)**: Static web files. Zero build step. Uses ApexCharts for rendering.
- **Continuous Integration Workflow (`update_data.yml`)**: GitHub Actions runner configured to run Python, install dependencies (`yfinance`, `beautifulsoup4`, `requests`), execute the script, and commit changes back to the repo.

### Technical & Design Specifications
- **No API Keys**: All inputs are sourced from public downloads:
  - FRED data series (`FEDFUNDS`, `T10Y2Y`, `DGS10`, `NAPM`, `BAMLH0A0HYM2`, `M2SL`) fetched via keyless CSV graph exports.
  - VIX and S&P 500 prices fetched via the `yfinance` package.
  - S&P 500 component tickers sourced from Wikipedia, then batch-calculated for their 200-day moving average.
  - Sentiment sourced via simulated CNN Fear & Greed endpoints and OpenInsider HTML scrapes.
- **Market Regime Index**: A weighted index combining:
  - Liquidity (M2 Growth)
  - Market Breadth (% of S&P 500 stocks above 200-day MA)
  - Credit Spread (High Yield Credit Spread)
  - Volatility (VIX)
  Normalizing each of these into a 0-100 range and averaging them with defined weights to represent an overall score (higher = healthier/risk-on, lower = stress/risk-off).
- **Data Contract (`market_data.json`)**:
  ```json
  {
    "last_updated": "2026-06-28T20:00:00Z",
    "market_regime_score": 68,
    "indicators": {
      "vix": [{"date": "2026-06-28", "value": 14.5}],
      "fear_greed": [{"date": "2026-06-28", "value": 55}],
      "yield_curve": [{"date": "2026-06-28", "value": -0.15}]
      // ...other indicators
    }
  }
  ```

## Testing Decisions

- **Automated Verification**:
  - Run the Python update script in the CI pipeline or local environment and check if a valid, schema-compliant `market_data.json` is generated.
  - Verify that if a fetch fails, the script uses the previous day's JSON data as a fallback instead of throwing an unhandled exception.
- **Manual Verification**:
  - Host a local server and test the web dashboard in multiple browser sizes.
  - Verify that tab selection changes visible charts instantly.
  - Hover over charts to confirm tooltip positioning and values are correct.

## Out of Scope

- Real-time / intraday streaming data updates (only daily updates are supported).
- Personal portfolio syncing or custom stock tracking.
- Interactive user settings (like customizable weights for the regime index).
- Authentication or server-side user data persistence.
