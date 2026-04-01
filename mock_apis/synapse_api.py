"""
Mock MMM Synapse API
Simulates Aryma Labs' Synapse attribution and forecasting API.
In production, replace with actual Synapse API calls.
"""
import random
from typing import Optional
from datetime import datetime

CHANNEL_BASELINES = {
    "facebook": {"base_roi": 2.8, "base_spend": 250000, "base_revenue": 700000},
    "google_search": {"base_roi": 4.2, "base_spend": 180000, "base_revenue": 756000},
    "tv": {"base_roi": 1.9, "base_spend": 400000, "base_revenue": 760000},
    "email": {"base_roi": 8.5, "base_spend": 30000, "base_revenue": 255000},
    "display": {"base_roi": 1.4, "base_spend": 90000, "base_revenue": 126000},
    "youtube": {"base_roi": 2.1, "base_spend": 120000, "base_revenue": 252000},
    "radio": {"base_roi": 1.6, "base_spend": 80000, "base_revenue": 128000},
    "influencer": {"base_roi": 3.1, "base_spend": 60000, "base_revenue": 186000},
}

MODEL_RUNS = {
    "Q1_2024": "run_abc123",
    "Q2_2024": "run_def456",
    "Q3_2024": "run_ghi789",
    "Q4_2024": "run_jkl012",
    "Q1_2025": "run_mno345",
    "Q2_2025": "run_pqr678",
    "Q3_2025": "run_stu901",
}


def get_attribution(time_period: str, channels: Optional[list[str]] = None) -> dict:
    """Return simulated attribution data for a given time period."""
    run_id = MODEL_RUNS.get(time_period.upper().replace(" ", "_"), "run_latest_001")

    if channels is None:
        channels = list(CHANNEL_BASELINES.keys())

    # Add slight variance per period
    seed = hash(time_period) % 1000
    random.seed(seed)

    channel_data = []
    total_revenue = 0
    total_spend = 0

    for ch in channels:
        if ch.lower() not in CHANNEL_BASELINES:
            continue
        base = CHANNEL_BASELINES[ch.lower()]
        variance = random.uniform(0.85, 1.15)
        spend = base["base_spend"] * variance
        revenue = base["base_revenue"] * variance
        roi = revenue / spend
        channel_data.append({
            "channel": ch,
            "spend": round(spend, 2),
            "revenue_attributed": round(revenue, 2),
            "roi": round(roi, 2),
        })
        total_revenue += revenue
        total_spend += spend

    for ch in channel_data:
        ch["contribution_pct"] = round((ch["revenue_attributed"] / total_revenue) * 100, 2)

    return {
        "run_id": run_id,
        "time_period": time_period,
        "channels": channel_data,
        "total_spend": round(total_spend, 2),
        "total_attributed_revenue": round(total_revenue, 2),
        "overall_roi": round(total_revenue / total_spend, 2),
        "model_version": "synapse_v3.2",
    }


def get_forecast(budget: float, channels: Optional[list[str]] = None, periods: int = 4) -> dict:
    """Return simulated forecast/scenario data for a given budget."""
    if channels is None:
        channels = list(CHANNEL_BASELINES.keys())

    scenarios = []
    total_baseline = 0
    total_projected = 0

    for ch in channels:
        if ch.lower() not in CHANNEL_BASELINES:
            continue
        base = CHANNEL_BASELINES[ch.lower()]
        # Proportional budget allocation based on historical ROI
        weight = base["base_roi"] / sum(CHANNEL_BASELINES[c]["base_roi"] for c in channels if c in CHANNEL_BASELINES)
        proposed_spend = budget * weight

        # Diminishing returns: ROI decreases as spend increases beyond threshold
        dr_threshold = base["base_spend"] * 1.4
        if proposed_spend > dr_threshold:
            effective_roi = base["base_roi"] * (dr_threshold / proposed_spend) ** 0.3
        else:
            effective_roi = base["base_roi"] * (proposed_spend / base["base_spend"]) ** 0.1

        projected_revenue = proposed_spend * effective_roi
        ci_margin = projected_revenue * 0.12

        total_baseline += base["base_revenue"]
        total_projected += projected_revenue

        scenarios.append({
            "channel": ch,
            "current_spend": base["base_spend"],
            "proposed_spend": round(proposed_spend, 2),
            "expected_roi": round(effective_roi, 2),
            "expected_revenue_uplift": round(projected_revenue - base["base_revenue"], 2),
            "confidence_interval_low": round(projected_revenue - ci_margin, 2),
            "confidence_interval_high": round(projected_revenue + ci_margin, 2),
            "diminishing_returns_threshold": round(dr_threshold, 2),
        })

    return {
        "total_budget": budget,
        "scenarios": scenarios,
        "projected_total_revenue": round(total_projected, 2),
        "baseline_revenue": round(total_baseline, 2),
        "projected_uplift_pct": round(((total_projected - total_baseline) / total_baseline) * 100, 2),
        "recommended_allocation": {s["channel"]: s["proposed_spend"] for s in scenarios},
        "confidence_interval_low": round(total_projected * 0.88, 2),
        "confidence_interval_high": round(total_projected * 1.12, 2),
        "model_run_id": "forecast_run_001",
    }
