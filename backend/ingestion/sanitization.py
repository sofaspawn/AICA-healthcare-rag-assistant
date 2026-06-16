import os
import re

ENABLE_PHI_REDACTION = os.getenv("ENABLE_PHI_REDACTION", "true").lower() in ("true", "1", "yes")

# Basic regex patterns for PII/PHI
PII_PATTERNS = {
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
    "PHONE": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
}

def sanitize_text(text: str) -> str:
    """
    Redact basic PII/PHI if ENABLE_PHI_REDACTION is true.
    Replaces matches with placeholders like [REDACTED_SSN].
    """
    if not ENABLE_PHI_REDACTION:
        return text

    sanitized = text
    for pii_type, pattern in PII_PATTERNS.items():
        sanitized = re.sub(pattern, f"[REDACTED_{pii_type}]", sanitized)

    return sanitized
