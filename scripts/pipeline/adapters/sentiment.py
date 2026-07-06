"""Sentiment and alternative data adapters."""

import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def fetch_cnn_fear_greed():
    """Fetch CNN Fear & Greed Index."""
    logger.info("Fetching CNN Fear & Greed Index...")
    url = "https://production.dataviz.cnn.io/index/fearandgreed/current"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9"
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    score = round(float(data["score"]), 2)
    ts_str = data.get("timestamp", datetime.now().isoformat())
    date_str = ts_str[:10]
    return {"date": date_str, "value": score}


def fetch_insider_ratio():
    """Fetch OpenInsider transaction data."""
    logger.info("Fetching OpenInsider transaction data...")
    url = "http://openinsider.com/screener"
    params = {
        'fd': 30,  # last 30 days
        'xp': 1,   # purchase
        'xs': 1,   # sale
        'cnt': 1000
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_='tinytable')
    if not table:
        raise ValueError("OpenInsider table (tinytable) not found")

    tbody = table.find('tbody')
    rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]

    buy_count = 0
    sell_count = 0

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 13:
            continue
        tr_type = cols[7].text.strip()
        if 'P - Purchase' in tr_type:
            buy_count += 1
        elif 'S - Sale' in tr_type:
            sell_count += 1

    if buy_count == 0 and sell_count == 0:
        raise ValueError("No insider buy/sell transactions found in the table")

    ratio = buy_count / sell_count if sell_count > 0 else float(buy_count)

    date_str = datetime.now().strftime('%Y-%m-%d')
    return {"date": date_str, "value": round(ratio, 3)}


def build_sentiment_fetchers(config):
    """Build sentiment indicator fetchers."""
    return [
        {
            "key": "fear_greed",
            "mode": "upsert",
            "fetcher": fetch_cnn_fear_greed
        },
        {
            "key": "insider_ratio",
            "mode": "upsert",
            "fetcher": fetch_insider_ratio
        }
    ]
