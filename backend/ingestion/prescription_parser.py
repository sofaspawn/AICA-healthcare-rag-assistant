import os
import json
import base64
import logging
from datetime import datetime
from backend.database.db import DatabaseManager
from backend.database.models import MedicationRecord
from backend.groq.provider import get_llm_provider

logger = logging.getLogger(__name__)

async def parse_prescription_image(image_path: str, patient_id: str = "patient_001") -> list[dict]:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    filename = os.path.basename(image_path)
    
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    prompt = f"Analyze this prescription image.\n" \
             f"Extract all medications mentioned in the prescription. For each medication, extract:\n" \
             f"- medicine (the drug name, e.g. Metformin)\n" \
             f"- dosage (e.g. 500mg, 1 tablet)\n" \
             f"- frequency (e.g. twice daily, every 8 hours, 1-0-1)\n\n" \
             f"Format your output strictly as a JSON array of objects with keys: \"medicine\", \"dosage\", \"frequency\". " \
             f"If no medications are found, return an empty JSON array []. Do not include explanation or markdown formatting."
             
    system_prompt = "You are a clinical data extraction assistant. Extract structured medication records from prescription images."
    
    try:
        provider = get_llm_provider()
        # Note: Llama 3.2 Vision supports image input, but JSON output format might require prompting. 
        # Groq might throw an error if response_format={"type": "json_object"} is used with Vision models in preview.
        # We will request JSON in prompt and parse it manually.
        response_str = await provider.generate(
            prompt, 
            system_prompt, 
            base64_image=base64_image
        )
        
        # Cleanup potential markdown around JSON
        cleaned = response_str.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1)
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        meds = json.loads(cleaned.strip())
        
        if not isinstance(meds, list):
            meds = []
    except Exception as e:
        logger.error(f"Failed to parse prescription via Groq Vision: {e}")
        meds = []

    timestamp = datetime.utcnow().isoformat()
    saved_meds = []
    for med in meds:
        medicine_name = med.get("medicine")
        if not medicine_name:
            continue
        
        record = MedicationRecord(
            patient_id=patient_id,
            timestamp=timestamp,
            medicine=medicine_name,
            dosage=med.get("dosage", "N/A"),
            frequency=med.get("frequency", "N/A"),
            source_file=filename
        )
        DatabaseManager.insert_medication(record)
        saved_meds.append(med)
        logger.info(f"Saved medication: {medicine_name} {med.get('dosage')} to Supabase.")

    return saved_meds
