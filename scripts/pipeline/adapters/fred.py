"""FRED network adapters and registry builder."""

import logging
from datetime import datetime, timedelta
import pandas as pd
import requests

logger = logging.getLogger(__name__)


def fetch_fred_series(series_id, api_key, years=5):
    """Fetch FRED series using API with CSV fallback."""
    logger.info(f"Fetching FRED series {series_id}...")
    df = None

    if api_key:
        try:
            logger.info(f"Using FRED API for series {series_id}...")
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            if 'observations' not in data:
                raise ValueError(f"No observations in FRED API response for {series_id}")
            df = pd.DataFrame(data['observations'])
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df = df.dropna(subset=['value'])
                df = df.sort_values('date')
            else:
                df = pd.DataFrame(columns=['date', 'value'])
        except Exception as e:
            logger.warning(f"FRED API fetch failed for series {series_id}, falling back to CSV scraping: {e}")
            df = None

    if df is None:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        df = pd.read_csv(url)

        if 'observation_date' not in df.columns or series_id not in df.columns:
            raise ValueError(f"Unexpected columns in FRED CSV for {series_id}: {df.columns}")

        df['date'] = pd.to_datetime(df['observation_date'])
        df['value'] = pd.to_numeric(df[series_id], errors='coerce')
        df = df.dropna(subset=['value'])
        df = df.sort_values('date')

    # Filter for the last N years
    start_date = datetime.now() - timedelta(days=years * 365)
    df = df[df['date'] >= start_date]

    data_points = []
    for _, row in df.iterrows():
        data_points.append({
            "date": row['date'].strftime('%Y-%m-%d'),
            "value": round(float(row['value']), 2)
        })

    data_points.sort(key=lambda x: x['date'])
    return data_points


def fetch_m2_growth(api_key, years=5):
    """Fetch M2 Money Supply and calculate YoY growth."""
    logger.info("Fetching M2 Money Supply (M2SL) and computing YoY Growth...")
    df = None

    if api_key:
        try:
            logger.info("Using FRED API for M2SL...")
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=M2SL&api_key={api_key}&file_type=json"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            if 'observations' not in data:
                raise ValueError("No observations in FRED API response for M2SL")
            df = pd.DataFrame(data['observations'])
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df['raw_value'] = pd.to_numeric(df['value'], errors='coerce')
                df = df.dropna(subset=['raw_value'])
                df = df.sort_values('date')
            else:
                df = pd.DataFrame(columns=['date', 'raw_value'])
        except Exception as e:
            logger.warning(f"FRED API fetch failed for M2SL, falling back to CSV scraping: {e}")
            df = None

    if df is None:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL"
        df = pd.read_csv(url)

        if 'observation_date' not in df.columns or 'M2SL' not in df.columns:
            raise ValueError(f"Unexpected columns in FRED CSV for M2SL: {df.columns}")

        df['date'] = pd.to_datetime(df['observation_date'])
        df['raw_value'] = pd.to_numeric(df['M2SL'], errors='coerce')
        df = df.dropna(subset=['raw_value'])
        df = df.sort_values('date')

    # YoY percentage change over 12 periods (monthly data, so 12 periods = 1 year)
    df['value'] = df['raw_value'].pct_change(periods=12) * 100
    df = df.dropna(subset=['value'])

    # Filter for the last N years
    start_date = datetime.now() - timedelta(days=years * 365)
    df = df[df['date'] >= start_date]

    data_points = []
    for _, row in df.iterrows():
        data_points.append({
            "date": row['date'].strftime('%Y-%m-%d'),
            "value": round(float(row['value']), 2)
        })

    data_points.sort(key=lambda x: x['date'])
    return data_points


def build_fred_fetchers(config):
    """Build FRED indicator fetchers."""
    fetchers = []

    # Standard FRED indicators mapping
    fred_configs = {
        "fed_funds": "FEDFUNDS",
        "treasury_10y": "DGS10",
        "yield_curve": "T10Y2Y",
        "high_yield_spread": "BAMLH0A0HYM2"
    }

    for key, series_id in fred_configs.items():
        # capture series_id cleanly in closure
        fetchers.append({
            "key": key,
            "mode": "replace",
            "fetcher": lambda sid=series_id: fetch_fred_series(sid, config.fred_api_key, years=5)
        })

    # Add M2 Growth
    fetchers.append({
        "key": "m2_growth",
        "mode": "replace",
        "fetcher": lambda: fetch_m2_growth(config.fred_api_key, years=5)
    })

    return fetchers
