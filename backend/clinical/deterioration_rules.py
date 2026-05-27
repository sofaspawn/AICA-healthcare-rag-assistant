from typing import List, Dict, Any
from backend.database.models import VitalsRecord

def evaluate_vitals_rules(vitals: VitalsRecord) -> List[Dict[str, Any]]:
    """
    Evaluates deterministic deterioration rules against current vitals.
    Returns a list of triggered rule dictionaries.
    """
    triggered_rules = []

    if vitals.spo2 is not None:
        if vitals.spo2 < 90:
            triggered_rules.append({"condition": "Critical Hypoxia (SpO2 < 90%)", "score": 40})
        elif vitals.spo2 < 94:
            triggered_rules.append({"condition": "Mild Hypoxia (SpO2 90-93%)", "score": 20})

    if vitals.heart_rate is not None:
        if vitals.heart_rate > 120:
            triggered_rules.append({"condition": "Severe Tachycardia (HR > 120)", "score": 30})
        elif vitals.heart_rate > 100:
            triggered_rules.append({"condition": "Tachycardia (HR > 100)", "score": 15})
        elif vitals.heart_rate < 50:
            triggered_rules.append({"condition": "Bradycardia (HR < 50)", "score": 20})

    if vitals.temperature is not None:
        if vitals.temperature > 103.0:
            triggered_rules.append({"condition": "High Fever (Temp > 103°F)", "score": 20})
        elif vitals.temperature > 100.4:
            triggered_rules.append({"condition": "Fever (Temp > 100.4°F)", "score": 10})

    if vitals.systolic_bp is not None:
        if vitals.systolic_bp < 90:
            triggered_rules.append({"condition": "Hypotension (Systolic BP < 90)", "score": 30})
        elif vitals.systolic_bp > 180:
            triggered_rules.append({"condition": "Hypertensive Crisis (Systolic BP > 180)", "score": 30})

    if vitals.respiratory_rate is not None:
        if vitals.respiratory_rate > 24:
            triggered_rules.append({"condition": "Tachypnea (RR > 24)", "score": 20})
        elif vitals.respiratory_rate < 12:
            triggered_rules.append({"condition": "Bradypnea (RR < 12)", "score": 20})

    return triggered_rules
