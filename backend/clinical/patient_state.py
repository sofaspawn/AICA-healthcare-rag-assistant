from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from backend.clinical.schemas import ExtractedClinicalData, ExtractedVitals
from backend.database.models import VitalsRecord
from backend.database.db import DatabaseManager

@dataclass
class PatientState:
    patient_id: str
    vitals_history: List[VitalsRecord] = field(default_factory=list)
    symptoms_history: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    
    @property
    def current_vitals(self) -> Optional[VitalsRecord]:
        return self.vitals_history[-1] if self.vitals_history else None

def get_patient_state(patient_id: str) -> PatientState:
    """
    Retrieves the patient state by loading vitals history and symptoms from DB.
    """
    vitals_history = DatabaseManager.get_vitals_history(patient_id, limit=20)
    history_records = DatabaseManager.get_patient_history(patient_id, limit=100)
    
    symptoms_history = []
    for record in history_records:
        symptoms_history.extend(record.extracted_symptoms)
        
    symptoms_history = list(set(symptoms_history))
    
    return PatientState(
        patient_id=patient_id,
        vitals_history=vitals_history,
        symptoms_history=symptoms_history
    )

def update_patient_state(patient_id: str, extracted_data: ExtractedClinicalData) -> PatientState:
    """
    Updates the patient state with newly extracted data and persists vitals to DB.
    """
    state = get_patient_state(patient_id)
    
    # Check if there are any new vitals to record
    v = extracted_data.vitals
    if any(val is not None for val in [v.spo2, v.heart_rate, v.temperature, v.respiratory_rate, v.systolic_bp, v.diastolic_bp]):
        record = VitalsRecord(
            patient_id=patient_id,
            spo2=v.spo2,
            heart_rate=v.heart_rate,
            temperature=v.temperature,
            respiratory_rate=v.respiratory_rate,
            systolic_bp=v.systolic_bp,
            diastolic_bp=v.diastolic_bp
        )
        DatabaseManager.insert_vitals(record)
        state.vitals_history.append(record)
        
    # Append symptoms
    state.symptoms_history.extend(extracted_data.symptoms)
    # Ensure uniqueness
    state.symptoms_history = list(set(state.symptoms_history))
    
    return state
