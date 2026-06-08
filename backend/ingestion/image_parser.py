import os
from datetime import datetime
from backend.database.db import DatabaseManager
from backend.database.models import ImageRecord
from backend.rag.ollama_client import query_llava_image

def parse_medical_image(image_path: str, image_type: str = "general", patient_id: str = "patient_001") -> dict:
    """
    Ingests a medical image (X-ray, CT scan, MRI scan, ECG, blood report image):
    1. Call local Ollama LLaVA model to generate a detailed clinical description/observations.
    2. Prompt constraints: Generate observations only. Do NOT diagnose.
    3. Store the record in SQLite 'medical_images' table.
    Returns the generated clinical description and record dict.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    filename = os.path.basename(image_path)
    
    # Map raw image type to cleaner display term
    type_display = image_type.replace("_", " ").title()
    
    # Construct a clinical LLaVA prompt
    prompt = f"Analyze this clinical image ({type_display}).\n" \
             f"Provide a detailed, systematic description of the visual findings and observations.\n" \
             f"Highlight any structural abnormalities, anomalies, opacities, signal changes, or patterns visible.\n" \
             f"STRICT RULE: DO NOT diagnose a disease or condition. Describe only raw clinical findings and observations.\n" \
             f"Example: 'Chest radiograph showing mild bilateral opacities in the lower lobes without pleural effusion.'\n" \
             f"Keep your tone highly objective, descriptive, clinical, and precise."
             
    print(f"Calling local LLaVA vision model for image: {filename} ({image_type})...")
    observation = query_llava_image(image_path, prompt)
    print(f"LLaVA observation response: {observation[:200]}...")

    # Store in SQLite
    timestamp = datetime.utcnow().isoformat()
    record = ImageRecord(
        patient_id=patient_id,
        timestamp=timestamp,
        image_type=image_type,
        observation=observation,
        image_path=image_path
    )
    DatabaseManager.insert_image(record)
    print(f"Stored image observation in SQLite for {filename}.")

    return {
        "filename": filename,
        "image_type": image_type,
        "observation": observation,
        "timestamp": timestamp,
        "image_path": image_path
    }
