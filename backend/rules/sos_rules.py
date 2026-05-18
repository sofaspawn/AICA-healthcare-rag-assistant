import re

SOS_SYMPTOMS = [
    "chest pain",
    "seizure",
    "fainting",
    "stroke",
    "breathing difficulty",
    "severe bleeding",
    "loss of consciousness",
    "heart attack",
    "cant breathe",
    "can't breathe",
    "passed out"
]

def check_sos(query: str) -> dict:
    """
    Checks if the user's query contains any critical emergency symptoms.
    Uses simple rule-based keyword matching.
    """
    query_lower = query.lower()
    matched_rules = []
    
    for symptom in SOS_SYMPTOMS:
        # Simple word boundary regex to avoid partial matches
        pattern = r'\b' + re.escape(symptom) + r'\b'
        if re.search(pattern, query_lower):
            matched_rules.append(symptom)
            
    is_sos = len(matched_rules) > 0
    
    return {
        "is_sos": is_sos,
        "matched_rules": matched_rules,
        "severity": "high" if is_sos else "low"
    }
