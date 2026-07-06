"""Pure indicator computation functions.

These functions take raw data (DataFrames or lists of dicts) and return
computed indicator data points. No I/O, no API calls, no side effects.
"""

import calendar
import logging
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)


def calculate_breadth(df_close):
    """Calculate S&P 500 breadth (% of stocks above 200-day SMA).

    Args:
        df_close: DataFrame of daily closing prices with stocks as columns.

    Returns:
        List of {date, value} dicts with breadth percentage.
    """
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
    breadth_pct = pd.Series(index=df_close.index, dtype=float)
    valid_dates = total_valid > 0
    breadth_pct[valid_dates] = (above_count[valid_dates] / total_valid[valid_dates]) * 100

    # Drop NaNs (where no stocks had 200 days of history yet)
    breadth_pct = breadth_pct.dropna()

    # Filter to the last 1 year
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


def calculate_ad_line(df_close):
    """Calculate the S&P 500 Advance-Decline Line.

    Args:
        df_close: DataFrame of daily closing prices with stocks as columns.

    Returns:
        List of {date, value} dicts with cumulative A/D values.
    """
    df_close = df_close.sort_index()
    df_diff = df_close.diff()
    advancers = (df_diff > 0).sum(axis=1)
    decliners = (df_diff < 0).sum(axis=1)
    daily_change = advancers - decliners
    ad_line = daily_change.cumsum()

    # Filter to the last 1 year
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
    """Calculate S&P 500 52-week New Highs vs Lows.

    Args:
        df_close: DataFrame of daily closing prices with stocks as columns.

    Returns:
        List of {date, highs, lows} dicts.
    """
    df_close = df_close.sort_index()
    rolling_max = df_close.rolling(window=252, min_periods=252).max()
    rolling_min = df_close.rolling(window=252, min_periods=252).min()
    is_high = df_close == rolling_max
    is_low = df_close == rolling_min
    valid_mask = rolling_max.notna()

    highs_count = (is_high & valid_mask).sum(axis=1)
    lows_count = (is_low & valid_mask).sum(axis=1)

    # Filter to the last 1 year
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


def compute_yoy_growth(data, key_name):
    """Compute Year-over-Year growth for a given key in quarterly data.

    Args:
        data: List of dicts with 'date' and key_name fields.
        key_name: The field name to compute YoY growth for.

    Returns:
        List of {date, value} dicts with YoY growth percentages.
    """
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
        min_diff_days = 45
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


def calculate_slope(y_values):
    """Calculate the slope of a linear regression through y_values.

    Args:
        y_values: List of numeric values.

    Returns:
        The slope as a float.
    """
    if len(y_values) < 2:
        return 0.0
    n = len(y_values)
    x = list(range(n))
    sum_x = sum(x)
    sum_y = sum(y_values)
    sum_xx = sum(i * i for i in x)
    sum_xy = sum(i * y for i, y in zip(x, y_values))
    denominator = (n * sum_xx - sum_x * sum_x)
    if denominator == 0:
        return 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    return slope


def _quarter_key(dt):
    """Return a (year, quarter) tuple for a datetime object."""
    return (dt.year, (dt.month - 1) // 3 + 1)


def _quarter_date_label(year, quarter):
    """Return a date string like '2025-03-31' representing the quarter end."""
    month = quarter * 3
    last_day = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-{last_day:02d}"
