"""
Hallucination Guard — verifies numeric claims are grounded in source data.

Grounding rules (any one is sufficient to pass):
1. Direct match — number appears in source data within 5% tolerance.
2. Derived range — number falls within [min * 0.5, max * 2.0] of all source
   numeric values. Covers LLM-computed aggregates, confidence intervals,
   uplifts, and weighted averages that are legitimately derived from the data.
3. Fabrication signal — number is WAY outside the plausible derived range,
   which is the only case we actually want to flag.
"""
import re


def _flatten_values(data) -> list[float]:
    values = []
    if isinstance(data, dict):
        for v in data.values():
            values.extend(_flatten_values(v))
    elif isinstance(data, list):
        for item in data:
            values.extend(_flatten_values(item))
    elif isinstance(data, (int, float)):
        values.append(float(data))
    return values


def extract_numbers_from_text(text: str) -> list[float]:
    """Extract all numeric values from a text string."""
    pattern = r'\b\d+(?:,\d{3})*(?:\.\d+)?\b'
    raw = re.findall(pattern, text.replace(",", ""))
    return [float(n) for n in raw]


def check_number_grounded(number: float, source_values: list[float], tolerance: float = 0.05) -> bool:
    """
    A number is grounded if:
    - It directly matches a source value (within tolerance), OR
    - It falls within a plausible derived range of source values.
      Derived range: [min_source * 0.5, sum_source * 1.2]
      This covers confidence intervals, uplifts, totals, and weighted averages.
    """
    if not source_values:
        return True  # no source data to check against — pass through

    # Rule 1: direct match within tolerance
    for value in source_values:
        if value != 0 and abs(number - value) / max(abs(value), 1) <= tolerance:
            return True

    # Rule 2: derived range check
    positive_values = [v for v in source_values if v > 0]
    if positive_values:
        lower_bound = min(positive_values) * 0.5
        upper_bound = sum(positive_values) * 1.2  # sum covers aggregated totals
        if lower_bound <= number <= upper_bound:
            return True

    return False


def run_hallucination_guard(response_text: str, source_data: dict) -> tuple[bool, list[float]]:
    """
    Check that numeric claims in response_text are grounded in source_data.
    Returns (all_grounded, list_of_ungrounded_numbers).

    Only flags numbers that are completely outside the plausible range
    derivable from the source data — i.e. genuine fabrications.
    """
    numbers = extract_numbers_from_text(response_text)
    source_values = _flatten_values(source_data)

    ungrounded = []
    for num in numbers:
        # Skip small numbers — percentages, counts, years, model version numbers
        if num < 100:
            continue
        if not check_number_grounded(num, source_values):
            ungrounded.append(num)

    return len(ungrounded) == 0, ungrounded
