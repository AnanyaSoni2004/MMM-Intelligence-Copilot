"""
MMM Analyst Agent
Wraps the Synapse API to answer attribution questions in natural language.
Enforces: never fabricate numbers not present in model output.
"""
import json
import os
import re
from groq import Groq
from mock_apis.synapse_api import get_attribution
from guardrails.hallucination_guard import run_hallucination_guard

client = Groq()

SYSTEM_PROMPT = """You are the MMM Analyst Agent, a specialist in Marketing Mix Modeling attribution analysis.

You have access to Aryma Synapse MMM model outputs. Your job is to answer attribution questions accurately.

CRITICAL RULES:
1. NEVER fabricate or estimate numbers not present in the provided model data.
2. ALWAYS cite the model run ID and time period when reporting numbers.
3. If data for a requested channel or time period is not available, say so explicitly.
4. Report ROI as revenue/spend ratios, not as percentages unless asked.
5. Always include a caveat if the confidence level is low.

When the user asks about attribution, you will receive structured model data. Use ONLY that data to answer.
Format your response as JSON matching this structure:
{
  "time_period": "...",
  "channels": [{"channel": "...", "spend": ..., "revenue_attributed": ..., "roi": ..., "contribution_pct": ...}],
  "total_spend": ...,
  "total_attributed_revenue": ...,
  "overall_roi": ...,
  "confidence": "high|medium|low",
  "sources": ["run_id"],
  "caveats": "...",
  "grounded": true
}"""


def run(query: str, time_period: str = "Q3_2024", channels: list[str] = None) -> dict:
    """Run the MMM Analyst Agent."""
    # Fetch ground-truth data from Synapse
    model_data = get_attribution(time_period, channels)

    messages = [
        {
            "role": "user",
            "content": f"""Query: {query}

Available Synapse Model Data:
{json.dumps(model_data, indent=2)}

Answer the query using ONLY the data above. Return valid JSON."""
        }
    ]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2048,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
    )

    raw_text = response.choices[0].message.content

    # Extract JSON from response
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if not json_match:
        return {"error": "Agent failed to produce valid JSON", "raw": raw_text}

    result = json.loads(json_match.group())
    result["query"] = query

    # Hallucination guard
    grounded, ungrounded = run_hallucination_guard(raw_text, model_data)
    result["grounded"] = grounded
    if not grounded:
        result["caveats"] = (result.get("caveats") or "") + f" [WARNING: Unverified numbers detected: {ungrounded}]"

    return result
