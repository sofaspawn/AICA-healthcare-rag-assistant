import os
from datetime import datetime
from faster_whisper import WhisperModel
from backend.rag.ollama_client import query_ollama_json

# Global WhisperModel instance, lazy loaded
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("Loading local Faster Whisper model (tiny)...")
        # tiny model is fast, loads quickly, and occupies < 100MB RAM
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _whisper_model

def parse_audio_recording(audio_path: str, source_type: str = "audio_dictation", patient_id: str = "patient_001") -> dict:
    """
    Ingests an audio recording (patient symptom descriptions or doctor dictation):
    1. Transcribe audio to text using Faster Whisper.
    2. Extract list of symptoms from the transcript using Qwen2.5:7B.
    Returns a dict containing the transcript and list of extracted symptoms.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    filename = os.path.basename(audio_path)
    model = get_whisper_model()
    
    print(f"Transcribing audio with Faster Whisper: {filename}...")
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    # Accumulate transcription segments
    transcript = " ".join([segment.text for segment in segments]).strip()
    
    print(f"Transcript generated: {transcript}")

    # Extract symptoms from transcript
    symptoms = []
    if transcript:
        prompt = f"Transcript:\n{transcript}\n\n" \
                 f"Extract all symptoms, ailments, or health issues mentioned by the patient or doctor in the transcript.\n" \
                 f"Format your output strictly as a JSON array of strings, for example: [\"cough\", \"fever\", \"shortness of breath\"]. " \
                 f"If no symptoms are mentioned, return []. Do not include markdown code block formatting or explanation."
        system_prompt = "You are a clinical data extraction assistant. Extract symptoms from voice transcripts."
        symptoms = query_ollama_json(prompt, system_prompt)
        if not isinstance(symptoms, list):
            symptoms = []
            
    print(f"Extracted symptoms: {symptoms}")

    return {
        "filename": filename,
        "source_type": source_type,
        "transcript": transcript,
        "symptoms": symptoms,
        "timestamp": datetime.utcnow().isoformat()
    }
