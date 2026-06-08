import json
from backend.clinical.schemas import ExtractedClinicalData
from backend.rag.ollama_client import query_ollama_json

def extract_clinical_data(text: str) -> ExtractedClinicalData:
    """
    Extracts structured clinical data (symptoms, vitals, medications) from text using local Qwen2.5:7B.
    """
    prompt = f"Clinical text:\n{text}\n\n" \
             f"Extract symptoms, vitals, and medications mentioned in the text.\n" \
             f"Output MUST be a valid JSON object matching the following structure:\n" \
             f"{{\n" \
             f"  \"symptoms\": [\"string\"],\n" \
             f"  \"vitals\": {{\n" \
             f"    \"spo2\": float or null,\n" \
             f"    \"heart_rate\": float or null,\n" \
             f"    \"temperature\": float or null,\n" \
             f"    \"respiratory_rate\": float or null,\n" \
             f"    \"systolic_bp\": float or null,\n" \
             f"    \"diastolic_bp\": float or null\n" \
             f"  }},\n" \
             f"  \"medications\": [\"string\"]\n" \
             f"}}\n\n" \
             f"If a vitals field is not mentioned, set it to null. If symptoms or medications are not mentioned, return an empty list. " \
             f"Do not include markdown formatting or explanation. Output raw JSON only."
             
    system_prompt = "You are a clinical data extraction assistant. Extract symptoms, vitals, and medications from clinical text."
    
    try:
        data = query_ollama_json(prompt, system_prompt)
        if not isinstance(data, dict):
            data = {}
        if "vitals" not in data or not isinstance(data["vitals"], dict):
            data["vitals"] = {}
        # Ensure all vitals keys are present
        for key in ["spo2", "heart_rate", "temperature", "respiratory_rate", "systolic_bp", "diastolic_bp"]:
            data["vitals"].setdefault(key, None)
        data.setdefault("symptoms", [])
        data.setdefault("medications", [])
        return ExtractedClinicalData(**data)
    except Exception as e:
        print(f"Local clinical extraction error: {e}")
        return ExtractedClinicalData()

