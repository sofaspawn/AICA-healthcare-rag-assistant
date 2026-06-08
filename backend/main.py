import os
import json
import uuid
import io
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

# Always load .env from the project root, regardless of where uvicorn is invoked
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

from backend.rag.vector_store import get_vector_store
from backend.rag.retriever import retrieve_context
from backend.rag.chat import chat_pipeline
from backend.rules.sos_rules import check_sos
from backend.clinical.extraction import extract_clinical_data
from backend.clinical.emergency_rules import EmergencyDetector
from backend.clinical.trend_analysis import TrendAnalyzer
from backend.database.db import DatabaseManager
from backend.database.models import PatientHistoryRecord, RiskRecord
from backend.clinical.patient_state import get_patient_state

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "patient_001")

def resolve_patient_id(patient_id: str | None = None) -> str:
    return patient_id or DEFAULT_PATIENT_ID

app = FastAPI(title="Multimodal Clinical Intelligence Platform API")

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    print("✅ Multimodal Clinical Intelligence Platform API starting up...")
    print("   → Ensure Ollama is running: `ollama serve`")
    print("   → Models needed: qwen2.5:7b (text), llava (vision)")

class ChatRequest(BaseModel):
    query: str
    patient_id: str = DEFAULT_PATIENT_ID

class SearchRequest(BaseModel):
    query: str

@app.get("/health")
def health_check():
    import subprocess
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        ollama_running = result.returncode == 0
    except Exception:
        ollama_running = False
    return {
        "status": "ok",
        "message": "Multimodal Clinical Intelligence Platform is running.",
        "ollama_available": ollama_running
    }

# Silence Chrome DevTools request
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools():
    return {}

# Mount static files
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
def serve_frontend():
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Multimodal Clinical Intelligence Platform API is running. Use Streamlit UI on :8501"}

async def save_upload_file(upload_file: UploadFile) -> str:
    """Helper to save uploaded file to workspace scratch folder."""
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scratch", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, upload_file.filename)
    await upload_file.seek(0)
    content = await upload_file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    return file_path

@app.post("/upload/document")
async def upload_clinical_document(patient_id: str | None = None, file: UploadFile = File(...)):
    """Ingests PDF, TXT, or DOCX clinical documents, chunks, embeds, and stores in ChromaDB."""
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        # 1. Ingest document text
        from backend.ingestion.documents.ingest_doc import ingest_document
        doc_data = ingest_document(file_path)
        
        # 2. Build unified knowledge record
        from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
        record = create_unified_record(
            patient_id=pid,
            source_type="document",
            clinical_content=doc_data["cleaned_text"],
            metadata={"source_file": file.filename}
        )
        
        # 3. Add to ChromaDB vector database
        add_to_knowledge_base(record)
        
        # 4. Extract structured state (symptoms, vitals) and update SQLite state
        extracted_data = preprocess_and_update_state(pid, doc_data["cleaned_text"][:8000], file.filename)
        
        return {
            "status": "success",
            "message": f"Successfully ingested document {file.filename}",
            "extracted_data": extracted_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/prescription")
async def upload_prescription(patient_id: str | None = None, file: UploadFile = File(...)):
    """Ingests scanned/photographed prescriptions, runs EasyOCR + Qwen, updates SQLite."""
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        # 1. Run prescription understanding
        from backend.ingestion.prescription_parser import parse_prescription_image
        meds = parse_prescription_image(file_path, patient_id=pid)
        
        # 2. Build clinical knowledge text description for ChromaDB
        meds_summary = f"Prescription uploaded: {file.filename}.\nMedications extracted:\n"
        if meds:
            for m in meds:
                meds_summary += f"- {m.get('medicine')} {m.get('dosage')} {m.get('frequency')}\n"
        else:
            meds_summary += "No medications could be extracted."
            
        from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
        record = create_unified_record(
            patient_id=pid,
            source_type="prescription",
            clinical_content=meds_summary,
            metadata={"source_file": file.filename}
        )
        add_to_knowledge_base(record)
        
        # 3. Update timeline/history
        log_interaction(pid, f"Uploaded prescription: {file.filename}", ["medication_update"], file.filename)
        
        return {
            "status": "success",
            "message": f"Prescription {file.filename} processed",
            "medications": meds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/lab-report")
async def upload_lab_report(patient_id: str | None = None, file: UploadFile = File(...)):
    """Ingests PDF or image lab reports, extracts values to SQLite, and adds interpretation to ChromaDB."""
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        # 1. Run lab report parser
        from backend.ingestion.lab_parser import parse_lab_report
        lab_data = parse_lab_report(file_path, patient_id=pid)
        
        # 2. Add interpretation text to ChromaDB
        if lab_data["interpretation"]:
            from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
            record = create_unified_record(
                patient_id=pid,
                source_type="lab_report",
                clinical_content=lab_data["interpretation"],
                metadata={"source_file": file.filename}
            )
            add_to_knowledge_base(record)
            
        # 3. Update timeline/history
        symptoms = [val["test"] for val in lab_data["values"]]
        log_interaction(pid, f"Uploaded lab report: {file.filename}", symptoms, file.filename)
        
        return {
            "status": "success",
            "message": f"Lab report {file.filename} processed",
            "values": lab_data["values"],
            "interpretation": lab_data["interpretation"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/image")
async def upload_medical_image(patient_id: str | None = None, image_type: str = "general", file: UploadFile = File(...)):
    """Ingests X-ray, CT, MRI, ECG, or blood report screenshot. Runs LLaVA observations and adds to databases."""
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        # 1. Run image parser (LLaVA observations)
        from backend.ingestion.image_parser import parse_medical_image
        image_data = parse_medical_image(file_path, image_type=image_type, patient_id=pid)
        
        # 2. Add description text to ChromaDB
        from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
        record = create_unified_record(
            patient_id=pid,
            source_type=image_type,
            clinical_content=image_data["observation"],
            metadata={"source_file": file.filename, "image_path": file_path}
        )
        add_to_knowledge_base(record)
        
        # 3. Update timeline/history
        log_interaction(pid, f"Analyzed {image_type} image: {file.filename}", ["imaging_finding"], file.filename)
        
        return {
            "status": "success",
            "message": f"Medical image {file.filename} analyzed",
            "observation": image_data["observation"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/audio")
async def upload_audio_recording(patient_id: str | None = None, source_type: str = "audio_dictation", file: UploadFile = File(...)):
    """Ingests symptom recordings or doctor dictation, runs Whisper transcription, updates state."""
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        # 1. Run Whisper + Qwen parser
        from backend.ingestion.audio_parser import parse_audio_recording
        audio_data = parse_audio_recording(file_path, source_type=source_type, patient_id=pid)
        
        # 2. Add transcript to ChromaDB
        if audio_data["transcript"]:
            from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
            record = create_unified_record(
                patient_id=pid,
                source_type=source_type,
                clinical_content=f"Voice Recording Transcript ({source_type}):\n{audio_data['transcript']}",
                metadata={"source_file": file.filename}
            )
            add_to_knowledge_base(record)
            
        # 3. Update symptoms in timeline/history
        if audio_data["symptoms"]:
            from backend.clinical.patient_state import update_patient_state
            from backend.clinical.schemas import ExtractedClinicalData, ExtractedVitals
            extracted = ExtractedClinicalData(symptoms=audio_data["symptoms"], vitals=ExtractedVitals(), medications=[])
            update_patient_state(pid, extracted)
            
        log_interaction(pid, f"Voice dictation processed: {audio_data['transcript'][:100]}...", audio_data["symptoms"], file.filename)
        
        return {
            "status": "success",
            "message": f"Audio file {file.filename} transcribed",
            "transcript": audio_data["transcript"],
            "symptoms": audio_data["symptoms"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/video")
async def upload_video_recording(patient_id: str | None = None, file: UploadFile = File(...)):
    """Ingests video recordings, extracts frames, describes via LLaVA, generates Qwen summary, stores results."""
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        # 1. Run video understanding parser
        from backend.ingestion.video_parser import parse_video_observations
        video_data = parse_video_observations(file_path, patient_id=pid)
        
        # 2. Add summary text to ChromaDB
        from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
        record = create_unified_record(
            patient_id=pid,
            source_type="video_observations",
            clinical_content=f"Video Summary: {video_data['summary']}\n\nFrame observations:\n{video_data['observations']}",
            metadata={"source_file": file.filename, "video_path": file_path}
        )
        add_to_knowledge_base(record)
        
        # 3. Update timeline/history
        log_interaction(pid, f"Analyzed gait/movement video: {file.filename}", ["movement_finding"], file.filename)
        
        return {
            "status": "success",
            "message": f"Video file {file.filename} analyzed",
            "summary": video_data["summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(request: ChatRequest):
    """Main reasoning endpoint. Combines timeline, vitals, medications, labs, and Chroma contexts."""
    try:
        pid = resolve_patient_id(request.patient_id)
        chat_result = chat_pipeline(request.query, patient_id=pid)
        sos_result = check_sos(request.query)

        return {
            "response": chat_result["response"],
            "retrieved_context": chat_result["retrieved_context"],
            "sos_detected": chat_result["is_emergency"] or sos_result["is_sos"],
            "sos_details": sos_result if (chat_result["is_emergency"] or sos_result["is_sos"]) else None,
            "risk_score": chat_result["risk_score"],
            "severity": chat_result["severity"],
            "alerts": chat_result["alerts"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/summary")
def get_patient_summary(patient_id: str | None = None):
    """Aggregated patient dashboard for initial page load."""
    pid = resolve_patient_id(patient_id)
    state = get_patient_state(pid)
    risks = DatabaseManager.get_risk_history(pid, limit=1)
    latest_risk = risks[-1] if risks else None
    history = DatabaseManager.get_patient_history(pid, limit=100)
    alert_records = DatabaseManager.get_alerts(pid, limit=5)

    priority_alerts = []
    for record in alert_records:
        for alert in record.alerts:
            priority_alerts.append({
                "type": "critical",
                "title": record.severity,
                "detail": alert,
            })
    if latest_risk:
        for reason in latest_risk.reasons[:5]:
            alert_type = "critical" if latest_risk.severity in ("HIGH", "CRITICAL") else "positive"
            priority_alerts.append({"type": alert_type, "title": "Risk Signal", "detail": reason})

    vitals = state.current_vitals
    last_updated = None
    if history:
        last_updated = history[-1].timestamp
    elif latest_risk:
        last_updated = latest_risk.timestamp

    return {
        "patient_id": pid,
        "severity": latest_risk.severity if latest_risk else "LOW",
        "risk_score": latest_risk.risk_score if latest_risk else 0,
        "vitals": vitals.dict() if vitals else None,
        "medications_count": len(DatabaseManager.get_medications(pid)),
        "labs_count": len(DatabaseManager.get_lab_results(pid)),
        "timeline_count": len(history),
        "priority_alerts": priority_alerts[:8],
        "last_updated": last_updated,
    }

@app.get("/patient/alerts")
def get_patient_alerts(patient_id: str | None = None, limit: int = 10):
    """Fetches persisted clinical alerts from SQLite."""
    pid = resolve_patient_id(patient_id)
    records = DatabaseManager.get_alerts(pid, limit=limit)
    return {"alerts": [r.dict() for r in records]}

@app.get("/patient/timeline")
def get_patient_timeline(patient_id: str | None = None):
    """Fetches chronological patient event logs and history from SQLite."""
    pid = resolve_patient_id(patient_id)
    history = DatabaseManager.get_patient_history(pid)
    risks = DatabaseManager.get_risk_history(pid)
    
    # Format a unified chronological timeline
    events = []
    for h in history:
        events.append({
            "type": "interaction",
            "timestamp": h.timestamp,
            "description": h.interaction_text,
            "symptoms": h.extracted_symptoms,
            "risk_score": h.risk_score,
            "severity": h.severity
        })
    for r in risks:
        events.append({
            "type": "risk_assessment",
            "timestamp": r.timestamp,
            "description": f"Risk assessment: score {r.risk_score} ({r.severity})",
            "reasons": r.reasons,
            "risk_score": r.risk_score,
            "severity": r.severity
        })
        
    events.sort(key=lambda x: x["timestamp"])
    return {"timeline": events}

@app.get("/patient/medications")
def get_patient_medications(patient_id: str | None = None):
    """Fetches medication records from SQLite."""
    pid = resolve_patient_id(patient_id)
    meds = DatabaseManager.get_medications(pid)
    return {"medications": [m.dict() for m in meds]}

@app.get("/patient/labs")
def get_patient_labs(patient_id: str | None = None):
    """Fetches lab report measurements from SQLite."""
    pid = resolve_patient_id(patient_id)
    labs = DatabaseManager.get_lab_results(pid)
    return {"labs": [l.dict() for l in labs]}

@app.get("/patient/vitals")
def get_patient_vitals_history(patient_id: str | None = None):
    """Fetches patient vitals records from SQLite."""
    pid = resolve_patient_id(patient_id)
    vitals = DatabaseManager.get_vitals_history(pid, limit=30)
    return {"vitals": [v.dict() for v in vitals]}

@app.get("/patient/images")
def get_patient_images(patient_id: str | None = None):
    """Fetches medical image descriptions from SQLite."""
    pid = resolve_patient_id(patient_id)
    images = DatabaseManager.get_images(pid)
    return {"images": [img.dict() for img in images]}

@app.get("/patient/videos")
def get_patient_videos(patient_id: str | None = None):
    """Fetches video observations from SQLite."""
    pid = resolve_patient_id(patient_id)
    videos = DatabaseManager.get_videos(pid)
    return {"videos": [vid.dict() for vid in videos]}

def preprocess_and_update_state(patient_id: str, text: str, source_file: str) -> dict:
    """Utility to run clinical extraction and update patient state with vitals and alerts."""
    from backend.clinical.patient_state import update_patient_state
    from backend.clinical.scorer import score_patient
    from backend.clinical.alert_engine import AlertEngine
    
    extracted_data = extract_clinical_data(text)
    state = update_patient_state(patient_id, extracted_data)
    
    # Scoring and alert logic
    trend_result = TrendAnalyzer.analyze(state.vitals_history)
    emergency_result = EmergencyDetector.detect(text, state.symptoms_history)
    score_result = score_patient(state, trend_result["score_modifier"], emergency_result["score_modifier"])
    
    all_alerts = list(set(score_result["reasons"] + trend_result["details"] + emergency_result["matched_symptoms"]))
    AlertEngine.process_alerts(patient_id, score_result["severity"], score_result["risk_score"], all_alerts)
    
    # Save risk
    DatabaseManager.insert_risk(RiskRecord(
        patient_id=patient_id,
        timestamp=datetime.utcnow().isoformat(),
        risk_score=score_result["risk_score"],
        reasons=score_result["reasons"],
        severity=score_result["severity"]
    ))
    
    return {
        "symptoms": extracted_data.symptoms,
        "vitals": extracted_data.vitals.dict(),
        "risk_score": score_result["risk_score"],
        "severity": score_result["severity"]
    }

def log_interaction(patient_id: str, interaction_text: str, symptoms: list, source_file: str):
    """Utility to log patient clinical history log in SQLite."""
    from backend.database.db import DatabaseManager
    from backend.clinical.patient_state import get_patient_state
    from backend.clinical.scorer import score_patient
    
    state = get_patient_state(patient_id)
    score_result = score_patient(state)
    
    history_record = PatientHistoryRecord(
        patient_id=patient_id,
        timestamp=datetime.utcnow().isoformat(),
        interaction_text=f"{interaction_text} (File: {source_file})",
        extracted_symptoms=symptoms,
        risk_score=score_result["risk_score"],
        severity=score_result["severity"]
    )
    DatabaseManager.insert_history(history_record)

