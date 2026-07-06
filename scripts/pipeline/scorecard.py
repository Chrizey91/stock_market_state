"""Health Scorecard evaluation.

Evaluates each indicator against its threshold to produce a
healthy/unhealthy/unavailable status. This is the single source
of truth for scorecard metrics.
"""

import logging

from .indicators import calculate_slope

logger = logging.getLogger(__name__)


def evaluate_scorecard(indicators):
    """Evaluate the 12-metric Health Scorecard.

    Args:
        indicators: Dict of indicator key -> data (lists or dicts).

    Returns:
        Tuple of (scorecard_list, health_score, health_total).
    """
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

    # 8. forward_pe
    forward_pe_data = indicators.get("forward_pe", [])
    if forward_pe_data:
        latest = forward_pe_data[-1]
        val = latest.get("value")
        if val is not None:
            status = "healthy" if 14.0 <= val <= 22.0 else "unhealthy"
            display_val = f"{val:.2f}"
        else:
            status = "unavailable"
            display_val = None
    else:
        status = "unavailable"
        display_val = None
    scorecard.append({
        "id": "forward_pe",
        "label": "Forward P/E",
        "category": "Valuation",
        "status": status,
        "value": display_val
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
