import os
import json
import base64
import logging
from datetime import datetime
from backend.database.db import DatabaseManager
from backend.database.models import LabResultRecord
from backend.ingestion.documents.pdf_parser import extract_pdf_text
from backend.groq.provider import get_llm_provider

logger = logging.getLogger(__name__)

async def parse_lab_report(file_path: str, patient_id: str = "patient_001") -> dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    
    ocr_text = ""
    base64_image = None
    
    if ext == ".pdf":
        ocr_text = extract_pdf_text(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        # Send directly to Groq Vision instead of EasyOCR
        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    else:
        raise ValueError(f"Unsupported lab report format: {ext}")

    provider = get_llm_provider()
    
    prompt_struct = f"Extract all lab test measurements mentioned. For each measurement, extract:\n" \
                    f"- test (the name of the test, e.g. Glucose, Hemoglobin, Cholesterol)\n" \
                    f"- value (the measured numeric value, e.g. 180, 12.5) - MUST be a number\n" \
                    f"- unit (the measurement unit, e.g. mg/dL, g/dL, mmol/L)\n" \
                    f"- reference_range (the reference range if provided, e.g. 70-100, < 200)\n\n" \
                    f"Format your output strictly as a JSON array of objects with keys: \"test\", \"value\", \"unit\", \"reference_range\". " \
                    f"If a value cannot be parsed as a number, ignore it. If no measurements are found, return []. " \
                    f"Do not include explanation or markdown formatting."
                    
    if base64_image:
        prompt_struct = "Analyze this lab report image.\n" + prompt_struct
    else:
        prompt_struct = f"Text from lab report:\n{ocr_text}\n\n" + prompt_struct
        
    system_prompt_struct = "You are a clinical data extraction assistant. Extract structured lab measurements."
    
    try:
        kwargs = {}
        if base64_image:
            kwargs["base64_image"] = base64_image
        else:
            kwargs["response_format"] = {"type": "json_object"}
            
        response_str = await provider.generate(prompt_struct, system_prompt_struct, **kwargs)
        
        cleaned = response_str.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1)
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        # If response_format wasn't used, we might get a raw array. If it was, we might get an object.
        # Let's try to parse
        parsed = json.loads(cleaned.strip())
        if isinstance(parsed, dict) and "measurements" in parsed:
            values = parsed["measurements"]
        elif isinstance(parsed, dict):
            # Sometimes models wrap array in some key
            values = list(parsed.values())[0] if parsed else []
        else:
            values = parsed
            
        if not isinstance(values, list):
            values = []
    except Exception as e:
        logger.error(f"Failed to parse lab values via Groq: {e}")
        values = []

    timestamp = datetime.utcnow().isoformat()
    saved_values = []
    for item in values:
        if not isinstance(item, dict):
            continue
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

    interpretation = ""
    if saved_values:
        prompt_interp = f"Clinical Lab Measurements extracted from report:\n{saved_values}\n\n" \
                        f"Provide a clinical interpretation of these results.\n" \
                        f"Identify any values that are out of range or critical.\n" \
                        f"Briefly explain what these abnormalities could signify in a helpful, patient-centric manner.\n" \
                        f"DO NOT diagnose any condition; only mention potential observations and highlight abnormal values.\n" \
                        f"Keep the tone professional and objective."
        system_prompt_interp = "You are a cautious medical interpreter. Summarize and explain lab values without diagnosing."
        
        try:
            interpretation = await provider.generate(prompt_interp, system_prompt_interp)
        except Exception as e:
            logger.error(f"Failed to generate lab interpretation via Groq: {e}")

    return {
        "values": saved_values,
        "interpretation": interpretation,
        "raw_text": ocr_text if not base64_image else "(Extracted via Vision API)"
    }
