"""
Shared clinical utility functions used by both FastAPI (main.py) and the Streamlit app.
Kept separate to avoid importing the FastAPI app object into Streamlit.
"""
from datetime import datetime
from backend.clinical.extraction import extract_clinical_data
from backend.clinical.emergency_rules import EmergencyDetector
from backend.clinical.trend_analysis import TrendAnalyzer
from backend.clinical.scorer import score_patient
from backend.clinical.alert_engine import AlertEngine
from backend.clinical.patient_state import get_patient_state, update_patient_state
from backend.database.db import DatabaseManager
from backend.database.models import PatientHistoryRecord, RiskRecord


def preprocess_and_update_state(patient_id: str, text: str, source_file: str) -> dict:
    """
    Runs clinical extraction on a text block, updates patient state, scores risk,
    fires alerts, and logs a risk record to SQLite.
    Used after ingesting any clinical document.
    """
    extracted_data = extract_clinical_data(text)
    state = update_patient_state(patient_id, extracted_data)

    trend_result = TrendAnalyzer.analyze(state.vitals_history)
    emergency_result = EmergencyDetector.detect(text, state.symptoms_history)
    score_result = score_patient(
        state,
        trend_score_modifier=trend_result["score_modifier"],
        emergency_score_modifier=emergency_result["score_modifier"],
    )

    all_alerts = list(
        set(score_result["reasons"] + trend_result["details"] + emergency_result["matched_symptoms"])
    )
    AlertEngine.process_alerts(patient_id, score_result["severity"], score_result["risk_score"], all_alerts)

    DatabaseManager.insert_risk(
        RiskRecord(
            patient_id=patient_id,
            timestamp=datetime.utcnow().isoformat(),
            risk_score=score_result["risk_score"],
            reasons=score_result["reasons"],
            severity=score_result["severity"],
        )
    )

    return {
        "symptoms": extracted_data.symptoms,
        "vitals": extracted_data.vitals.dict(),
        "risk_score": score_result["risk_score"],
        "severity": score_result["severity"],
    }


def log_interaction(patient_id: str, interaction_text: str, symptoms: list, source_file: str):
    """
    Appends a patient interaction record to the SQLite history table.
    Used after any upload or ingestion event to maintain the clinical timeline.
    """
    state = get_patient_state(patient_id)
    score_result = score_patient(state)

    history_record = PatientHistoryRecord(
        patient_id=patient_id,
        timestamp=datetime.utcnow().isoformat(),
        interaction_text=f"{interaction_text} (File: {source_file})",
        extracted_symptoms=symptoms,
        risk_score=score_result["risk_score"],
        severity=score_result["severity"],
    )
    DatabaseManager.insert_history(history_record)
