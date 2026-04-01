# MMM Intelligence Copilot

A multi-agent AI system for Marketing Mix Modeling (MMM) analysts. Query your MMM models in natural language, get ROI forecasts, retrieve cited insights from research documents, and catch data anomalies — all with production-grade guardrails.

Built with **Groq** (LLaMA 3.3 70B), **ChromaDB**, and **FastAPI**.

---

## What It Does

You talk to it like a colleague. It figures out what you're asking, routes to the right specialist agent, and returns structured, grounded answers.

```
"What was Facebook's ROI in Q3 2024?"           → MMM Analyst Agent
"Allocate a $2M budget across channels"         → Forecast Agent
"What is adstock and how does it work?"         → RAG Insight Agent
"Check my data feed for anomalies"              → Anomaly Detection Agent
"What was email ROI in Q2 and should I scale?"  → Both agents, in parallel
```

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────┐
│     Input Validator         │  ← blocks empty queries, prompt injection
└─────────────┬───────────────┘
              │
    ▼
┌─────────────────────────────┐
│       Orchestrator          │  ← classifies intent, routes to agent(s)
└──┬──────┬──────┬────────┬───┘
   │      │      │        │
   ▼      ▼      ▼        ▼
Analyst  Fore- RAG    Anomaly
Agent   cast  Agent   Agent
         Agent
   │      │      │        │
   └──────┴──────┴────────┘
              │
    ▼
┌─────────────────────────────┐
│   Hallucination Guard       │  ← checks numbers are traceable to source data
│   Output Parser (Pydantic)  │  ← enforces typed schemas
└─────────────────────────────┘
              │
    ▼
  Response
```

### The Four Agents

| Agent | Does | Data Source |
|---|---|---|
| **MMM Analyst** | Attribution questions — past ROI, channel performance, revenue contribution | Mock Synapse API |
| **Forecast** | Budget allocation scenarios, diminishing returns curves, revenue uplift projections | Mock Synapse API |
| **RAG Insight** | Methodology questions, benchmarks, case studies — answers grounded in retrieved documents | ChromaDB (4 knowledge docs) |
| **Anomaly Detection** | Scans data feeds for missing channels, spend spikes, negative values, data drift | Raw feed data |

### Guardrails (3 layers, non-negotiable)

1. **Input Validator** — rejects empty queries and prompt injection attempts
2. **Output Parser** — Pydantic v2 schemas on all agent outputs; fails loudly if the LLM hallucinates a field
3. **Hallucination Guard** — checks that every numeric claim in a response is traceable to source data

---

## Project Structure

```
MMM_AgenticAI/
├── main.py                        # CLI entry point
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── analyst_agent.py           # Attribution queries
│   ├── forecast_agent.py          # Budget scenario planning
│   ├── rag_agent.py               # Knowledge base Q&A
│   └── anomaly_agent.py           # Data feed monitoring
│
├── orchestrator/
│   └── orchestrator.py            # Intent classification + routing
│
├── guardrails/
│   ├── input_validator.py         # Prompt injection detection
│   ├── output_parser.py           # Pydantic schema enforcement
│   └── hallucination_guard.py     # Numeric claim traceability
│
├── rag/
│   ├── indexer.py                 # ChromaDB + MiniLM-L6-v2 embeddings
│   ├── retriever.py               # Cosine similarity retrieval
│   └── sample_docs/
│       ├── mmm_methodology.txt    # Adstock, saturation, model quality
│       ├── channel_benchmarks.txt # Industry ROI benchmarks by channel
│       ├── case_studies.txt       # 4 real-world MMM case studies
│       └── data_quality_guide.txt # Pre-run data quality checklist
│
├── mock_apis/
│   ├── synapse_api.py             # Simulated MMM attribution + forecast data
│   └── nebula_api.py              # Delegates to ChromaDB retriever
│
├── schemas/                       # Pydantic v2 output schemas
│   ├── analyst_schema.py
│   ├── forecast_schema.py
│   ├── rag_schema.py
│   ├── anomaly_schema.py
│   └── orchestrator_schema.py
│
├── evals/
│   ├── golden_sets/               # 19 hand-labeled test cases (4 agents)
│   │   ├── analyst_golden.json
│   │   ├── forecast_golden.json
│   │   ├── rag_golden.json
│   │   └── anomaly_golden.json
│   ├── eval_runner.py             # Full eval harness with Rich tables
│   └── llm_judge.py               # LLM-as-judge (5 scoring dimensions)
│
└── api/
    └── app.py                     # FastAPI REST API
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get a free Groq API key

Go to [console.groq.com](https://console.groq.com) → sign up free → API Keys → Create Key

### 3. Add your key

```bash
cp .env.example .env
# Edit .env and paste your key:
# GROQ_API_KEY=gsk_your_key_here
```

### 4. Index the knowledge base

```bash
python main.py setup
```

This downloads the `all-MiniLM-L6-v2` embedding model and indexes the 4 MMM knowledge documents into ChromaDB. One-time step.

---

## Usage

### Interactive chat (recommended)

```bash
python main.py chat
```

### Single query

```bash
python main.py query -q "What was Facebook's ROI in Q3 2024?"

# Target a specific agent
python main.py query -q "What is adstock?" --agent rag
python main.py query -q "Allocate $1.5M across channels" --agent forecast
python main.py query -q "Q2 2024 channel performance" --agent analyst --period Q2_2024

# Raw JSON output
python main.py query -q "Check data for anomalies" --json
```

### REST API

```bash
python main.py serve
# API docs at http://localhost:8000/docs
```

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `POST` | `/query` | Main endpoint — auto-routes via orchestrator |
| `POST` | `/agents/analyst` | Direct analyst agent |
| `POST` | `/agents/forecast` | Direct forecast agent |
| `POST` | `/agents/rag` | Direct RAG agent |
| `POST` | `/agents/anomaly` | Direct anomaly agent |
| `POST` | `/index` | Re-index knowledge base |
| `GET` | `/health` | Health check |

Example:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What was email ROI in Q1 2024?"}'
```

### Eval harness

```bash
# Run all agent evals
python main.py eval

# Run one agent
python main.py eval --agent analyst

# With LLM-as-judge scoring
python main.py eval --judge
```

---

## Sample Questions to Try

**Attribution**
- `What was Facebook's ROI in Q3 2024?`
- `Which channel had the highest ROI in Q1 2024?`
- `Compare Google Search and Facebook performance in Q4 2024`

**Forecasting**
- `If I have a $2 million budget, how should I allocate it across channels?`
- `What revenue uplift can I expect with a $1.5M budget?`
- `Which channels are over-saturated at a $3M spend level?`

**Research / Methodology**
- `What is adstock and how does it work?`
- `What is the typical ROI for email marketing?`
- `How many weeks of data do I need for a reliable MMM run?`
- `What happened in the CPG brand case study?`

**Anomaly Detection**
- `Check my marketing data feed for anomalies before the model run`
- `Is the data clean enough to run the MMM model?`

**Multi-domain (runs two agents in parallel)**
- `What was email ROI in Q2 2024 and should I increase the budget?`

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | LLaMA 3.3 70B via Groq (free) |
| Vector DB | ChromaDB (local, persistent) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Schemas | Pydantic v2 |
| API | FastAPI + Uvicorn |
| CLI | Typer + Rich |

---

## Understanding the Output

Every response includes:

- `intent` — what the orchestrator classified the query as
- `agents_called` — which agent(s) ran
- `grounded` — whether all numeric claims are traceable to source data (`false` = hallucination guard triggered)
- `guardrails_passed` — overall pass/fail across all three guardrail layers
- `flagged_issues` — list of any guardrail violations
- `processing_time_ms` — end-to-end latency

### Note on `grounded: false`

The hallucination guard flags numbers in LLM responses that it cannot directly match to the raw source data. LLM-computed values (e.g. confidence intervals derived from model data) will trigger this even when correct. A `grounded: false` flag means **review the numbers**, not that the response is wrong.

---

## Eval Harness

19 golden test cases across 4 agents:

| Agent | Test Cases | What's tested |
|---|---|---|
| Analyst | 5 | Attribution accuracy, required fields, no fabrication |
| Forecast | 5 | CI inclusion, budget extraction, over-saturation detection |
| RAG | 6 | Citation quality, out-of-domain refusal, context grounding |
| Anomaly | 3 | Anomaly detection, severity classification, safe-to-run flag |

LLM-as-judge scores on 5 dimensions: **Accuracy, Groundedness, Completeness, Clarity, Refusal Quality**. Pass threshold: overall ≥ 7/10.
