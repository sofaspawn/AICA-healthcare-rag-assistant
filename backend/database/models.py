import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class VitalsRecord(BaseModel):
    id: Optional[int] = None
    patient_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    spo2: Optional[float] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None

class AlertRecord(BaseModel):
    id: Optional[int] = None
    patient_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    severity: str
    score: int
    alerts: List[str] # Will be stored as JSON string in DB
    
    @classmethod
    def from_db(cls, row: dict):
        d = dict(row)
        if "alerts" in d and isinstance(d["alerts"], str):
            try:
                d["alerts"] = json.loads(d["alerts"])
            except:
                d["alerts"] = []
        return cls(**d)

class PatientHistoryRecord(BaseModel):
    id: Optional[int] = None
    patient_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    interaction_text: str
    extracted_symptoms: List[str] # JSON
    risk_score: int
    severity: str
    
    @classmethod
    def from_db(cls, row: dict):
        d = dict(row)
        if "extracted_symptoms" in d and isinstance(d["extracted_symptoms"], str):
            try:
                d["extracted_symptoms"] = json.loads(d["extracted_symptoms"])
            except:
                d["extracted_symptoms"] = []
        return cls(**d)

class MedicationRecord(BaseModel):
    id: Optional[int] = None
    patient_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    medicine: str
    dosage: str
    frequency: str
    source_file: Optional[str] = None

class LabResultRecord(BaseModel):
    id: Optional[int] = None
    patient_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    test: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    source_file: Optional[str] = None

class ImageRecord(BaseModel):
    id: Optional[int] = None
    patient_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    image_type: str
    observation: str
    image_path: str

class VideoRecord(BaseModel):
    id: Optional[int] = None
    patient_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    video_path: str
    summary: str
    observations: str

class RiskRecord(BaseModel):
    id: Optional[int] = None
    patient_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    risk_score: int
    reasons: List[str]
    severity: str

    @classmethod
    def from_db(cls, row: dict):
        d = dict(row)
        if "reasons" in d and isinstance(d["reasons"], str):
            try:
                d["reasons"] = json.loads(d["reasons"])
            except:
                d["reasons"] = []
        return cls(**d)

