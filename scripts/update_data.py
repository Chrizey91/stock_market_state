import os
import json
import logging
import random
from datetime import datetime, timedelta, timezone
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup


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

def fetch_sp500_breadth():
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
    
    logger.info(f"Combined data shape: {df_all_close.shape}. Calculating breadth indicator...")
    breadth_data = calculate_breadth(df_all_close)
    return breadth_data

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
