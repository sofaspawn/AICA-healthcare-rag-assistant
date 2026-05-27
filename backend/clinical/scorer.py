from typing import Dict, Any, List
from backend.clinical.patient_state import PatientState
from backend.clinical.deterioration_rules import evaluate_vitals_rules

def calculate_severity_band(score: int) -> str:
    if score >= 70:
        return "CRITICAL"
    elif score >= 40:
        return "HIGH"
    elif score >= 20:
        return "MEDIUM"
    return "LOW"

def score_patient(state: PatientState, trend_score_modifier: int = 0, emergency_score_modifier: int = 0) -> Dict[str, Any]:
    """
    Calculates total risk score based on vitals, trends, and emergencies.
    """
    total_score = 0
    triggered_alerts = []

    # 1. Base vitals score
    current_vitals = state.current_vitals
    if current_vitals:
        vitals_alerts = evaluate_vitals_rules(current_vitals)
        for alert in vitals_alerts:
            total_score += alert["score"]
            triggered_alerts.append(alert["condition"])
            
    # 2. Add modifiers
    total_score += trend_score_modifier
    total_score += emergency_score_modifier
    
    # Cap score for safety bounds
    total_score = min(max(total_score, 0), 100)
    
    severity = calculate_severity_band(total_score)
    
    return {
        "score": total_score,
        "severity": severity,
        "alerts": triggered_alerts
    }
