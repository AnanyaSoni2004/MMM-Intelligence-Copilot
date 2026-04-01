from pydantic import BaseModel, Field
from typing import Optional

class SpendScenario(BaseModel):
    channel: str
    current_spend: float = Field(..., ge=0)
    proposed_spend: float = Field(..., ge=0)
    expected_roi: float
    expected_revenue_uplift: float
    confidence_interval_low: float
    confidence_interval_high: float
    diminishing_returns_threshold: Optional[float] = Field(None, description="Spend level beyond which returns flatten significantly")

class ForecastResponse(BaseModel):
    query: str
    total_budget: float = Field(..., ge=0)
    scenarios: list[SpendScenario]
    projected_total_revenue: float = Field(..., ge=0)
    baseline_revenue: float = Field(..., ge=0)
    projected_uplift_pct: float
    recommended_allocation: dict[str, float] = Field(..., description="Channel -> recommended spend")
    confidence_interval_low: float
    confidence_interval_high: float
    methodology_note: str
    grounded: bool = Field(True)
    sources: list[str]
