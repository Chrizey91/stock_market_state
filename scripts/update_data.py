import os
import json
import logging
from datetime import datetime, timedelta, timezone
import pandas as pd
import yfinance as yf

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
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url)
    
    if 'observation_date' not in df.columns or series_id not in df.columns:
        raise ValueError(f"Unexpected columns in FRED CSV for {series_id}: {df.columns}")
        
    df['date'] = pd.to_datetime(df['observation_date'])
    df['value'] = pd.to_numeric(df[series_id], errors='coerce')
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

def main():
    existing_data = load_existing_data()
    
    # Initialize updated structure, retaining existing indicators in case of fetch failure
    updated_data = {
        "last_updated": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "indicators": existing_data.get("indicators", {})
    }
    
    # Fetch VIX
    try:
        updated_data["indicators"]["vix"] = fetch_vix()
    except Exception as e:
        logger.warning(f"Failed to fetch VIX data: {e}")
        # Keep existing if it exists, otherwise empty list
        if "vix" not in updated_data["indicators"]:
            updated_data["indicators"]["vix"] = []
            
    # Fetch FRED indicators
    fred_configs = {
        "fed_funds": "FEDFUNDS",
        "treasury_10y": "DGS10",
        "yield_curve": "T10Y2Y"
    }
    
    for key, series_id in fred_configs.items():
        try:
            updated_data["indicators"][key] = fetch_fred_series(series_id, years=5)
        except Exception as e:
            logger.warning(f"Failed to fetch FRED series {series_id} ({key}): {e}")
            if key not in updated_data["indicators"]:
                updated_data["indicators"][key] = []
                
    save_data(updated_data)

if __name__ == "__main__":
    main()
