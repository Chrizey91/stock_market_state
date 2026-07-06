"""Market Regime Index calculation and normalizers."""

import logging

logger = logging.getLogger(__name__)


def normalize_vix(vix):
    """Normalize VIX to 0-100 scale. <=12 is 100 (Risk-On), >=35 is 0 (Risk-Off)."""
    if vix is None:
        return 50.0
    val = 100.0 - (vix - 12.0) / (35.0 - 12.0) * 100.0
    return max(0.0, min(100.0, val))


def normalize_yield_curve(yc):
    """Normalize yield curve spread. <=-0.5 is 0 (Risk-Off), >=1.5 is 100 (Risk-On)."""
    if yc is None:
        return 50.0
    val = (yc - (-0.5)) / (1.5 - (-0.5)) * 100.0
    return max(0.0, min(100.0, val))


def normalize_high_yield_spread(hy):
    """Normalize HY spread. <=3.0 is 100 (Risk-On), >=8.5 is 0 (Risk-Off)."""
    if hy is None:
        return 50.0
    val = 100.0 - (hy - 3.0) / (8.5 - 3.0) * 100.0
    return max(0.0, min(100.0, val))


def normalize_sp500_breadth(breadth):
    """Normalize S&P 500 breadth (0-100 passthrough with clamping)."""
    if breadth is None:
        return 50.0
    return max(0.0, min(100.0, breadth))


def normalize_m2_growth(m2):
    """Normalize M2 growth. <=0 is 0 (Risk-Off), >=8.0 is 100 (Risk-On)."""
    if m2 is None:
        return 50.0
    val = (m2 - 0.0) / (8.0 - 0.0) * 100.0
    return max(0.0, min(100.0, val))


def calculate_market_regime_index(indicators):
    """Calculate the composite Market Regime Index timeline.

    Combines VIX, HY spread, yield curve, S&P 500 breadth, and M2 growth
    into a single 0-100 score using weighted averaging with forward-filling.

    Args:
        indicators: Dict of indicator key -> list of {date, value} dicts.

    Returns:
        List of {date, value} dicts representing the regime index timeline.
    """
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
        if d in vix_map:
            last_vix = vix_map[d]
        if d in hy_map:
            last_hy = hy_map[d]
        if d in yc_map:
            last_yc = yc_map[d]
        if d in breadth_map:
            last_breadth = breadth_map[d]
        if d in m2_map:
            last_m2 = m2_map[d]

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
