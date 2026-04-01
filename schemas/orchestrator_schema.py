from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum

class IntentType(str, Enum):
    ATTRIBUTION = "attribution"
    FORECAST = "forecast"
    RESEARCH = "research"
    ANOMALY = "anomaly"
    MULTI_DOMAIN = "multi_domain"
    UNKNOWN = "unknown"

class OrchestratorResponse(BaseModel):
    query: str
    intent: IntentType
    agents_called: list[str]
    response: Any = Field(..., description="The actual agent response(s)")
    processing_time_ms: float
    guardrails_passed: bool
    flagged_issues: list[str] = Field(default_factory=list)
