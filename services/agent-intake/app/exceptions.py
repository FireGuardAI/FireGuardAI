"""Custom exceptions — never let raw library errors leak into API
responses. Each maps to a specific HTTP status in main.py.
"""


class IntakeError(Exception):
    """Base exception for the intake agent domain."""


class IntakeEngineError(IntakeError):
    """Raised when the Groq API call itself fails (auth, quota, network,
    timeout — after retries are exhausted)."""


class IntakeResponseParsingError(IntakeError):
    """Raised when Groq's response isn't valid JSON, or doesn't match
    the expected SanitizedBuildingDetails schema."""


class GuardrailRejection(IntakeError):
    """Raised when the input fails a safety or domain-relevance check.

    Deliberately NOT a subclass of a generic catch-all in main.py's error
    handling — this must map to 400, and must never be swallowed by a
    broader `except Exception` the way the reference doc's blanket
    handler did (see main.py's docstring for the full story)."""

    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.reason = reason  # "unsafe_input" or "off_topic"
