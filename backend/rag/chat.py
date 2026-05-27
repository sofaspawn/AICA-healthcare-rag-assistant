import os
from openai import OpenAI
from backend.rag.retriever import retrieve_context
from backend.clinical.extraction import extract_clinical_data
from backend.clinical.patient_state import update_patient_state, get_patient_state
from backend.clinical.emergency_rules import EmergencyDetector
from backend.clinical.trend_analysis import TrendAnalyzer
from backend.clinical.scorer import score_patient
from backend.clinical.alert_engine import AlertEngine
from backend.database.models import PatientHistoryRecord
from backend.database.db import DatabaseManager
import json

# Groq exposes an OpenAI-compatible API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required but not set. "
                     "Set it in your .env file or export it in the shell.")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Create a persistent client to avoid "client has been closed" errors
_groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
)

def generate_chat_response(query: str, context_string: str, patient_context: str = "") -> str:
    """
    Generates a response using Groq API via the OpenAI-compatible client.
    """
    model_name = GROQ_MODEL
    
    system_prompt = """You are a highly cautious and helpful AI medical assistant.
Your goal is to answer the user's queries based SOLELY on the provided medical context and patient data.
You MUST follow these rules:
1. NEVER hallucinate medical diagnoses.
2. If the context does not contain the answer, explicitly state that you cannot answer based on the available information.
3. Always encourage the user to consult a qualified physician or healthcare professional for medical advice.
4. Explain your reasoning simply and clearly.
5. Be empathetic but maintain a professional, objective tone.
6. This system is an AI assistant and not a replacement for professional medical care.
7. If the Patient Context indicates HIGH or CRITICAL risk severity, or EMERGENCY symptoms, you MUST explicitly mention this severity to the user and strongly recommend immediate medical escalation (like visiting the ER or calling 911).

MEDICAL CONTEXT:
{context}

PATIENT CONTEXT:
{patient_context}
"""
    
    messages = [
        {"role": "system", "content": system_prompt.format(context=context_string, patient_context=patient_context)},
        {"role": "user", "content": query}
    ]
    
    response = _groq_client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.1, # Low temperature for more grounded/factual responses
    )
    
    return response.choices[0].message.content

def chat_pipeline(query: str, patient_id: str = "patient_001", uploaded_sources: list = None):
    """
    Phase 2 Chat Pipeline:
    1. Retrieve medical history
    2. Extract structured data
    3. Update patient state
    4. Run emergency detection
    5. Run trend analysis
    6. Run deterioration scoring
    7. Generate doctor alerts
    8. Generate final AI response
    """
    # 1. Retrieve RAG Context
    retrieval_data = retrieve_context(query, uploaded_sources=uploaded_sources)
    context_str = retrieval_data["context_string"]
    
    # 2. Extract structured data
    extracted_data = extract_clinical_data(query)
    
    # 3. Update patient state
    state = update_patient_state(patient_id, extracted_data)
    
    # 4. Run emergency detection (using ALL accumulated symptoms from state, not just current query)
    emergency_result = EmergencyDetector.detect(query, state.symptoms_history)
    
    # 5. Run trend analysis
    trend_result = TrendAnalyzer.analyze(state.vitals_history)
    
    # 6. Run deterioration scoring
    score_result = score_patient(
        state, 
        trend_score_modifier=trend_result["score_modifier"], 
        emergency_score_modifier=emergency_result["score_modifier"]
    )
    
    # Combine alerts from all systems
    all_alerts = score_result["alerts"] + trend_result["details"] + emergency_result["matched_symptoms"]
    # De-duplicate alerts
    all_alerts = list(set(all_alerts))
    
    # 7. Generate doctor alerts
    AlertEngine.process_alerts(patient_id, score_result["severity"], score_result["score"], all_alerts)
    
    # Log patient history to DB
    history_record = PatientHistoryRecord(
        patient_id=patient_id,
        interaction_text=query,
        extracted_symptoms=extracted_data.symptoms,
        risk_score=score_result["score"],
        severity=score_result["severity"]
    )
    DatabaseManager.insert_history(history_record)
    
    # 8. Generate final AI response
    patient_context = f"Severity: {score_result['severity']}, Score: {score_result['score']}\n"
    if all_alerts:
        patient_context += f"Active Alerts: {', '.join(all_alerts)}\n"
        
    try:
        response_text = generate_chat_response(query, context_str, patient_context)
    except Exception as e:
        response_text = f"Error generating response: {str(e)}"
        
    return {
        "response": response_text,
        "retrieved_context": retrieval_data["metadata"],
        "is_emergency": emergency_result["is_emergency"],
        "emergency_symptoms": emergency_result["matched_symptoms"],
        "risk_score": score_result["score"],
        "severity": score_result["severity"],
        "alerts": all_alerts,
        "trend": trend_result
    }
