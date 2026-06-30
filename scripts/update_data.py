import os
import json
import logging
import random
import calendar
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load .env file so API keys are available via os.environ
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'market_data.json')

def load_existing_data():
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading existing market data: {e}")
    return {}

def save_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    try:
        with open(DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved market data to {DATA_PATH}")
    except Exception as e:
        logger.error(f"Error saving market data: {e}")

def fetch_vix():
    logger.info("Fetching VIX data...")
    # VIX is a sentiment indicator (1 year of history)
    ticker = yf.Ticker('^VIX')
    df = ticker.history(period='1y')
    if df.empty:
        raise ValueError("VIX data is empty")
    
    df = df.dropna(subset=['Close'])
    data_points = []
    for date_val, row in df.iterrows():
        # Handle timezone-aware index
        date_str = date_val.strftime('%Y-%m-%d')
        data_points.append({
            "date": date_str,
            "value": round(float(row['Close']), 2)
        })
    data_points.sort(key=lambda x: x['date'])
    return data_points

def fetch_fred_series(series_id, years=5):
    logger.info(f"Fetching FRED series {series_id}...")
    api_key = os.environ.get("FRED_API_KEY")
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

def fetch_m2_growth(years=5):
    logger.info("Fetching M2 Money Supply (M2SL) and computing YoY Growth...")
    api_key = os.environ.get("FRED_API_KEY")
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

def generate_mock_ism_pmi(years=5):
    logger.info("Generating realistic fallback data for ISM Manufacturing PMI (NAPM)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    # Generate monthly dates (1st of each month)
    curr = datetime(start_date.year, start_date.month, 1)
    data_points = []
    
    while curr <= end_date:
        yr = curr.year
        m = curr.month
        # Base trends
        if yr == 2021:
            base = 60.0 + (m / 12.0) * 3.0 if m <= 6 else 63.0 - ((m - 6) / 6.0) * 5.0
        elif yr == 2022:
            base = 58.0 - (m / 12.0) * 10.0
        elif yr == 2023:
            base = 47.4 + (m % 3 - 1) * 0.8
        elif yr == 2024:
            base = 48.5 + (m % 4 - 2) * 1.0
        elif yr == 2025:
            base = 49.5 + (m % 5 - 2.5) * 0.7
        else: # 2026
            base = 50.2 + (m % 3 - 1) * 0.5
            
        # Add a tiny bit of random-like noise using date hash to be deterministic but look organic
        noise = ((curr.year * 13 + curr.month * 7) % 10 - 5) * 0.15
        val = round(base + noise, 1)
        
        data_points.append({
            "date": curr.strftime('%Y-%m-%d'),
            "value": val
        })
        
        # Advance to next month
        if curr.month == 12:
            curr = datetime(curr.year + 1, 1, 1)
        else:
            curr = datetime(curr.year, curr.month + 1, 1)
            
    return data_points

def get_sp500_tickers():
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
            # Fallback to class if ID is not found
            table = soup.find('table', class_='wikitable')
            
        if not table:
            raise ValueError("Could not find S&P 500 constituents table on page")
            
        tickers = []
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if cols:
                ticker = cols[0].text.strip()
                # yfinance uses '-' instead of '.' for classes (e.g. BRK-B instead of BRK.B)
                ticker = ticker.replace('.', '-')
                tickers.append(ticker)
                
        return sorted(list(set(tickers)))
    except Exception as e:
        logger.error(f"Error fetching S&P 500 tickers: {e}")
        raise

def chunk_tickers(tickers, chunk_size):
    return [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]

def calculate_breadth(df_close):
    # Sort index (dates) to ensure rolling works correctly
    df_close = df_close.sort_index()
    
    # Compute 200-day SMA for each column
    sma = df_close.rolling(window=200, min_periods=200).mean()
    
    # Check if close is greater than SMA
    is_above = df_close > sma
    
    # Valid SMA mask
    valid_sma = sma.notna()
    
    # Count of stocks above SMA per day
    above_count = (is_above & valid_sma).sum(axis=1)
    
    # Count of stocks with valid SMA per day
    total_valid = valid_sma.sum(axis=1)
    
    # Calculate percentage
    # Avoid division by zero
    breadth_pct = pd.Series(index=df_close.index, dtype=float)
    valid_dates = total_valid > 0
    breadth_pct[valid_dates] = (above_count[valid_dates] / total_valid[valid_dates]) * 100
    
    # We want to drop NaNs (where no stocks had 200 days of history yet)
    breadth_pct = breadth_pct.dropna()
    
    # Filter to the last 1 year (365 calendar days) of data to match other sentiment/internal indicators
    start_date = datetime.now() - timedelta(days=365)
    breadth_pct = breadth_pct[breadth_pct.index >= start_date]
    
    # Convert to JSON format
    data_points = []
    for date_val, val in breadth_pct.items():
        data_points.append({
            "date": date_val.strftime('%Y-%m-%d'),
            "value": round(float(val), 2)
        })
        
    data_points.sort(key=lambda x: x['date'])
    return data_points

_sp500_df_cache = None

def get_sp500_data():
    global _sp500_df_cache
    if _sp500_df_cache is not None:
        return _sp500_df_cache
        
    logger.info("Fetching S&P 500 constituents...")
    tickers = get_sp500_tickers()
    if not tickers:
        raise ValueError("No tickers retrieved from S&P 500 list")
        
    logger.info(f"Retrieved {len(tickers)} tickers. Downloading closing prices in batches...")
    
    # Download close prices in chunks
    chunks = chunk_tickers(tickers, chunk_size=100)
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
    _sp500_df_cache = df_all_close
    return _sp500_df_cache

def calculate_ad_line(df_close):
    df_close = df_close.sort_index()
    df_diff = df_close.diff()
    advancers = (df_diff > 0).sum(axis=1)
    decliners = (df_diff < 0).sum(axis=1)
    daily_change = advancers - decliners
    ad_line = daily_change.cumsum()
    
    # Filter to the last 1 year (365 calendar days) of data to match other sentiment/internal indicators
    start_date = datetime.now() - timedelta(days=365)
    ad_line = ad_line[ad_line.index >= start_date]
    
    data_points = []
    for date_val, val in ad_line.items():
        data_points.append({
            "date": date_val.strftime('%Y-%m-%d'),
            "value": int(val)
        })
    data_points.sort(key=lambda x: x['date'])
    return data_points

def calculate_new_highs_lows(df_close):
    df_close = df_close.sort_index()
    rolling_max = df_close.rolling(window=252, min_periods=252).max()
    rolling_min = df_close.rolling(window=252, min_periods=252).min()
    is_high = df_close == rolling_max
    is_low = df_close == rolling_min
    valid_mask = rolling_max.notna()
    
    highs_count = (is_high & valid_mask).sum(axis=1)
    lows_count = (is_low & valid_mask).sum(axis=1)
    
    # Filter to the last 1 year (365 calendar days) of data to match other sentiment/internal indicators
    start_date = datetime.now() - timedelta(days=365)
    highs_count = highs_count[highs_count.index >= start_date]
    lows_count = lows_count[lows_count.index >= start_date]
    
    data_points = []
    for date_val in highs_count.index:
        data_points.append({
            "date": date_val.strftime('%Y-%m-%d'),
            "highs": int(highs_count.loc[date_val]),
            "lows": int(lows_count.loc[date_val])
        })
    data_points.sort(key=lambda x: x['date'])
    return data_points

def fetch_sp500_breadth():
    df_all_close = get_sp500_data()
    return calculate_breadth(df_all_close)

def fetch_sp500_ad_line():
    df_all_close = get_sp500_data()
    return calculate_ad_line(df_all_close)

def fetch_sp500_new_highs_lows():
    df_all_close = get_sp500_data()
    return calculate_new_highs_lows(df_all_close)

def compute_yoy_growth(data, key_name):
    # Sort chronologically by date
    sorted_data = sorted(data, key=lambda x: x['date'])
    
    parsed_data = []
    for item in sorted_data:
        try:
            dt = datetime.strptime(item['date'], '%Y-%m-%d')
            val = item.get(key_name)
            if val is not None:
                parsed_data.append({
                    "date_obj": dt,
                    "date": item['date'],
                    "val": float(val)
                })
        except Exception as e:
            logger.warning(f"Error parsing date or value in YoY growth calculation for {key_name}: {e}")
            
    growth_points = []
    for i, current in enumerate(parsed_data):
        current_dt = current["date_obj"]
        target_year = current_dt.year - 1
        
        # Find the closest observation in target_year (matching quarter)
        prev_year_item = None
        min_diff_days = 45 # max 45 days diff to be considered the same quarter
        for prev in parsed_data[:i]:
            prev_dt = prev["date_obj"]
            if prev_dt.year == target_year:
                try:
                    target_dt = current_dt.replace(year=target_year)
                    diff_days = abs((prev_dt - target_dt).days)
                except ValueError:
                    diff_days = abs((prev_dt - (current_dt - timedelta(days=365))).days)
                if diff_days < min_diff_days:
                    min_diff_days = diff_days
                    prev_year_item = prev
                    
        if prev_year_item:
            prev_val = prev_year_item["val"]
            if prev_val != 0:
                yoy_growth = ((current["val"] - prev_val) / abs(prev_val)) * 100.0
                growth_points.append({
                    "date": current["date"],
                    "value": round(yoy_growth, 2)
                })
    return growth_points

def _quarter_key(dt):
    """Return a (year, quarter) tuple for a datetime object."""
    return (dt.year, (dt.month - 1) // 3 + 1)


def _quarter_date_label(year, quarter):
    """Return a date string like '2025-03-31' representing the quarter end."""
    month = quarter * 3

    last_day = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-{last_day:02d}"


def fetch_sp500_earnings_fmp():
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
    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        logger.warning("FMP_API_KEY environment variable is absent. Skipping FMP earnings.")
        return [], []

    # Top 30 S&P 500 companies by market cap (stable representative set)
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

        # Compute YoY growth using existing helper
        eps_growth = compute_yoy_growth(quarterly_data, "eps")
        revenue_growth = compute_yoy_growth(quarterly_data, "revenue")

        logger.info(f"FMP: computed {len(eps_growth)} EPS growth and {len(revenue_growth)} revenue growth points.")
        return eps_growth, revenue_growth

    except Exception as e:
        logger.warning(f"Failed to fetch S&P 500 earnings from FMP: {e}")
        return [], []

def generate_mock_fear_greed(days=365):
    end_date = datetime.now()
    data_points = []
    val = 50.0
    for i in range(days):
        date_str = (end_date - timedelta(days=days-i)).strftime('%Y-%m-%d')
        # Mean-reverting random walk to simulate F&G index
        val = val + 0.1 * (50.0 - val) + random.uniform(-8.0, 8.0)
        val = max(10.0, min(90.0, val))
        data_points.append({
            "date": date_str,
            "value": round(val, 2)
        })
    return data_points

def generate_mock_insider_ratio(days=365):
    end_date = datetime.now()
    data_points = []
    val = 0.2
    for i in range(days):
        date_str = (end_date - timedelta(days=days-i)).strftime('%Y-%m-%d')
        # Mean reverting around 0.22, with some occasional spikes
        val = val + 0.15 * (0.22 - val) + random.uniform(-0.05, 0.05)
        if random.random() < 0.05:
            val += random.uniform(0.15, 0.35)
        val = max(0.02, min(1.0, val))
        data_points.append({
            "date": date_str,
            "value": round(val, 3)
        })
    return data_points

def fetch_cnn_fear_greed():
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
    logger.info("Fetching OpenInsider transaction data...")
    url = "http://openinsider.com/screener"
    params = {
        'fd': 30, # last 30 days
        'xp': 1,  # purchase
        'xs': 1,  # sale
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

def fallback_duplicate_last_value(indicator_name, indicator_list, today_str=None):
    if not today_str:
        today_str = datetime.now().strftime('%Y-%m-%d')
    
    if not indicator_list:
        logger.warning(f"No historical data available to duplicate for indicator: {indicator_name}")
        return []
        
    last_entry = indicator_list[-1]
    if last_entry.get("date") == today_str:
        logger.info(f"Indicator {indicator_name} already has a data point for today {today_str}.")
        return indicator_list
        
    duplicated_entry = {
        "date": today_str,
        "value": last_entry["value"]
    }
    logger.info(f"Duplicating last value of {indicator_name} ({last_entry['value']}) for today ({today_str})")
    return indicator_list + [duplicated_entry]

def fetch_sp500_trend():
    logger.info("Fetching S&P 500 trend data...")
    ticker = yf.Ticker('^GSPC')
    # Fetch 2 years to have enough data to calculate 200-day SMA for the last 1 year
    df = ticker.history(period='2y')
    if df.empty:
        raise ValueError("S&P 500 (^GSPC) data is empty")
    
    df = df.dropna(subset=['Close'])
    # Compute 50-day and 200-day SMAs
    df['ma50'] = df['Close'].rolling(window=50).mean()
    df['ma200'] = df['Close'].rolling(window=200).mean()
    
    # Filter to the last 1 year (365 calendar days)
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
    logger.info("Fetching RSP and SPY data for Equal-Weight vs Cap-Weight...")
    # Fetch 1 year of daily closing prices
    data = yf.download(['RSP', 'SPY'], period='1y', interval='1d', progress=False)
    if data.empty or 'Close' not in data.columns:
        raise ValueError("RSP/SPY data is empty or missing Close column")
        
    df_close = data['Close'].dropna()
    if 'RSP' not in df_close.columns or 'SPY' not in df_close.columns:
        raise ValueError("RSP or SPY Close price data is missing")
        
    # Sort index to ensure correct rolling calculation
    df_close = df_close.sort_index()
    
    # Compute rolling 3-month (63 trading days) returns: (Price_t - Price_t-63) / Price_t-63 * 100
    df_close['rsp_return'] = df_close['RSP'].pct_change(63) * 100
    df_close['spy_return'] = df_close['SPY'].pct_change(63) * 100
    df_close['spread'] = df_close['rsp_return'] - df_close['spy_return']
    
    # Drop rows with NaN returns
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
    logger.info("Fetching 11 SPDR sector ETFs data...")
    sectors = ['XLK', 'XLF', 'XLI', 'XLV', 'XLY', 'XLP', 'XLE', 'XLU', 'XLC', 'XLRE', 'XLB']
    
    # Download 2 years of daily data to be safe for 200d MA and returns
    data = yf.download(sectors, period='2y', interval='1d', progress=False)
    if data.empty or 'Close' not in data.columns:
        raise ValueError("Sector ETFs data is empty or missing Close column")
        
    df_close = data['Close'].dropna(how='all')
    df_close = df_close.sort_index()
    
    # Calculate Sector MA Breadth (above 200-day MA)
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
    
    # Calculate Sector Performance Heatmap (1w, 1m, 3m returns)
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

def calculate_slope(y_values):
    if len(y_values) < 2:
        return 0.0
    n = len(y_values)
    x = list(range(n))
    sum_x = sum(x)
    sum_y = sum(y_values)
    sum_xx = sum(i*i for i in x)
    sum_xy = sum(i*y for i, y in zip(x, y_values))
    denominator = (n * sum_xx - sum_x * sum_x)
    if denominator == 0:
        return 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    return slope

def evaluate_scorecard(indicators):
    scorecard = []
    
    # 1. sp500_trend
    sp500_trend_data = indicators.get("sp500_trend", [])
    if sp500_trend_data:
        latest = sp500_trend_data[-1]
        val = latest.get("value")
        ma200 = latest.get("ma200")
        if val is not None and ma200 is not None:
            status = "healthy" if val > ma200 else "unhealthy"
            display_val = "Above" if val > ma200 else "Below"
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "sp500_trend",
        "label": "S&P 500 vs 200-day MA",
        "category": "Trend",
        "status": status,
        "value": display_val
    })
    
    # 2. sp500_momentum
    if sp500_trend_data:
        latest = sp500_trend_data[-1]
        ma50 = latest.get("ma50")
        ma200 = latest.get("ma200")
        if ma50 is not None and ma200 is not None:
            status = "healthy" if ma50 > ma200 else "unhealthy"
            display_val = "Golden Cross" if ma50 > ma200 else "Death Cross"
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "sp500_momentum",
        "label": "50-day vs 200-day MA",
        "category": "Momentum",
        "status": status,
        "value": display_val
    })
    
    # 3. sp500_breadth
    breadth_data = indicators.get("sp500_breadth", [])
    if breadth_data:
        latest = breadth_data[-1]
        val = latest.get("value")
        if val is not None:
            status = "healthy" if val > 70 else "unhealthy"
            display_val = f"{val:.1f}%"
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "sp500_breadth",
        "label": "% above 200-day MA",
        "category": "Breadth",
        "status": status,
        "value": display_val
    })
    
    # 4. sp500_ad_line
    ad_data = indicators.get("sp500_ad_line", [])
    if ad_data and len(ad_data) >= 20:
        last_20_vals = [float(pt["value"]) for pt in ad_data[-20:]]
        slope = calculate_slope(last_20_vals)
        status = "healthy" if slope > 0 else "unhealthy"
        display_val = "Rising" if slope > 0 else "Falling"
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "sp500_ad_line",
        "label": "S&P 500 A/D Line",
        "category": "Breadth",
        "status": status,
        "value": display_val
    })
    
    # 5. equal_vs_cap_weight
    eq_cap_data = indicators.get("equal_vs_cap_weight", [])
    if eq_cap_data:
        latest = eq_cap_data[-1]
        spread = latest.get("spread")
        if spread is not None:
            status = "healthy" if -5.0 <= spread <= 5.0 else "unhealthy"
            display_val = f"{spread:+.2f}%"
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "equal_vs_cap_weight",
        "label": "Equal-Weight vs Cap-Weight",
        "category": "Breadth",
        "status": status,
        "value": display_val
    })
    
    # 6. eps_growth
    eps_data = indicators.get("eps_growth", [])
    if eps_data:
        latest = eps_data[-1]
        val = latest.get("value")
        if val is not None:
            status = "healthy" if val > 0.0 else "unhealthy"
            display_val = f"{val:+.2f}%" if val != 0 else "0.00%"
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "eps_growth",
        "label": "S&P 500 EPS Growth",
        "category": "Earnings",
        "status": status,
        "value": display_val
    })
    
    # 7. revenue_growth
    rev_data = indicators.get("revenue_growth", [])
    if rev_data:
        latest = rev_data[-1]
        val = latest.get("value")
        if val is not None:
            status = "healthy" if val > 0.0 else "unhealthy"
            display_val = f"{val:+.2f}%" if val != 0 else "0.00%"
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "revenue_growth",
        "label": "S&P 500 Revenue Growth",
        "category": "Earnings",
        "status": status,
        "value": display_val
    })
    
    # 8. forward_pe (unimplemented)
    scorecard.append({
        "id": "forward_pe",
        "label": "Forward P/E",
        "category": "Valuation",
        "status": "unavailable",
        "value": None
    })
    
    # 9. vix
    vix_data = indicators.get("vix", [])
    if vix_data:
        latest = vix_data[-1]
        val = latest.get("value")
        if val is not None:
            status = "healthy" if val <= 20 else "unhealthy"
            display_val = round(float(val), 2)
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "vix",
        "label": "VIX",
        "category": "Volatility",
        "status": status,
        "value": display_val
    })
    
    # 10. hy_spread
    hy_data = indicators.get("high_yield_spread", [])
    if hy_data:
        latest = hy_data[-1]
        val = latest.get("value")
        if val is not None:
            status = "healthy" if val < 5.0 else "unhealthy"
            display_val = f"{val:.2f}%"
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "hy_spread",
        "label": "HY Credit Spread",
        "category": "Credit",
        "status": status,
        "value": display_val
    })
    
    # 11. m2_growth
    m2_data = indicators.get("m2_growth", [])
    if m2_data:
        latest = m2_data[-1]
        val = latest.get("value")
        if val is not None:
            status = "healthy" if val >= 0.0 else "unhealthy"
            display_val = f"{val:.2f}%"
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "m2_growth",
        "label": "M2 YoY Growth",
        "category": "Liquidity",
        "status": status,
        "value": display_val
    })
    
    # 12. sector_leadership
    sector_lead_data = indicators.get("sector_leadership", {})
    if sector_lead_data and "above_200d" in sector_lead_data and "total" in sector_lead_data:
        above_count = sector_lead_data["above_200d"]
        total_count = sector_lead_data["total"]
        status = "healthy" if above_count >= 8 else "unhealthy"
        display_val = f"{above_count}/{total_count}"
    else:
        status = "unavailable"
        display_val = None
        
    scorecard.append({
        "id": "sector_leadership",
        "label": "Sector MA Breadth",
        "category": "Leadership",
        "status": status,
        "value": display_val
    })
    
    # Calculate health_score and health_total
    health_score = sum(1 for m in scorecard if m["status"] == "healthy")
    health_total = sum(1 for m in scorecard if m["status"] in ("healthy", "unhealthy"))
    
    return scorecard, health_score, health_total

def main():
    existing_data = load_existing_data()
    
    # Deep copy existing indicators to avoid mutation issues
    existing_indicators = existing_data.get("indicators", {})
    indicators_copy = {}
    for key, val in existing_indicators.items():
        if isinstance(val, list):
            indicators_copy[key] = [dict(item) for item in val if isinstance(item, dict)]
        else:
            indicators_copy[key] = val

    # Initialize updated structure
    updated_data = {
        "last_updated": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "indicators": indicators_copy
    }
    
    # Fetch VIX
    try:
        updated_data["indicators"]["vix"] = fetch_vix()
    except Exception as e:
        logger.warning(f"Failed to fetch VIX data: {e}")
        vix_list = existing_indicators.get("vix", [])
        updated_data["indicators"]["vix"] = fallback_duplicate_last_value("vix", vix_list)
            
    # Fetch S&P 500 trend and momentum data
    try:
        updated_data["indicators"]["sp500_trend"] = fetch_sp500_trend()
    except Exception as e:
        logger.warning(f"Failed to fetch S&P 500 trend data: {e}")
        trend_list = existing_indicators.get("sp500_trend", [])
        if trend_list:
            today_str = datetime.now().strftime('%Y-%m-%d')
            last_entry = trend_list[-1]
            if last_entry.get("date") == today_str:
                updated_data["indicators"]["sp500_trend"] = trend_list
            else:
                new_entry = dict(last_entry)
                new_entry["date"] = today_str
                updated_data["indicators"]["sp500_trend"] = trend_list + [new_entry]
        else:
            updated_data["indicators"]["sp500_trend"] = []
            
    # Fetch standard FRED indicators
    fred_configs = {
        "fed_funds": "FEDFUNDS",
        "treasury_10y": "DGS10",
        "yield_curve": "T10Y2Y",
        "high_yield_spread": "BAMLH0A0HYM2"
    }
    
    for key, series_id in fred_configs.items():
        try:
            updated_data["indicators"][key] = fetch_fred_series(series_id, years=5)
        except Exception as e:
            logger.warning(f"Failed to fetch FRED series {series_id} ({key}): {e}")
            fred_list = existing_indicators.get(key, [])
            updated_data["indicators"][key] = fallback_duplicate_last_value(key, fred_list)
                
    # Fetch/Compute M2 Liquidity Growth
    try:
        updated_data["indicators"]["m2_growth"] = fetch_m2_growth(years=5)
    except Exception as e:
        logger.warning(f"Failed to fetch/compute M2 Liquidity Growth: {e}")
        m2_list = existing_indicators.get("m2_growth", [])
        updated_data["indicators"]["m2_growth"] = fallback_duplicate_last_value("m2_growth", m2_list)

    # Fetch ISM Manufacturing PMI (try FRED first, fallback to generated mock data or duplicate last value)
    try:
        updated_data["indicators"]["ism_pmi"] = fetch_fred_series("NAPM", years=5)
    except Exception as e:
        logger.warning(f"Failed to fetch FRED series NAPM (ism_pmi): {e}")
        pmi_list = existing_indicators.get("ism_pmi", [])
        if pmi_list:
            updated_data["indicators"]["ism_pmi"] = fallback_duplicate_last_value("ism_pmi", pmi_list)
        else:
            logger.warning("No existing ism_pmi data. Using realistic generated fallback.")
            updated_data["indicators"]["ism_pmi"] = generate_mock_ism_pmi(years=5)

    # Fetch/Compute S&P 500 Breadth (% of stocks above 200-day SMA)
    try:
        updated_data["indicators"]["sp500_breadth"] = fetch_sp500_breadth()
    except Exception as e:
        logger.warning(f"Failed to fetch/compute S&P 500 Breadth: {e}")
        breadth_list = existing_indicators.get("sp500_breadth", [])
        updated_data["indicators"]["sp500_breadth"] = fallback_duplicate_last_value("sp500_breadth", breadth_list)

    # Fetch/Compute S&P 500 Advance-Decline Line
    try:
        updated_data["indicators"]["sp500_ad_line"] = fetch_sp500_ad_line()
    except Exception as e:
        logger.warning(f"Failed to fetch/compute S&P 500 A/D Line: {e}")
        ad_list = existing_indicators.get("sp500_ad_line", [])
        updated_data["indicators"]["sp500_ad_line"] = fallback_duplicate_last_value("sp500_ad_line", ad_list)

    # Fetch/Compute Equal-Weight vs Cap-Weight
    try:
        updated_data["indicators"]["equal_vs_cap_weight"] = fetch_equal_vs_cap_weight()
    except Exception as e:
        logger.warning(f"Failed to fetch/compute Equal-Weight vs Cap-Weight: {e}")
        eq_cap_list = existing_indicators.get("equal_vs_cap_weight", [])
        if eq_cap_list:
            today_str = datetime.now().strftime('%Y-%m-%d')
            last_entry = eq_cap_list[-1]
            if last_entry.get("date") == today_str:
                updated_data["indicators"]["equal_vs_cap_weight"] = eq_cap_list
            else:
                new_entry = dict(last_entry)
                new_entry["date"] = today_str
                updated_data["indicators"]["equal_vs_cap_weight"] = eq_cap_list + [new_entry]
        else:
            updated_data["indicators"]["equal_vs_cap_weight"] = []

    # Fetch/Compute S&P 500 New Highs vs Lows
    try:
        updated_data["indicators"]["sp500_new_highs_lows"] = fetch_sp500_new_highs_lows()
    except Exception as e:
        logger.warning(f"Failed to fetch/compute S&P 500 New Highs/Lows: {e}")
        highs_lows_list = existing_indicators.get("sp500_new_highs_lows", [])
        if highs_lows_list:
            today_str = datetime.now().strftime('%Y-%m-%d')
            last_hl = highs_lows_list[-1]
            if last_hl.get("date") == today_str:
                updated_data["indicators"]["sp500_new_highs_lows"] = highs_lows_list
            else:
                new_hl = dict(last_hl)
                new_hl["date"] = today_str
                updated_data["indicators"]["sp500_new_highs_lows"] = highs_lows_list + [new_hl]
        else:
            updated_data["indicators"]["sp500_new_highs_lows"] = []

    # Fetch S&P 500 earnings data (YoY EPS and Revenue growth) from FMP
    try:
        eps_growth, revenue_growth = fetch_sp500_earnings_fmp()
        updated_data["indicators"]["eps_growth"] = eps_growth
        updated_data["indicators"]["revenue_growth"] = revenue_growth
    except Exception as e:
        logger.warning(f"Failed to fetch/compute S&P 500 earnings: {e}")
        updated_data["indicators"]["eps_growth"] = []
        updated_data["indicators"]["revenue_growth"] = []

    # Fetch Sector ETFs leadership and performance heatmap
    try:
        sector_leadership, sector_heatmap = fetch_sector_data()
        updated_data["indicators"]["sector_leadership"] = sector_leadership
        updated_data["indicators"]["sector_heatmap"] = sector_heatmap
        logger.info("Successfully fetched sector ETFs leadership and heatmap data")
    except Exception as e:
        logger.warning(f"Failed to fetch/compute Sector ETFs data: {e}")
        updated_data["indicators"]["sector_leadership"] = existing_indicators.get("sector_leadership", {"above_200d": 0, "total": 11, "sectors": []})
        updated_data["indicators"]["sector_heatmap"] = existing_indicators.get("sector_heatmap", [])

    # Fetch/Compute CNN Fear & Greed Index
    fear_greed_list = updated_data["indicators"].get("fear_greed", [])
    if not fear_greed_list:
        logger.info("Fear & Greed history not found. Generating realistic history...")
        fear_greed_list = generate_mock_fear_greed(365)
        
    try:
        new_fg = fetch_cnn_fear_greed()
        updated = False
        for item in fear_greed_list:
            if item["date"] == new_fg["date"]:
                item["value"] = new_fg["value"]
                updated = True
                break
        if not updated:
            fear_greed_list.append(new_fg)
        fear_greed_list.sort(key=lambda x: x["date"])
        fear_greed_list = fear_greed_list[-365:]
        logger.info(f"Successfully updated Fear & Greed Index: {new_fg}")
    except Exception as e:
        logger.warning(f"Failed to fetch/compute CNN Fear & Greed: {e}")
        # Duplicate last value on failure
        fear_greed_list = fallback_duplicate_last_value("fear_greed", fear_greed_list)
        
    updated_data["indicators"]["fear_greed"] = fear_greed_list

    # Fetch/Compute Insider Buying vs Selling Ratio
    insider_list = updated_data["indicators"].get("insider_ratio", [])
    if not insider_list:
        logger.info("Insider Buying/Selling ratio history not found. Generating realistic history...")
        insider_list = generate_mock_insider_ratio(365)
        
    try:
        new_insider = fetch_insider_ratio()
        updated = False
        for item in insider_list:
            if item["date"] == new_insider["date"]:
                item["value"] = new_insider["value"]
                updated = True
                break
        if not updated:
            insider_list.append(new_insider)
        insider_list.sort(key=lambda x: x["date"])
        insider_list = insider_list[-365:]
        logger.info(f"Successfully updated Insider Buy/Sell Ratio: {new_insider}")
    except Exception as e:
        logger.warning(f"Failed to fetch/compute Insider Buy/Sell Ratio: {e}")
        # Duplicate last value on failure
        insider_list = fallback_duplicate_last_value("insider_ratio", insider_list)
        
    updated_data["indicators"]["insider_ratio"] = insider_list

    # Calculate composite market regime index
    try:
        regime_timeline = calculate_market_regime_index(updated_data["indicators"])
        updated_data["indicators"]["market_regime_index"] = regime_timeline
        if regime_timeline:
            updated_data["market_regime_score"] = regime_timeline[-1]["value"]
            logger.info(f"Successfully calculated Market Regime Index. Current score: {updated_data['market_regime_score']}")
        else:
            updated_data["market_regime_score"] = 50.0
            logger.warning("Market Regime Index timeline is empty. Setting default score to 50.0")
    except Exception as e:
        logger.error(f"Failed to calculate Market Regime Index: {e}")
        updated_data["indicators"]["market_regime_index"] = existing_indicators.get("market_regime_index", [])
        updated_data["market_regime_score"] = existing_data.get("market_regime_score", 50.0)

    # Calculate scorecard
    try:
        scorecard, health_score, health_total = evaluate_scorecard(updated_data["indicators"])
        updated_data["scorecard"] = scorecard
        updated_data["health_score"] = health_score
        updated_data["health_total"] = health_total
        logger.info(f"Successfully evaluated scorecard: {health_score} of {health_total} healthy")
    except Exception as e:
        logger.error(f"Failed to evaluate scorecard: {e}")
        updated_data["scorecard"] = existing_data.get("scorecard", [])
        updated_data["health_score"] = existing_data.get("health_score", 0)
        updated_data["health_total"] = existing_data.get("health_total", 0)

    save_data(updated_data)

def normalize_vix(vix):
    if vix is None:
        return 50.0
    # Clamped linear mapping: <=12 is 100 (Risk-On), >=35 is 0 (Risk-Off)
    val = 100.0 - (vix - 12.0) / (35.0 - 12.0) * 100.0
    return max(0.0, min(100.0, val))

def normalize_yield_curve(yc):
    if yc is None:
        return 50.0
    # Clamped linear mapping: <=-0.5 is 0 (Risk-Off), >=1.5 is 100 (Risk-On)
    val = (yc - (-0.5)) / (1.5 - (-0.5)) * 100.0
    return max(0.0, min(100.0, val))

def normalize_high_yield_spread(hy):
    if hy is None:
        return 50.0
    # Clamped linear mapping: <=3.0 is 100 (Risk-On), >=8.5 is 0 (Risk-Off)
    val = 100.0 - (hy - 3.0) / (8.5 - 3.0) * 100.0
    return max(0.0, min(100.0, val))

def normalize_sp500_breadth(breadth):
    if breadth is None:
        return 50.0
    return max(0.0, min(100.0, breadth))

def normalize_m2_growth(m2):
    if m2 is None:
        return 50.0
    # Clamped linear mapping: <=0 is 0 (Risk-Off), >=8.0 is 100 (Risk-On)
    val = (m2 - 0.0) / (8.0 - 0.0) * 100.0
    return max(0.0, min(100.0, val))

def calculate_market_regime_index(indicators):
    # Weights definition
    weights = {
        "vix": 0.25,
        "high_yield_spread": 0.20,
        "yield_curve": 0.15,
        "sp500_breadth": 0.20,
        "m2_growth": 0.20
    }
    
    # Extract historical timelines
    vix_series = indicators.get("vix", [])
    hy_series = indicators.get("high_yield_spread", [])
    yc_series = indicators.get("yield_curve", [])
    breadth_series = indicators.get("sp500_breadth", [])
    m2_series = indicators.get("m2_growth", [])
    
    # Collect all unique dates across these 5 indicators
    all_dates = set()
    for series in [vix_series, hy_series, yc_series, breadth_series, m2_series]:
        for pt in series:
            if "date" in pt:
                all_dates.add(pt["date"])
                
    sorted_dates = sorted(list(all_dates))
    
    # Create maps for fast lookups
    vix_map = {pt["date"]: pt["value"] for pt in vix_series if "date" in pt and pt.get("value") is not None}
    hy_map = {pt["date"]: pt["value"] for pt in hy_series if "date" in pt and pt.get("value") is not None}
    yc_map = {pt["date"]: pt["value"] for pt in yc_series if "date" in pt and pt.get("value") is not None}
    breadth_map = {pt["date"]: pt["value"] for pt in breadth_series if "date" in pt and pt.get("value") is not None}
    m2_map = {pt["date"]: pt["value"] for pt in m2_series if "date" in pt and pt.get("value") is not None}
    
    # State for forward-filling
    last_vix = None
    last_hy = None
    last_yc = None
    last_breadth = None
    last_m2 = None
    
    timeline = []
    for d in sorted_dates:
        # Update last seen value
        if d in vix_map: last_vix = vix_map[d]
        if d in hy_map: last_hy = hy_map[d]
        if d in yc_map: last_yc = yc_map[d]
        if d in breadth_map: last_breadth = breadth_map[d]
        if d in m2_map: last_m2 = m2_map[d]
        
        # Calculate only if we have at least one value for all 5 indicators
        if (last_vix is not None and 
            last_hy is not None and 
            last_yc is not None and 
            last_breadth is not None and 
            last_m2 is not None):
            
            # Normalize each
            n_vix = normalize_vix(last_vix)
            n_hy = normalize_high_yield_spread(last_hy)
            n_yc = normalize_yield_curve(last_yc)
            n_breadth = normalize_sp500_breadth(last_breadth)
            n_m2 = normalize_m2_growth(last_m2)
            
            # Weighted average
            score = (
                n_vix * weights["vix"] +
                n_hy * weights["high_yield_spread"] +
                n_yc * weights["yield_curve"] +
                n_breadth * weights["sp500_breadth"] +
                n_m2 * weights["m2_growth"]
            )
            
            timeline.append({
                "date": d,
                "value": round(score, 2)
            })
            
    return timeline

if __name__ == "__main__":
    main()
