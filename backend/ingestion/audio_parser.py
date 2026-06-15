import os
import json
import logging
from datetime import datetime
from backend.groq.provider import get_llm_provider

logger = logging.getLogger(__name__)

async def parse_audio_recording(audio_path: str, source_type: str = "audio_dictation", patient_id: str = "patient_001") -> dict:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    filename = os.path.basename(audio_path)
    provider = get_llm_provider()
    
    transcript = ""
    try:
        # Use Groq's whisper model
        with open(audio_path, "rb") as file:
            response = await provider.client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3",
            )
            transcript = response.text.strip()
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")

    symptoms = []
    if transcript:
        prompt = f"Transcript:\n{transcript}\n\n" \
                 f"Extract all symptoms, ailments, or health issues mentioned by the patient or doctor in the transcript.\n" \
                 f"Format your output strictly as a JSON array of strings, for example: [\"cough\", \"fever\", \"shortness of breath\"]. " \
                 f"If no symptoms are mentioned, return []. Do not include markdown code block formatting or explanation."
        system_prompt = "You are a clinical data extraction assistant. Extract symptoms from voice transcripts."
        
        try:
            response_str = await provider.generate(prompt, system_prompt, response_format={"type": "json_object"})
            
            cleaned = response_str.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            
            if isinstance(parsed, dict):
                # might be wrapped in 'symptoms': [...]
                symptoms = parsed.get("symptoms", list(parsed.values())[0] if parsed else [])
            elif isinstance(parsed, list):
                symptoms = parsed
        except Exception as e:
            logger.error(f"Failed to extract symptoms from audio via Groq: {e}")

    return {
        "filename": filename,
        "source_type": source_type,
        "transcript": transcript,
        "symptoms": symptoms,
        "timestamp": datetime.utcnow().isoformat()
    }
