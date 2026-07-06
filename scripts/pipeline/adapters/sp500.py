"""S&P 500 network adapters and registry builder."""

import logging
from datetime import datetime, timedelta, timezone
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

from ..indicators import calculate_breadth, calculate_ad_line, calculate_new_highs_lows

logger = logging.getLogger(__name__)


def get_sp500_tickers():
    """Fetch S&P 500 tickers from Wikipedia."""
    logger.info("Fetching S&P 500 tickers from Wikipedia...")
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            raise ValueError(f"HTTP error {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'constituents'})
        if not table:
            table = soup.find('table', class_='wikitable')

        if not table:
            raise ValueError("Could not find S&P 500 constituents table on page")

        tickers = []
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if cols:
                ticker = cols[0].text.strip()
                ticker = ticker.replace('.', '-')
                tickers.append(ticker)

        return sorted(list(set(tickers)))
    except Exception as e:
        logger.error(f"Error fetching S&P 500 tickers: {e}")
        raise


def fetch_sp500_data():
    """Download daily close prices for all S&P 500 constituents (2 years)."""
    logger.info("Fetching S&P 500 constituents...")
    tickers = get_sp500_tickers()
    if not tickers:
        raise ValueError("No tickers retrieved from S&P 500 list")

    logger.info(f"Retrieved {len(tickers)} tickers. Downloading closing prices in batches...")

    chunk_size = 100
    chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    all_close_dfs = []

    for i, chunk in enumerate(chunks):
        logger.info(f"Downloading chunk {i+1}/{len(chunks)} ({len(chunk)} tickers)...")
        try:
            data = yf.download(chunk, period='2y', interval='1d', progress=False)
            if not data.empty and 'Close' in data.columns:
                close_df = data['Close']
                if isinstance(close_df, pd.Series):
                    close_df = close_df.to_frame(name=chunk[0])
                all_close_dfs.append(close_df)
            else:
                logger.warning(f"Chunk {i+1} returned no Close price data.")
        except Exception as e:
            logger.error(f"Error downloading chunk {i+1}: {e}")

    if not all_close_dfs:
        raise ValueError("Failed to download any ticker closing price data")

    df_all_close = pd.concat(all_close_dfs, axis=1)
    df_all_close = df_all_close.loc[:, ~df_all_close.columns.duplicated()]
    return df_all_close


def fetch_vix():
    """Fetch VIX data."""
    logger.info("Fetching VIX data...")
    ticker = yf.Ticker('^VIX')
    df = ticker.history(period='1y')
    if df.empty:
        raise ValueError("VIX data is empty")

    df = df.dropna(subset=['Close'])
    data_points = []
    for date_val, row in df.iterrows():
        date_str = date_val.strftime('%Y-%m-%d')
        data_points.append({
            "date": date_str,
            "value": round(float(row['Close']), 2)
        })
    data_points.sort(key=lambda x: x['date'])
    return data_points


def fetch_sp500_trend():
    """Fetch S&P 500 trend (Price vs 50d/200d MA)."""
    logger.info("Fetching S&P 500 trend data...")
    ticker = yf.Ticker('^GSPC')
    df = ticker.history(period='2y')
    if df.empty:
        raise ValueError("S&P 500 (^GSPC) data is empty")

    df = df.dropna(subset=['Close'])
    df['ma50'] = df['Close'].rolling(window=50).mean()
    df['ma200'] = df['Close'].rolling(window=200).mean()

    start_date = datetime.now(timezone.utc) - timedelta(days=365)
    if df.index.tz is not None:
        df = df[df.index >= start_date]
    else:
        df = df[df.index >= start_date.replace(tzinfo=None)]

    data_points = []
    for date_val, row in df.iterrows():
        date_str = date_val.strftime('%Y-%m-%d')
        ma50_val = row['ma50']
        ma200_val = row['ma200']
        data_points.append({
            "date": date_str,
            "value": round(float(row['Close']), 2),
            "ma50": round(float(ma50_val), 2) if pd.notna(ma50_val) else None,
            "ma200": round(float(ma200_val), 2) if pd.notna(ma200_val) else None
        })

    data_points.sort(key=lambda x: x['date'])
    return data_points


def fetch_equal_vs_cap_weight():
    """Fetch RSP vs SPY spread."""
    logger.info("Fetching RSP and SPY data for Equal-Weight vs Cap-Weight...")
    data = yf.download(['RSP', 'SPY'], period='1y', interval='1d', progress=False)
    if data.empty or 'Close' not in data.columns:
        raise ValueError("RSP/SPY data is empty or missing Close column")

    df_close = data['Close'].dropna()
    if 'RSP' not in df_close.columns or 'SPY' not in df_close.columns:
        raise ValueError("RSP or SPY Close price data is missing")

    df_close = df_close.sort_index()
    df_close['rsp_return'] = df_close['RSP'].pct_change(63) * 100
    df_close['spy_return'] = df_close['SPY'].pct_change(63) * 100
    df_close['spread'] = df_close['rsp_return'] - df_close['spy_return']

    df_clean = df_close.dropna(subset=['rsp_return', 'spy_return', 'spread'])

    data_points = []
    for date_val, row in df_clean.iterrows():
        data_points.append({
            "date": date_val.strftime('%Y-%m-%d'),
            "rsp_return": round(float(row['rsp_return']), 2),
            "spy_return": round(float(row['spy_return']), 2),
            "spread": round(float(row['spread']), 2)
        })

    data_points.sort(key=lambda x: x['date'])
    return data_points


def fetch_sector_data():
    """Fetch 11 SPDR sectors MA breadth and heatmaps."""
    logger.info("Fetching 11 SPDR sector ETFs data...")
    sectors = ['XLK', 'XLF', 'XLI', 'XLV', 'XLY', 'XLP', 'XLE', 'XLU', 'XLC', 'XLRE', 'XLB']

    data = yf.download(sectors, period='2y', interval='1d', progress=False)
    if data.empty or 'Close' not in data.columns:
        raise ValueError("Sector ETFs data is empty or missing Close column")

    df_close = data['Close'].dropna(how='all')
    df_close = df_close.sort_index()

    sma200 = df_close.rolling(window=200, min_periods=200).mean()

    latest_prices = df_close.iloc[-1]
    latest_sma200 = sma200.iloc[-1]

    sectors_above = []
    above_count = 0

    for s in sectors:
        if s in latest_prices.index and s in latest_sma200.index:
            price = latest_prices[s]
            sma = latest_sma200[s]

            if pd.notna(price) and pd.notna(sma):
                above = bool(price > sma)
                if above:
                    above_count += 1
                sectors_above.append({"name": s, "above": above})
            else:
                sectors_above.append({"name": s, "above": False})
        else:
            sectors_above.append({"name": s, "above": False})

    sector_leadership = {
        "above_200d": above_count,
        "total": len(sectors),
        "sectors": sectors_above
    }

    pct_1w = df_close.pct_change(5).iloc[-1] * 100
    pct_1m = df_close.pct_change(21).iloc[-1] * 100
    pct_3m = df_close.pct_change(63).iloc[-1] * 100

    sector_heatmap = []
    for s in sectors:
        val_1w = pct_1w.get(s) if s in pct_1w.index else None
        val_1m = pct_1m.get(s) if s in pct_1m.index else None
        val_3m = pct_3m.get(s) if s in pct_3m.index else None

        sector_heatmap.append({
            "sector": s,
            "1w": round(float(val_1w), 2) if val_1w is not None and pd.notna(val_1w) else None,
            "1m": round(float(val_1m), 2) if val_1m is not None and pd.notna(val_1m) else None,
            "3m": round(float(val_3m), 2) if val_3m is not None and pd.notna(val_3m) else None
        })

    return sector_leadership, sector_heatmap


def build_sp500_fetchers(config, df_sp500):
    """Build S&P 500 indicator fetchers."""
    return [
        {
            "key": "vix",
            "mode": "replace",
            "fetcher": fetch_vix
        },
        {
            "key": "sp500_trend",
            "mode": "replace",
            "fetcher": fetch_sp500_trend
        },
        {
            "key": "sp500_breadth",
            "mode": "replace",
            "fetcher": lambda: calculate_breadth(df_sp500)
        },
        {
            "key": "sp500_ad_line",
            "mode": "replace",
            "fetcher": lambda: calculate_ad_line(df_sp500)
        },
        {
            "key": "sp500_new_highs_lows",
            "mode": "replace",
            "fetcher": lambda: calculate_new_highs_lows(df_sp500)
        },
        {
            "key": "equal_vs_cap_weight",
            "mode": "replace",
            "fetcher": fetch_equal_vs_cap_weight
        },
        {
            "keys": ["sector_leadership", "sector_heatmap"],
            "mode": "multi_output",
            "fetcher": fetch_sector_data
        }
    ]
