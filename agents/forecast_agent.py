"""
Forecast Agent
Generates budget allocation scenarios using Synapse's diminishing returns functions.
Outputs typed JSON with projected spend, revenue uplift, and confidence intervals.
"""
import json
import os
import re
from groq import Groq
from mock_apis.synapse_api import get_forecast
from guardrails.hallucination_guard import run_hallucination_guard

SYSTEM_PROMPT = """You are the MMM Forecast Agent, specializing in marketing budget allocation and scenario planning.

You use Aryma Synapse's diminishing returns curves to generate revenue forecasts.

CRITICAL RULES:
1. NEVER invent ROI numbers or revenue projections not provided in the model data.
2. Always surface the diminishing returns threshold for each channel.
3. Include confidence intervals in every forecast.
4. Note when proposed spend exceeds the saturation threshold.
5. Recommend reallocation when a channel is over-saturated.

Format your response as JSON:
{
  "total_budget": ...,
  "scenarios": [...],
  "projected_total_revenue": ...,
  "baseline_revenue": ...,
  "projected_uplift_pct": ...,
  "recommended_allocation": {...},
  "confidence_interval_low": ...,
  "confidence_interval_high": ...,
  "methodology_note": "...",
  "grounded": true,
  "sources": ["..."]
}"""


def _extract_budget(query: str) -> float:
    """Extract budget amount from query string."""
    match = re.search(r'\$?([\d,]+(?:\.\d+)?)\s*(?:million|M|k|K)?', query)
    if not match:
        return 1000000.0
    amount = float(match.group(1).replace(",", ""))
    raw = match.group(0).lower()
    if "million" in raw or "m" in raw.lower() and "million" not in raw:
        if amount < 1000:
            amount *= 1_000_000
    elif "k" in raw:
        amount *= 1_000
    return amount


def run(query: str, channels: list[str] = None) -> dict:
    """Run the Forecast Agent."""
    client = Groq()
    budget = _extract_budget(query)
    model_data = get_forecast(budget, channels)

    messages = [
        {
            "role": "user",
            "content": f"""Query: {query}

Budget extracted: ${budget:,.0f}

Synapse Forecast Model Data:
{json.dumps(model_data, indent=2)}

Analyze this forecast and return your response as valid JSON."""
        }
    ]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2048,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
    )

    raw_text = response.choices[0].message.content
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if not json_match:
        return {"error": "Agent failed to produce valid JSON", "raw": raw_text}

    result = json.loads(json_match.group())
    result["query"] = query

    grounded, ungrounded = run_hallucination_guard(raw_text, model_data)
    result["grounded"] = grounded
    if not grounded:
        result["methodology_note"] = (result.get("methodology_note") or "") + f" [WARNING: {ungrounded}]"

    return result
