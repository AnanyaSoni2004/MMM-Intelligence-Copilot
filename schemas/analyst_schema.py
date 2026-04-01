from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ChannelAttribution(BaseModel):
    channel: str = Field(..., description="Marketing channel name")
    spend: float = Field(..., ge=0, description="Spend in USD")
    revenue_attributed: float = Field(..., ge=0, description="Revenue attributed to this channel")
    roi: float = Field(..., description="Return on investment (revenue/spend)")
    contribution_pct: float = Field(..., ge=0, le=100, description="Percentage contribution to total revenue")

class AnalystResponse(BaseModel):
    query: str = Field(..., description="Original user query")
    time_period: str = Field(..., description="Time period analyzed")
    channels: list[ChannelAttribution] = Field(..., description="Per-channel attribution data")
    total_spend: float = Field(..., ge=0)
    total_attributed_revenue: float = Field(..., ge=0)
    overall_roi: float = Field(...)
    confidence: ConfidenceLevel = Field(...)
    sources: list[str] = Field(..., description="Model run IDs or data sources used")
    caveats: Optional[str] = Field(None, description="Any limitations or caveats")
    grounded: bool = Field(True, description="Whether all numbers are traceable to model output")
