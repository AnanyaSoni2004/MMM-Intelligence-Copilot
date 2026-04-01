"""
MMM Intelligence Copilot Orchestrator
Classifies intent and routes to appropriate specialist agents.
Supports parallel execution for multi-domain queries.
"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq
from guardrails.input_validator import validate_input
from agents import analyst_agent, forecast_agent, rag_agent, anomaly_agent

client = Groq()

INTENT_SYSTEM_PROMPT = """You classify marketing analytics queries into one of these intents:
- attribution: Questions about past ROI, channel performance, or historical attribution
- forecast: Questions about future spend, budget allocation, or scenario planning
- research: Questions about methodology, benchmarks, case studies, or best practices
- anomaly: Questions about data quality, feed issues, or anomaly detection
- multi_domain: Queries that span multiple intents above

Return ONLY a JSON object: {"intent": "...", "sub_intents": ["...", "..."], "reasoning": "..."}"""


def classify_intent(query: str) -> dict:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=256,
        messages=[
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
    )
    raw = response.choices[0].message.content
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"intent": "unknown", "sub_intents": [], "reasoning": "Classification failed"}


def _run_agent(agent_type: str, query: str) -> tuple[str, dict]:
    """Run a single agent and return (agent_type, result)."""
    try:
        if agent_type == "attribution":
            # Extract time period from query
            period_match = re.search(r'Q[1-4][\s_]?20\d{2}', query, re.IGNORECASE)
            period = period_match.group().replace(" ", "_").upper() if period_match else "Q3_2024"
            return "attribution", analyst_agent.run(query, time_period=period)
        elif agent_type == "forecast":
            return "forecast", forecast_agent.run(query)
        elif agent_type == "research":
            return "research", rag_agent.run(query)
        elif agent_type == "anomaly":
            return "anomaly", anomaly_agent.run(query)
        else:
            return agent_type, {"error": f"Unknown agent type: {agent_type}"}
    except Exception as e:
        return agent_type, {"error": str(e)}


def run(query: str) -> dict:
    """Main orchestrator entry point."""
    start_time = time.time()
    flagged_issues = []

    # Gate 1: Input validation
    is_valid, reason = validate_input(query)
    if not is_valid:
        return {
            "query": query,
            "intent": "blocked",
            "agents_called": [],
            "response": {"error": reason},
            "processing_time_ms": 0,
            "guardrails_passed": False,
            "flagged_issues": [reason],
        }

    # Classify intent
    intent_result = classify_intent(query)
    intent = intent_result.get("intent", "unknown")
    sub_intents = intent_result.get("sub_intents", [])

    if intent == "unknown":
        return {
            "query": query,
            "intent": intent,
            "agents_called": [],
            "response": {"error": "Could not determine query intent. Please rephrase your question."},
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "guardrails_passed": True,
            "flagged_issues": ["Unknown intent"],
        }

    # Determine which agents to call
    if intent == "multi_domain" and sub_intents:
        agents_to_call = [i for i in sub_intents if i in ["attribution", "forecast", "research", "anomaly"]]
    else:
        agents_to_call = [intent] if intent in ["attribution", "forecast", "research", "anomaly"] else []

    if not agents_to_call:
        agents_to_call = ["research"]  # fallback to RAG

    # Run agents (in parallel if multiple)
    results = {}
    if len(agents_to_call) == 1:
        agent_type, result = _run_agent(agents_to_call[0], query)
        results[agent_type] = result
    else:
        with ThreadPoolExecutor(max_workers=len(agents_to_call)) as executor:
            futures = {executor.submit(_run_agent, a, query): a for a in agents_to_call}
            for future in as_completed(futures):
                agent_type, result = future.result()
                results[agent_type] = result

    # Check for agent errors
    for agent_type, result in results.items():
        if "error" in result:
            flagged_issues.append(f"{agent_type}: {result['error']}")
        if not result.get("grounded", True):
            flagged_issues.append(f"{agent_type}: hallucination guard triggered")

    processing_time = round((time.time() - start_time) * 1000, 2)

    return {
        "query": query,
        "intent": intent,
        "agents_called": agents_to_call,
        "response": results if len(results) > 1 else list(results.values())[0],
        "processing_time_ms": processing_time,
        "guardrails_passed": len(flagged_issues) == 0,
        "flagged_issues": flagged_issues,
    }
