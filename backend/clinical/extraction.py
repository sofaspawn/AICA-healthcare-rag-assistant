import json
import logging
from backend.clinical.schemas import ExtractedClinicalData, GraphRelationship
from backend.groq.provider import get_llm_provider

logger = logging.getLogger(__name__)

async def extract_clinical_data(text: str) -> ExtractedClinicalData:
    """
    Extracts structured clinical data (symptoms, vitals, medications, entities, relationships) from text using Groq.
    """
    prompt = f"Clinical text:\n{text}\n\n" \
             f"Extract symptoms, vitals, medications, medical entities (conditions, body parts), and relationships.\n" \
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
             f"  \"medications\": [\"string\"],\n" \
             f"  \"entities\": [\"string\"],\n" \
             f"  \"relationships\": [{{\"source\": \"string\", \"target\": \"string\", \"relation\": \"string\"}}]\n" \
             f"}}\n\n" \
             f"If a field is not mentioned, set it to null or an empty list. " \
             f"Do not include markdown formatting or explanation. Output raw JSON only."
             
    system_prompt = "You are a clinical data extraction assistant. Extract symptoms, vitals, medications, entities, and relationships from clinical text."
    
    try:
        provider = get_llm_provider()
        response_str = await provider.generate(
            prompt, 
            system_prompt,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response_str)
        if not isinstance(data, dict):
            data = {}
        if "vitals" not in data or not isinstance(data["vitals"], dict):
            data["vitals"] = {}
        # Ensure all vitals keys are present
        for key in ["spo2", "heart_rate", "temperature", "respiratory_rate", "systolic_bp", "diastolic_bp"]:
            data["vitals"].setdefault(key, None)
        data.setdefault("symptoms", [])
        data.setdefault("medications", [])
        data.setdefault("entities", [])
        data.setdefault("relationships", [])
        
        # Format relationships
        rels = []
        for r in data["relationships"]:
            if isinstance(r, dict) and "source" in r and "target" in r and "relation" in r:
                rels.append(GraphRelationship(**r))
        data["relationships"] = rels

        return ExtractedClinicalData(**data)
    except Exception as e:
        logger.error(f"Groq clinical extraction error: {e}")
        return ExtractedClinicalData()
