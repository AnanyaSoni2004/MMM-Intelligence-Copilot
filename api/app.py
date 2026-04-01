"""
MMM Intelligence Copilot — FastAPI REST API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from orchestrator.orchestrator import run as orchestrate
from agents import analyst_agent, forecast_agent, rag_agent, anomaly_agent
from rag.indexer import index_documents

app = FastAPI(
    title="MMM Intelligence Copilot",
    description="Multi-agent AI system for Marketing Mix Modeling analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    agent: Optional[str] = None  # If None, use orchestrator


class AnalystRequest(BaseModel):
    query: str
    time_period: str = "Q3_2024"
    channels: Optional[list[str]] = None


class ForecastRequest(BaseModel):
    query: str
    channels: Optional[list[str]] = None


class RAGRequest(BaseModel):
    query: str
    top_k: int = 5


class AnomalyRequest(BaseModel):
    query: str
    data: Optional[list[dict]] = None


@app.on_event("startup")
async def startup():
    """Index documents on startup if not already indexed."""
    try:
        index_documents()
    except Exception as e:
        print(f"Warning: Could not index documents on startup: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "service": "MMM Intelligence Copilot"}


@app.post("/query")
def query(req: QueryRequest):
    """Main endpoint — routes to orchestrator or specific agent."""
    result = orchestrate(req.query)
    return result


@app.post("/agents/analyst")
def analyst(req: AnalystRequest):
    """Direct MMM Analyst Agent endpoint."""
    result = analyst_agent.run(req.query, time_period=req.time_period, channels=req.channels)
    return result


@app.post("/agents/forecast")
def forecast(req: ForecastRequest):
    """Direct Forecast Agent endpoint."""
    result = forecast_agent.run(req.query, channels=req.channels)
    return result


@app.post("/agents/rag")
def rag(req: RAGRequest):
    """Direct RAG Insight Agent endpoint."""
    result = rag_agent.run(req.query, top_k=req.top_k)
    return result


@app.post("/agents/anomaly")
def anomaly(req: AnomalyRequest):
    """Direct Anomaly Detection Agent endpoint."""
    result = anomaly_agent.run(req.query, data=req.data)
    return result


@app.post("/index")
def reindex():
    """Re-index the knowledge base."""
    index_documents(force_reindex=True)
    return {"status": "reindexed"}


if __name__ == "__main__":
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
