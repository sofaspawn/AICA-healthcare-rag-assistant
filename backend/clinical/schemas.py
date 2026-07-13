from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class ExtractedVitals(BaseModel):
    spo2: Optional[float] = Field(None, description="Oxygen saturation (SpO2) percentage")
    heart_rate: Optional[float] = Field(None, description="Heart rate in beats per minute (BPM)")
    temperature: Optional[float] = Field(None, description="Body temperature in Fahrenheit or Celsius")
    respiratory_rate: Optional[float] = Field(None, description="Respiratory rate in breaths per minute")
    systolic_bp: Optional[float] = Field(None, description="Systolic blood pressure (top number)")
    diastolic_bp: Optional[float] = Field(None, description="Diastolic blood pressure (bottom number)")

class GraphRelationship(BaseModel):
    source: str
    target: str
    relation: str

class ExtractedClinicalData(BaseModel):
    symptoms: List[str] = Field(default_factory=list, description="List of symptoms mentioned by the patient")
    vitals: ExtractedVitals = Field(default_factory=ExtractedVitals, description="Vitals extracted from the text")
    medications: List[str] = Field(default_factory=list, description="List of medications mentioned")
    entities: List[str] = Field(default_factory=list, description="General medical entities (e.g., conditions, body parts, procedures)")
    relationships: List[GraphRelationship] = Field(default_factory=list, description="Relationships between entities (e.g., symptom -> body part)")
