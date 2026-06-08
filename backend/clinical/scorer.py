from typing import Dict, Any, List
from backend.clinical.patient_state import PatientState
from backend.clinical.deterioration_rules import evaluate_vitals_rules
from backend.clinical.emergency_rules import EmergencyDetector

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
    triggered_reasons = []

    # 1. Base vitals score
    current_vitals = state.current_vitals
    if current_vitals:
        vitals_alerts = evaluate_vitals_rules(current_vitals)
        for alert in vitals_alerts:
            total_score += alert["score"]
            triggered_reasons.append(f"{alert['condition']} (+{alert['score']})")
            
    # 2. Trend modifiers
    if trend_score_modifier > 0:
        total_score += trend_score_modifier
        triggered_reasons.append(f"Deteriorating vitals trend (+{trend_score_modifier})")
        
    # 3. Emergency modifiers
    historic_emergency = False
    for sym in state.symptoms_history:
        for e_sym in EmergencyDetector.EMERGENCY_SYMPTOMS:
            if e_sym in sym.lower():
                historic_emergency = True
                if f"Persistent Emergency: {e_sym}" not in triggered_reasons:
                    triggered_reasons.append(f"Persistent Emergency: {e_sym}")

    if emergency_score_modifier > 0:
        total_score += emergency_score_modifier
        triggered_reasons.append(f"Emergency SOS symptoms detected (+{emergency_score_modifier})")
    elif historic_emergency:
        total_score += 50
        
    # 4. Progression / Symptom accumulation modifier
    if len(state.symptoms_history) >= 3:
        total_score += 15
        triggered_reasons.append(f"Multiple accumulated symptoms ({len(state.symptoms_history)} symptoms total) (+15)")
        
    # Cap score for safety bounds
    total_score = min(max(total_score, 0), 100)
    
    severity = calculate_severity_band(total_score)
    
    return {
        "risk_score": total_score,
        "severity": severity,
        "reasons": triggered_reasons if triggered_reasons else ["All tracked vitals and symptoms are within stable ranges"]
    }

