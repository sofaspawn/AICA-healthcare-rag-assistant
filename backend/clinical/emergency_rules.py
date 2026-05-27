import re
from typing import Dict, Any, List

class EmergencyDetector:
    EMERGENCY_SYMPTOMS = [
        "chest pain",
        "seizure",
        "fainting",
        "stroke",
        "severe bleeding",
        "loss of consciousness",
        "heart attack",
        "shortness of breath",
        "cant breathe",
        "can't breathe",
        "passed out"
    ]

    @classmethod
    def detect(cls, text: str, extracted_symptoms: List[str] = None) -> Dict[str, Any]:
        text_lower = text.lower()
        matched_rules = []
        
        # Check text via regex
        for symptom in cls.EMERGENCY_SYMPTOMS:
            pattern = r'\b' + re.escape(symptom) + r'\b'
            if re.search(pattern, text_lower):
                if symptom not in matched_rules:
                    matched_rules.append(symptom)
                    
        # Check extracted symptoms explicitly
        if extracted_symptoms:
            for s in extracted_symptoms:
                s_lower = s.lower()
                for e_symptom in cls.EMERGENCY_SYMPTOMS:
                    if e_symptom in s_lower and e_symptom not in matched_rules:
                        matched_rules.append(e_symptom)
                        
        is_emergency = len(matched_rules) > 0
        
        return {
            "is_emergency": is_emergency,
            "matched_symptoms": matched_rules,
            "score_modifier": 50 if is_emergency else 0
        }
