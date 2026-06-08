import os
from datetime import datetime
from backend.database.db import DatabaseManager
from backend.database.models import LabResultRecord
from backend.ingestion.documents.pdf_parser import extract_pdf_text
from backend.ingestion.prescription_parser import get_ocr_reader
from backend.rag.ollama_client import query_ollama_json, query_ollama_text

def parse_lab_report(file_path: str, patient_id: str = "patient_001") -> dict:
    """
    Ingests a PDF or image lab report:
    1. Extract text (using pdfplumber/fitz for PDF or EasyOCR for image).
    2. Extract structured lab values using Qwen2.5:7B -> store in SQLite.
    3. Generate clinical interpretation text using Qwen2.5:7B -> to be stored in ChromaDB.
    Returns a dict containing extracted structured values and the interpretation text.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    
    ocr_text = ""
    if ext == ".pdf":
        print(f"Extracting PDF text from lab report: {filename}")
        ocr_text = extract_pdf_text(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        print(f"Running EasyOCR on lab report image: {filename}")
        reader = get_ocr_reader()
        results = reader.readtext(file_path)
        ocr_text = " ".join([res[1] for res in results])
    else:
        raise ValueError(f"Unsupported lab report format: {ext}")

    if not ocr_text.strip():
        print(f"No text extracted from lab report: {filename}")
        return {"values": [], "interpretation": "", "raw_text": ""}

    # 1. Extract structured lab values
    prompt_struct = f"Text from lab report:\n{ocr_text}\n\n" \
                    f"Extract all lab test measurements mentioned in the text. For each measurement, extract:\n" \
                    f"- test (the name of the test, e.g. Glucose, Hemoglobin, Cholesterol)\n" \
                    f"- value (the measured numeric value, e.g. 180, 12.5) - MUST be a number\n" \
                    f"- unit (the measurement unit, e.g. mg/dL, g/dL, mmol/L)\n" \
                    f"- reference_range (the reference range if provided, e.g. 70-100, < 200)\n\n" \
                    f"Format your output strictly as a JSON array of objects with keys: \"test\", \"value\", \"unit\", \"reference_range\". " \
                    f"If a value cannot be parsed as a number, ignore it. If no measurements are found, return []. " \
                    f"Do not include explanation or markdown formatting."
                    
    system_prompt_struct = "You are a clinical data extraction assistant. Extract structured lab measurements from text."
    
    values = query_ollama_json(prompt_struct, system_prompt_struct)
    if not isinstance(values, list):
        values = []

    # Store in SQLite
    timestamp = datetime.utcnow().isoformat()
    saved_values = []
    for item in values:
        test_name = item.get("test")
        val = item.get("value")
        unit = item.get("unit")
        
        if not test_name or val is None or not unit:
            continue
            
        try:
            val_float = float(val)
        except ValueError:
            continue
            
        record = LabResultRecord(
            patient_id=patient_id,
            timestamp=timestamp,
            test=test_name,
            value=val_float,
            unit=unit,
            reference_range=item.get("reference_range"),
            source_file=filename
        )
        DatabaseManager.insert_lab_result(record)
        saved_values.append(item)
        print(f"Saved lab result: {test_name} = {val_float} {unit} to SQLite.")

    # 2. Generate clinical interpretation text for ChromaDB
    interpretation = ""
    if saved_values:
        prompt_interp = f"Clinical Lab Measurements extracted from report:\n{saved_values}\n\n" \
                        f"Provide a clinical interpretation of these results.\n" \
                        f"Identify any values that are out of range or critical.\n" \
                        f"Briefly explain what these abnormalities could signify in a helpful, patient-centric manner.\n" \
                        f"DO NOT diagnose any condition; only mention potential observations and highlight abnormal values.\n" \
                        f"Keep the tone professional and objective."
        system_prompt_interp = "You are a cautious medical interpreter. Summarize and explain lab values without diagnosing."
        interpretation = query_ollama_text(prompt_interp, system_prompt_interp)
        print(f"Generated lab interpretation: {interpretation[:200]}...")

    return {
        "values": saved_values,
        "interpretation": interpretation,
        "raw_text": ocr_text
    }
