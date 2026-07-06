"""Financial Modeling Prep and Valuation adapters."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
import requests

from ..indicators import _quarter_key, _quarter_date_label, compute_yoy_growth

logger = logging.getLogger(__name__)


def fetch_sp500_earnings_fmp(api_key):
    """Fetch S&P 500 aggregate earnings via FMP's stable income-statement API.

    Strategy (free-tier friendly, ~30 API calls):
    1. Use a fixed list of the top-30 S&P 500 companies by market cap.
       These represent ~50% of the index weight and serve as a reliable proxy.
    2. For each company, call /stable/income-statement?period=quarter&limit=5
       to get the last 5 quarters of EPS and revenue data.
    3. Aggregate by calendar quarter (sum EPS, sum revenue).
    4. Compute YoY growth on the quarterly aggregates.
    """
    logger.info("Fetching S&P 500 aggregate earnings data from Financial Modeling Prep...")
    if not api_key:
        logger.warning("FMP_API_KEY is absent. Skipping FMP earnings.")
        return [], []

    # Top 30 S&P 500 companies by market cap
    TOP_30_TICKERS = [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "LLY", "AVGO",
        "JPM", "TSLA", "UNH", "XOM", "V", "MA", "COST", "PG",
        "JNJ", "HD", "ABBV", "WMT", "NFLX", "CRM", "BAC", "ORCL",
        "CVX", "MRK", "KO", "PEP", "AMD", "ADBE",
    ]

    try:
        all_records = []
        failed_count = 0

        for ticker in TOP_30_TICKERS:
            url = (
                f"https://financialmodelingprep.com/stable/income-statement"
                f"?symbol={ticker}&period=quarter&limit=5&apikey={api_key}"
            )
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 403:
                    logger.warning(f"FMP API returned 403 for {ticker}. Skipping all FMP earnings.")
                    return [], []
                if response.status_code == 402:
                    logger.warning(f"FMP API returned 402 (payment required) for {ticker}. Skipping ticker.")
                    continue
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        date_str = item.get("date")
                        eps = item.get("epsDiluted")
                        revenue = item.get("revenue")
                        if date_str and eps is not None and revenue is not None:
                            try:
                                all_records.append({
                                    "symbol": ticker,
                                    "date": datetime.strptime(date_str, '%Y-%m-%d'),
                                    "eps": float(eps),
                                    "revenue": float(revenue),
                                })
                            except (ValueError, TypeError):
                                continue
            except Exception as e:
                logger.warning(f"FMP: failed to fetch income statement for {ticker}: {e}")
                failed_count += 1
                if failed_count >= 5:
                    logger.warning("FMP: too many failures, aborting earnings fetch.")
                    return [], []

        logger.info(f"FMP: fetched {len(all_records)} quarterly records from {len(TOP_30_TICKERS)} companies.")

        if not all_records:
            logger.warning("FMP: no earnings records retrieved.")
            return [], []

        # Aggregate by calendar quarter (sum EPS, sum revenue)
        quarterly = defaultdict(lambda: {"eps": 0.0, "revenue": 0.0, "count": 0})
        for item in all_records:
            qk = _quarter_key(item["date"])
            quarterly[qk]["eps"] += item["eps"]
            quarterly[qk]["revenue"] += item["revenue"]
            quarterly[qk]["count"] += 1

        # Drop incomplete quarters (where fewer than half the median companies reported)
        counts = [v["count"] for v in quarterly.values()]
        median_count = sorted(counts)[len(counts) // 2] if counts else 0
        min_threshold = max(median_count // 2, 2)

        # Convert to sorted list for YoY calculation, skipping incomplete quarters
        quarterly_data = []
        for (year, quarter), vals in sorted(quarterly.items()):
            date_label = _quarter_date_label(year, quarter)
            if vals["count"] < min_threshold:
                logger.info(
                    f"  Q{quarter}/{year}: SKIPPED (only {vals['count']} companies, "
                    f"threshold={min_threshold})"
                )
                continue
            quarterly_data.append({
                "date": date_label,
                "eps": round(vals["eps"], 2),
                "revenue": round(vals["revenue"], 2),
            })
            logger.info(
                f"  Q{quarter}/{year}: EPS={vals['eps']:.2f}, "
                f"Revenue={vals['revenue']:.0f}, Companies={vals['count']}"
            )

        eps_growth = compute_yoy_growth(quarterly_data, "eps")
        revenue_growth = compute_yoy_growth(quarterly_data, "revenue")

        logger.info(f"FMP: computed {len(eps_growth)} EPS growth and {len(revenue_growth)} revenue growth points.")
        return eps_growth, revenue_growth

    except Exception as e:
        logger.warning(f"Failed to fetch S&P 500 earnings from FMP: {e}")
        return [], []


def fetch_sp500_pe_fmp(api_key):
    """Fetch S&P 500 Forward P/E ratio from FMP."""
    logger.info("Fetching S&P 500 Forward P/E ratio from Financial Modeling Prep...")
    if not api_key:
        logger.warning("FMP_API_KEY is absent. Skipping Forward P/E.")
        return []

    url = f"https://financialmodelingprep.com/api/v4/standard_pe_ratio_index?symbol=^GSPC&apikey={api_key}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code in (401, 402, 403):
            logger.warning(f"FMP API returned status {response.status_code} for Forward P/E. Skipping.")
            return []
        response.raise_for_status()
        data = response.json()

        forward_pe = []
        if isinstance(data, list):
            for item in data:
                date_str = item.get("date")
                val = None
                for key in ["pe", "peRatio", "value", "priceToEarnings"]:
                    if key in item and item[key] is not None:
                        val = item[key]
                        break
                if date_str and val is not None:
                    forward_pe.append({
                        "date": date_str,
                        "value": round(float(val), 2)
                    })
        forward_pe.sort(key=lambda x: x["date"])

        # Filter last 5 years
        start_date = (datetime.now() - timedelta(days=5 * 365)).strftime('%Y-%m-%d')
        forward_pe = [pt for pt in forward_pe if pt["date"] >= start_date]

        logger.info(f"Successfully fetched {len(forward_pe)} Forward P/E data points.")
        return forward_pe
    except Exception as e:
        logger.warning(f"Failed to fetch Forward P/E ratio from FMP: {e}")
        return []


def fetch_cape_ratio_nasdaq(api_key):
    """Fetch Shiller CAPE Ratio from Nasdaq Data Link."""
    logger.info("Fetching Shiller CAPE Ratio from Nasdaq Data Link...")
    if not api_key:
        logger.warning("NASDAQ_DATA_LINK_API_KEY is absent. Skipping CAPE ratio.")
        return []

    url = f"https://data.nasdaq.com/api/v3/datasets/MULTPL/SHILLER_PE_RATIO_MONTH.json?api_key={api_key}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code in (401, 402, 403):
            logger.warning(f"Nasdaq Data Link API returned status {response.status_code}. Skipping CAPE ratio.")
            return []
        response.raise_for_status()
        data = response.json()
        raw_data = data.get("dataset", {}).get("data", [])

        cape_ratio = []
        for item in raw_data:
            if len(item) >= 2:
                date_str = item[0]
                val = item[1]
                if date_str and val is not None:
                    cape_ratio.append({
                        "date": date_str,
                        "value": round(float(val), 2)
                    })
        cape_ratio.sort(key=lambda x: x["date"])

        # Filter last 5 years
        start_date = (datetime.now() - timedelta(days=5 * 365)).strftime('%Y-%m-%d')
        cape_ratio = [pt for pt in cape_ratio if pt["date"] >= start_date]

        logger.info(f"Successfully fetched {len(cape_ratio)} CAPE ratio data points.")
        return cape_ratio
    except Exception as e:
        logger.warning(f"Failed to fetch Shiller CAPE Ratio from Nasdaq Data Link: {e}")
        return []


def build_fmp_fetchers(config):
    """Build FMP and Nasdaq indicator fetchers."""
    return [
        {
            "keys": ["eps_growth", "revenue_growth"],
            "mode": "multi_output",
            "fetcher": lambda: fetch_sp500_earnings_fmp(config.fmp_api_key)
        },
        {
            "key": "forward_pe",
            "mode": "replace",
            "fetcher": lambda: fetch_sp500_pe_fmp(config.fmp_api_key)
        },
        {
            "key": "cape_ratio",
            "mode": "replace",
            "fetcher": lambda: fetch_cape_ratio_nasdaq(config.nasdaq_api_key)
        }
    ]
