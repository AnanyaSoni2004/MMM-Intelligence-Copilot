from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AnomalyType(str, Enum):
    MISSING_CHANNEL = "missing_channel"
    SPEND_SPIKE = "spend_spike"
    SPEND_DROP = "spend_drop"
    DATA_DRIFT = "data_drift"
    IMPLAUSIBLE_VALUE = "implausible_value"
    MISSING_DATA = "missing_data"

class Anomaly(BaseModel):
    anomaly_id: str
    channel: str
    anomaly_type: AnomalyType
    severity: SeverityLevel
    detected_value: Optional[float] = None
    expected_range_low: Optional[float] = None
    expected_range_high: Optional[float] = None
    description: str
    recommended_action: str
    affected_date_range: Optional[str] = None

class AnomalyResponse(BaseModel):
    query: str
    dataset_summary: str
    anomalies_found: list[Anomaly]
    total_anomalies: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    safe_to_run_model: bool = Field(..., description="Whether data is clean enough to run MMM")
    grounded: bool = Field(True)
