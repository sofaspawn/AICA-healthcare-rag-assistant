import os
import json
from openai import OpenAI
from backend.clinical.schemas import ExtractedClinicalData

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
)

def extract_clinical_data(text: str) -> ExtractedClinicalData:
    """
    Extracts structured clinical data (symptoms, vitals, medications) from user text.
    """
    system_prompt = """You are a medical data extraction assistant.
Extract symptoms, vitals, and medications from the user's text.
Output MUST be a valid JSON object matching the following structure:
{
  "symptoms": ["string"],
  "vitals": {
    "spo2": float or null,
    "heart_rate": float or null,
    "temperature": float or null,
    "respiratory_rate": float or null,
    "systolic_bp": float or null,
    "diastolic_bp": float or null
  },
  "medications": ["string"]
}

If a field is not present in the text, return null or empty list as appropriate. DO NOT add markdown block formatting around the JSON output, return raw JSON.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]
    
    try:
        response = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        json_str = response.choices[0].message.content
        data = json.loads(json_str)
        return ExtractedClinicalData(**data)
    except Exception as e:
        print(f"Extraction error: {e}")
        # Return empty data on failure
        return ExtractedClinicalData()
