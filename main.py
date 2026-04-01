"""
MMM Intelligence Copilot — CLI Entry Point
"""
import os
import json
import typer
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.prompt import Prompt
from dotenv import load_dotenv

load_dotenv()

from rag.indexer import index_documents
from orchestrator.orchestrator import run as orchestrate

app = typer.Typer(help="MMM Intelligence Copilot — Multi-Agent AI for Marketing Mix Modeling")
console = Console()


def ensure_api_key():
    if not os.getenv("GROQ_API_KEY"):
        console.print("[red]Error: GROQ_API_KEY not set. Copy .env.example to .env and add your key.[/red]")
        raise typer.Exit(1)


@app.command()
def setup():
    """Index knowledge base documents."""
    ensure_api_key()
    console.print("[blue]Indexing MMM knowledge base...[/blue]")
    index_documents(force_reindex=True)
    console.print("[green]Setup complete![/green]")


@app.command()
def query(
    q: str = typer.Option(None, "--query", "-q", help="Query to run"),
    agent: str = typer.Option(None, "--agent", "-a", help="Specific agent: analyst|forecast|rag|anomaly"),
    period: str = typer.Option("Q3_2024", "--period", "-p", help="Time period for analyst agent"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Run a query through the MMM Intelligence Copilot."""
    ensure_api_key()

    if not q:
        q = Prompt.ask("[bold]Enter your query[/bold]")

    console.print(f"\n[dim]Processing: {q}[/dim]\n")

    if agent:
        from agents import analyst_agent, forecast_agent, rag_agent, anomaly_agent
        agent_map = {
            "analyst": lambda: analyst_agent.run(q, time_period=period),
            "forecast": lambda: forecast_agent.run(q),
            "rag": lambda: rag_agent.run(q),
            "anomaly": lambda: anomaly_agent.run(q),
        }
        if agent not in agent_map:
            console.print(f"[red]Unknown agent: {agent}. Choose from: {list(agent_map.keys())}[/red]")
            raise typer.Exit(1)
        result = agent_map[agent]()
    else:
        result = orchestrate(q)

    if json_output:
        console.print(JSON(json.dumps(result, indent=2)))
    else:
        console.print(Panel(
            JSON(json.dumps(result, indent=2)),
            title="MMM Intelligence Copilot Response",
            border_style="blue",
        ))

    if not result.get("guardrails_passed", True):
        console.print(f"\n[yellow]Guardrail flags: {result.get('flagged_issues', [])}[/yellow]")


@app.command()
def eval(
    agent: str = typer.Option(None, "--agent", "-a", help="Agent to eval (default: all)"),
    judge: bool = typer.Option(False, "--judge", help="Use LLM-as-judge scoring"),
):
    """Run evaluation harness."""
    ensure_api_key()

    # Ensure knowledge base is indexed for RAG evals
    index_documents()

    from evals.eval_runner import run_evals
    results = run_evals(agent_name=agent, use_llm_judge=judge)

    console.print("\n[bold green]Eval Summary[/bold green]")
    for name, data in results.items():
        status = "PASS" if data["pass_rate"] >= 80 else "FAIL"
        color = "green" if status == "PASS" else "red"
        console.print(f"  [{color}]{name}: {data['pass_rate']}% ({data['passed']}/{data['total']})[/{color}]")


@app.command()
def serve():
    """Start the FastAPI server."""
    ensure_api_key()
    import uvicorn
    console.print("[green]Starting MMM Intelligence Copilot API on http://localhost:8000[/green]")
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)


@app.command()
def chat():
    """Interactive chat mode."""
    ensure_api_key()
    index_documents()

    console.print(Panel(
        "[bold blue]MMM Intelligence Copilot[/bold blue]\n"
        "Ask questions about attribution, forecasting, methodology, or data quality.\n"
        "Type [bold]exit[/bold] to quit.",
        border_style="blue",
    ))

    while True:
        try:
            q = Prompt.ask("\n[bold green]You[/bold green]")
            if q.lower() in ["exit", "quit", "q"]:
                break

            result = orchestrate(q)

            # Display clean response
            response = result.get("response", {})
            intent = result.get("intent", "unknown")
            agents = result.get("agents_called", [])

            console.print(f"\n[dim]Intent: {intent} | Agents: {', '.join(agents)} | Time: {result.get('processing_time_ms', 0):.0f}ms[/dim]")
            console.print(Panel(
                JSON(json.dumps(response, indent=2, default=str)),
                title="Response",
                border_style="green",
            ))

            if not result.get("guardrails_passed", True):
                console.print(f"[yellow]Flags: {result.get('flagged_issues')}[/yellow]")

        except KeyboardInterrupt:
            break

    console.print("\n[dim]Goodbye![/dim]")


if __name__ == "__main__":
    app()
