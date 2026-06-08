import re
from typing import Union, List

SOS_SYMPTOMS = [
    "chest pain",
    "seizure",
    "fainting",
    "stroke",
    "breathing difficulty",
    "shortness of breath",
    "severe bleeding",
    "loss of consciousness",
    "heart attack",
    "cant breathe",
    "can't breathe",
    "passed out",
    "unresponsive",
    "severe chest pressure",
    "sudden collapse",
    "difficulty breathing",
]

def check_sos(query: Union[str, List[str]]) -> dict:
    """
    Checks if the user's query (or a list of symptoms) contains any critical emergency symptoms.
    Uses rule-based word-boundary keyword matching.

    Args:
        query: Either a plain text string or a list of symptom strings from patient state.

    Returns:
        dict with keys: is_sos, matched_rules, severity
    """
    # Normalize: if a list is passed, join into one string
    if isinstance(query, list):
        text = " ".join(query).lower()
    else:
        text = query.lower()

    matched_rules = []
    for symptom in SOS_SYMPTOMS:
        pattern = r'\b' + re.escape(symptom) + r'\b'
        if re.search(pattern, text):
            if symptom not in matched_rules:
                matched_rules.append(symptom)

    is_sos = len(matched_rules) > 0

    return {
        "is_sos": is_sos,
        "matched_rules": matched_rules,
        "severity": "CRITICAL" if is_sos else "LOW"
    }
