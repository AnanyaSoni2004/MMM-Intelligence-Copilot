"""
LLM-as-Judge — uses Claude to score agent response quality.
"""
import json
import re
from groq import Groq

client = Groq()

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator of MMM (Marketing Mix Modeling) AI agent responses.

Score the response on these dimensions (0-10 each):
1. Accuracy: Are the numbers and facts correct and consistent?
2. Groundedness: Are claims traceable to provided data/sources?
3. Completeness: Does the response address all parts of the query?
4. Clarity: Is the response clear and well-structured?
5. Refusal_quality: If the agent should have refused (out-of-domain, fabrication risk), did it do so appropriately?

Return JSON: {
  "accuracy": 0-10,
  "groundedness": 0-10,
  "completeness": 0-10,
  "clarity": 0-10,
  "refusal_quality": 0-10,
  "overall": 0-10,
  "reasoning": "...",
  "pass": true|false
}

Pass threshold: overall >= 7"""


def judge_response(query: str, response: dict, golden: dict) -> dict:
    """Score an agent response using LLM-as-judge."""
    messages = [
        {
            "role": "user",
            "content": f"""Query: {query}

Agent Response:
{json.dumps(response, indent=2)}

Golden Test Case Requirements:
{json.dumps(golden, indent=2)}

Score this response and return JSON."""
        }
    ]

    result = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=512,
        messages=[{"role": "system", "content": JUDGE_SYSTEM_PROMPT}] + messages,
    )

    raw = result.choices[0].message.content
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"error": "Judge failed to return valid JSON", "raw": raw}
