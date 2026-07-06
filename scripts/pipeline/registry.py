"""Orchestration loop and registry for the data pipeline.

Maintains the list of all indicators to fetch, and implements the main
refresh_all() orchestrator that calls each fetcher with fallback protection.
"""

import logging
from datetime import datetime, timezone

from .fallback import fetch_with_fallback
from .regime import calculate_market_regime_index
from .scorecard import evaluate_scorecard

logger = logging.getLogger(__name__)


def build_registry(config, df_sp500):
    """Build the registry of indicator fetchers.

    Args:
        config: PipelineConfig containing API keys.
        df_sp500: S&P 500 historical DataFrame (shared cache).

    Returns:
        List of dicts defining the fetch strategy for each indicator.
    """
    # Import adapters here to avoid circular imports if they need config
    from .adapters.fred import build_fred_fetchers
    from .adapters.fmp import build_fmp_fetchers
    from .adapters.sentiment import build_sentiment_fetchers
    from .adapters.sp500 import build_sp500_fetchers

    registry = []

    # S&P 500 Indicators (pass shared dataframe)
    registry.extend(build_sp500_fetchers(config, df_sp500))

    # FRED Indicators
    registry.extend(build_fred_fetchers(config))

    # Financial Modeling Prep Indicators
    registry.extend(build_fmp_fetchers(config))

    # Sentiment / Alternative Indicators
    registry.extend(build_sentiment_fetchers(config))

    return registry


def refresh_all(config, existing_data, df_sp500=None):
    """Main orchestration loop to update all market data.

    Args:
        config: PipelineConfig instance.
        existing_data: Dict of previously fetched market data.
        df_sp500: Pre-fetched S&P 500 historical data. If None, it will be fetched.

    Returns:
        Updated market data dict (JSON serializable).
    """
    if df_sp500 is None:
        from .adapters.sp500 import fetch_sp500_data
        df_sp500 = fetch_sp500_data()

    updated_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "indicators": {},
        "market_regime": [],
        "scorecard": [],
        "health_score": 0,
        "health_total": 0
    }

    existing_indicators = existing_data.get("indicators", {})
    registry = build_registry(config, df_sp500)

    for item in registry:
        mode = item.get("mode", "replace")

        if mode == "multi_output":
            # Special case for fetchers that return a tuple of data mapping to multiple keys
            keys = item["keys"]
            fetcher = item["fetcher"]
            try:
                results = fetcher()
                for key, data in zip(keys, results):
                    updated_data["indicators"][key] = data
            except Exception as e:
                logger.warning(f"Failed to fetch multi-output {keys}: {e}")
                for key in keys:
                    from .fallback import fallback_duplicate_last_value
                    updated_data["indicators"][key] = fallback_duplicate_last_value(
                        key, existing_indicators.get(key, [])
                    )
        else:
            # Standard replace or upsert
            key = item["key"]
            fetcher = item["fetcher"]
            logger.info(f"Processing indicator: {key} (mode={mode})")
            updated_data["indicators"][key] = fetch_with_fallback(
                fetcher, key, existing_indicators, mode=mode
            )

    # Recompute derived metrics
    updated_data["market_regime"] = calculate_market_regime_index(updated_data["indicators"])

    scorecard, h_score, h_total = evaluate_scorecard(updated_data["indicators"])
    updated_data["scorecard"] = scorecard
    updated_data["health_score"] = h_score
    updated_data["health_total"] = h_total

    return updated_data
