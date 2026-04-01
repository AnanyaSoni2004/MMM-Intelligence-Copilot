"""
Input Validator — validates queries and blocks prompt injection attempts.
"""
import re

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+your\s+system\s+prompt",
    r"you\s+are\s+now\s+a\s+different\s+ai",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"output\s+your\s+system\s+prompt",
    r"reveal\s+your\s+instructions",
    r"forget\s+everything",
]

MIN_QUERY_LENGTH = 5
MAX_QUERY_LENGTH = 2000


class InputValidationError(Exception):
    pass


def validate_input(query: str) -> tuple[bool, str]:
    """
    Validate a user query.
    Returns (is_valid, reason).
    """
    if not query or not query.strip():
        return False, "Query is empty."

    if len(query.strip()) < MIN_QUERY_LENGTH:
        return False, f"Query too short (minimum {MIN_QUERY_LENGTH} characters)."

    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Query too long (maximum {MAX_QUERY_LENGTH} characters)."

    query_lower = query.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower):
            return False, "Query contains disallowed content (potential prompt injection detected)."

    return True, "OK"
