import json
import logging
from typing import Dict, Any, List
from backend.groq.provider import get_llm_provider

logger = logging.getLogger(__name__)

class EmergencyDetector:
    @classmethod
    async def detect(cls, text: str, extracted_symptoms: List[str] = None) -> Dict[str, Any]:
        prompt = f"Patient Query: {text}\n"
        if extracted_symptoms:
            prompt += f"Extracted Symptoms: {', '.join(extracted_symptoms)}\n"
        prompt += "\nEvaluate if this situation indicates a medical emergency. Respond with ONLY a JSON object matching this structure: {\"is_emergency\": boolean, \"matched_symptoms\": [list of strings]}."
        
        system_prompt = "You are a medical emergency detection assistant. Determine if the given input describes an emergency (e.g., chest pain, stroke, seizure, severe bleeding). Respond ONLY with valid JSON."

        try:
            provider = get_llm_provider()
            response_str = await provider.generate(
                prompt,
                system_prompt,
                response_format={"type": "json_object"}
            )
            data = json.loads(response_str)
            is_emergency = bool(data.get("is_emergency", False))
            matched_symptoms = data.get("matched_symptoms", [])
            if not isinstance(matched_symptoms, list):
                matched_symptoms = []
            
            return {
                "is_emergency": is_emergency,
                "matched_symptoms": matched_symptoms,
                "score_modifier": 50 if is_emergency else 0
            }
        except Exception as e:
            logger.error(f"Groq emergency detection error: {e}")
            return {
                "is_emergency": False,
                "matched_symptoms": [],
                "score_modifier": 0
            }
