import os
from datetime import datetime
import easyocr
from backend.database.db import DatabaseManager
from backend.database.models import MedicationRecord
from backend.rag.ollama_client import query_ollama_json

# Global reader instance, initialized on demand
_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        print("Initializing EasyOCR reader (English)...")
        # Initialize easyocr reader. This will download model files on first run.
        _ocr_reader = easyocr.Reader(['en'], gpu=False) 
    return _ocr_reader

def parse_prescription_image(image_path: str, patient_id: str = "patient_001") -> list[dict]:
    """
    Ingests a scanned or photographed prescription image:
    1. Run OCR (EasyOCR) to extract raw text.
    2. Pass text to local Qwen2.5:7B to extract structured medications.
    3. Store each medication record in SQLite.
    Returns a list of structured medication dicts.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    filename = os.path.basename(image_path)
    reader = get_ocr_reader()
    
    # Run EasyOCR
    print(f"Running EasyOCR on: {filename}")
    results = reader.readtext(image_path)
    ocr_text = " ".join([res[1] for res in results])
    
    if not ocr_text.strip():
        print(f"No text extracted via OCR from {filename}")
        return []

    print(f"OCR text extracted: {ocr_text[:300]}...")

    # Query Qwen2.5 to extract medications
    prompt = f"OCR text from prescription image:\n{ocr_text}\n\n" \
             f"Extract all medications mentioned in the prescription. For each medication, extract:\n" \
             f"- medicine (the drug name, e.g. Metformin)\n" \
             f"- dosage (e.g. 500mg, 1 tablet)\n" \
             f"- frequency (e.g. twice daily, every 8 hours, 1-0-1)\n\n" \
             f"Format your output strictly as a JSON array of objects with keys: \"medicine\", \"dosage\", \"frequency\". " \
             f"If no medications are found, return an empty JSON array []. Do not include explanation or markdown formatting."
             
    system_prompt = "You are a clinical data extraction assistant. Extract structured medication records from OCR text."
    
    meds = query_ollama_json(prompt, system_prompt)
    if not isinstance(meds, list):
        meds = []

    # Store in SQLite and return
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
        print(f"Saved medication: {medicine_name} {med.get('dosage')} to SQLite.")

    return saved_meds
