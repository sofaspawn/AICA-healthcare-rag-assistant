import json
import logging
from typing import Union, List
from backend.groq.provider import get_llm_provider

logger = logging.getLogger(__name__)

async def check_sos(query: Union[str, List[str]]) -> dict:
    """
    Checks if the user's query (or a list of symptoms) contains any critical emergency symptoms.
    Uses an LLM zero-shot classification via Groq.

    Args:
        query: Either a plain text string or a list of symptom strings from patient state.

    Returns:
        dict with keys: is_sos, matched_rules, severity
    """
    if isinstance(query, list):
        text = " ".join(query)
    else:
        text = query

    prompt = f"Text to evaluate:\n{text}\n\nDoes this text describe a life-threatening medical emergency or severe SOS situation (like stroke, heart attack, severe bleeding, sudden collapse)? Respond with ONLY a JSON object: {{\"is_sos\": boolean, \"matched_rules\": [list of strings]}}."
    system_prompt = "You are a critical SOS detection assistant. Determine if the input describes an extreme emergency. Respond ONLY with valid JSON."

    try:
        provider = get_llm_provider()
        response_str = await provider.generate(
            prompt,
            system_prompt,
            response_format={"type": "json_object"}
        )
        data = json.loads(response_str)
        is_sos = bool(data.get("is_sos", False))
        matched_rules = data.get("matched_rules", [])
        if not isinstance(matched_rules, list):
            matched_rules = []

        return {
            "is_sos": is_sos,
            "matched_rules": matched_rules,
            "severity": "CRITICAL" if is_sos else "LOW"
        }
    except Exception as e:
        logger.error(f"Groq SOS detection error: {e}")
        return {
            "is_sos": False,
            "matched_rules": [],
            "severity": "LOW"
        }
