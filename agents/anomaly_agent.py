"""
Anomaly Detection Agent
Monitors marketing data feeds for drift, missing channels, or implausible values.
Fires structured alerts with severity and recommended action.
"""
import json
import os
import re
import uuid
import numpy as np
from groq import Groq

client = Groq()

SYSTEM_PROMPT = """You are the MMM Anomaly Detection Agent. You analyze marketing data feeds for quality issues before they corrupt a model run.

You detect:
- Missing channel data (zeros where spend was expected)
- Spend spikes (>3x trailing average)
- Spend drops (>70% below trailing average)
- Implausible values (negative numbers, extreme outliers)
- Data drift (significant distribution shift)
- Missing data (null values, incomplete time series)

For each anomaly, assign severity:
- critical: Will definitely corrupt the model run
- high: Will likely corrupt the model run
- medium: May affect model accuracy
- low: Minor issue, model can proceed with caveat

Format response as JSON:
{
  "dataset_summary": "...",
  "anomalies_found": [
    {
      "anomaly_id": "uuid",
      "channel": "...",
      "anomaly_type": "missing_channel|spend_spike|spend_drop|data_drift|implausible_value|missing_data",
      "severity": "critical|high|medium|low",
      "detected_value": ...,
      "expected_range_low": ...,
      "expected_range_high": ...,
      "description": "...",
      "recommended_action": "...",
      "affected_date_range": "..."
    }
  ],
  "total_anomalies": ...,
  "critical_count": ...,
  "high_count": ...,
  "medium_count": ...,
  "low_count": ...,
  "safe_to_run_model": true|false,
  "grounded": true
}"""


def _compute_stats(data: list[dict]) -> dict:
    """Compute basic statistics for anomaly detection."""
    channels = {}
    for row in data:
        ch = row.get("channel", "unknown")
        spend = row.get("spend", 0)
        if ch not in channels:
            channels[ch] = []
        channels[ch].append(spend)

    stats = {}
    for ch, spends in channels.items():
        arr = np.array(spends, dtype=float)
        stats[ch] = {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "zeros": int(np.sum(arr == 0)),
            "negatives": int(np.sum(arr < 0)),
            "values": spends,
        }
    return stats


def run(query: str, data: list[dict] = None) -> dict:
    """Run the Anomaly Detection Agent."""
    if data is None:
        # Generate sample data with anomalies for demo
        import random
        random.seed(42)
        channels = ["facebook", "google_search", "tv", "email", "display"]
        data = []
        for week in range(12):
            for ch in channels:
                spend = random.uniform(50000, 300000)
                # Inject anomalies
                if ch == "display" and week == 8:
                    spend = 0  # Missing data
                if ch == "facebook" and week == 10:
                    spend = 950000  # Spike
                if ch == "email" and week == 5:
                    spend = -1200  # Negative value
                data.append({"week": week + 1, "channel": ch, "spend": round(spend, 2)})

    stats = _compute_stats(data)

    messages = [
        {
            "role": "user",
            "content": f"""Query: {query}

Data Statistics (computed from the feed):
{json.dumps(stats, indent=2)}

Raw Data Sample (first 30 rows):
{json.dumps(data[:30], indent=2)}

Total rows: {len(data)}
Channels present: {list(stats.keys())}

Analyze for anomalies and return your findings as valid JSON."""
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

    # Assign UUIDs to anomalies if missing
    for anomaly in result.get("anomalies_found", []):
        if not anomaly.get("anomaly_id"):
            anomaly["anomaly_id"] = str(uuid.uuid4())

    return result
