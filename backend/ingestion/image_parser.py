import os
import base64
import logging
from datetime import datetime
from backend.database.db import DatabaseManager
from backend.database.models import ImageRecord
from backend.groq.provider import get_llm_provider

logger = logging.getLogger(__name__)

async def parse_medical_image(image_path: str, image_type: str = "general", patient_id: str = "patient_001") -> dict:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    filename = os.path.basename(image_path)
    type_display = image_type.replace("_", " ").title()
    
    prompt = f"Analyze this clinical image ({type_display}).\n" \
             f"Provide a detailed, systematic description of the visual findings and observations.\n" \
             f"Highlight any structural abnormalities, anomalies, opacities, signal changes, or patterns visible.\n" \
             f"STRICT RULE: DO NOT diagnose a disease or condition. Describe only raw clinical findings and observations.\n" \
             f"Example: 'Chest radiograph showing mild bilateral opacities in the lower lobes without pleural effusion.'\n" \
             f"Keep your tone highly objective, descriptive, clinical, and precise."
             
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    try:
        provider = get_llm_provider()
        observation = await provider.generate(prompt=prompt, base64_image=base64_image)
    except Exception as e:
        logger.error(f"Groq vision error: {e}")
        observation = "Failed to analyze image due to API error."

    timestamp = datetime.utcnow().isoformat()
    record = ImageRecord(
        patient_id=patient_id,
        timestamp=timestamp,
        image_type=image_type,
        observation=observation,
        image_path=image_path
    )
    DatabaseManager.insert_image(record)

    return {
        "filename": filename,
        "image_type": image_type,
        "observation": observation,
        "timestamp": timestamp,
        "image_path": image_path
    }
