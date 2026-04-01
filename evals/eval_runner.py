"""
Eval Runner — runs golden set evaluations for all agents.
"""
import json
import os
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import track

from agents import analyst_agent, forecast_agent, rag_agent, anomaly_agent
from evals.llm_judge import judge_response

console = Console()

GOLDEN_DIR = Path(__file__).parent / "golden_sets"

AGENT_MAP = {
    "analyst": (analyst_agent, "analyst_golden.json"),
    "forecast": (forecast_agent, "forecast_golden.json"),
    "rag": (rag_agent, "rag_golden.json"),
    "anomaly": (anomaly_agent, "anomaly_golden.json"),
}


def run_analyst_eval(golden: dict) -> dict:
    query = golden["query"]
    period_match = __import__("re").search(r'Q[1-4][\s_]?20\d{2}', query, __import__("re").IGNORECASE)
    period = period_match.group().replace(" ", "_").upper() if period_match else "Q3_2024"
    return analyst_agent.run(query, time_period=period)


def run_forecast_eval(golden: dict) -> dict:
    return forecast_agent.run(golden["query"])


def run_rag_eval(golden: dict) -> dict:
    return rag_agent.run(golden["query"])


def run_anomaly_eval(golden: dict) -> dict:
    return anomaly_agent.run(golden["query"])


AGENT_RUNNERS = {
    "analyst": run_analyst_eval,
    "forecast": run_forecast_eval,
    "rag": run_rag_eval,
    "anomaly": run_anomaly_eval,
}


def check_required_fields(response: dict, required_fields: list[str]) -> tuple[bool, list[str]]:
    missing = [f for f in required_fields if f not in response]
    return len(missing) == 0, missing


def run_evals(agent_name: str = None, use_llm_judge: bool = False) -> dict:
    """Run evaluations for one or all agents."""
    agents_to_eval = [agent_name] if agent_name else list(AGENT_MAP.keys())
    all_results = {}

    for name in agents_to_eval:
        if name not in AGENT_MAP:
            console.print(f"[red]Unknown agent: {name}[/red]")
            continue

        _, golden_file = AGENT_MAP[name]
        golden_path = GOLDEN_DIR / golden_file

        if not golden_path.exists():
            console.print(f"[yellow]Golden set not found: {golden_path}[/yellow]")
            continue

        goldens = json.loads(golden_path.read_text())
        runner = AGENT_RUNNERS[name]

        console.print(f"\n[bold blue]Running evals for: {name.upper()} agent[/bold blue]")

        results = []
        for golden in track(goldens, description=f"  {name}"):
            start = time.time()
            try:
                response = runner(golden)
                elapsed = round((time.time() - start) * 1000, 2)

                # Field check
                required = golden.get("expected_fields", [])
                fields_ok, missing = check_required_fields(response, required)

                # Grounded check
                grounded = response.get("grounded", True)

                result = {
                    "id": golden["id"],
                    "query": golden["query"],
                    "fields_ok": fields_ok,
                    "missing_fields": missing,
                    "grounded": grounded,
                    "has_error": "error" in response,
                    "elapsed_ms": elapsed,
                    "response": response,
                    "golden": golden,
                }

                if use_llm_judge:
                    result["judge_scores"] = judge_response(golden["query"], response, golden)

                results.append(result)

            except Exception as e:
                results.append({
                    "id": golden["id"],
                    "query": golden["query"],
                    "error": str(e),
                    "fields_ok": False,
                    "grounded": False,
                    "has_error": True,
                })

        # Summary
        passed = sum(1 for r in results if r.get("fields_ok") and not r.get("has_error"))
        all_results[name] = {
            "total": len(results),
            "passed": passed,
            "pass_rate": round(passed / len(results) * 100, 1) if results else 0,
            "results": results,
        }

        # Display table
        table = Table(title=f"{name.upper()} Agent Eval Results")
        table.add_column("ID", style="cyan")
        table.add_column("Pass", style="green")
        table.add_column("Grounded", style="blue")
        table.add_column("Time (ms)")
        table.add_column("Issues")

        for r in results:
            table.add_row(
                r.get("id", "?"),
                "✓" if r.get("fields_ok") and not r.get("has_error") else "✗",
                "✓" if r.get("grounded", True) else "✗",
                str(r.get("elapsed_ms", "N/A")),
                ", ".join(r.get("missing_fields", [])) or r.get("error", ""),
            )

        console.print(table)
        console.print(f"  Pass rate: {all_results[name]['pass_rate']}%")

    return all_results


if __name__ == "__main__":
    run_evals()
