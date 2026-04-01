"""
Output Parser — enforces Pydantic schemas on agent outputs.
"""
from pydantic import ValidationError
from schemas.analyst_schema import AnalystResponse
from schemas.forecast_schema import ForecastResponse
from schemas.rag_schema import RAGResponse
from schemas.anomaly_schema import AnomalyResponse

SCHEMA_MAP = {
    "analyst": AnalystResponse,
    "forecast": ForecastResponse,
    "rag": RAGResponse,
    "anomaly": AnomalyResponse,
}


def parse_and_validate(agent_type: str, data: dict) -> tuple[bool, object, list[str]]:
    """
    Parse and validate agent output against its Pydantic schema.
    Returns (success, parsed_object_or_None, list_of_errors).
    """
    schema = SCHEMA_MAP.get(agent_type)
    if not schema:
        return False, None, [f"Unknown agent type: {agent_type}"]

    try:
        obj = schema(**data)
        return True, obj, []
    except ValidationError as e:
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return False, None, errors
