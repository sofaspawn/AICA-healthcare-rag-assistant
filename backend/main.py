import os
import json
import uuid
import io
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from pathlib import Path

# Always load .env from the project root, regardless of where uvicorn is invoked
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

from backend.ingestion.download_dataset import download_and_export
from backend.ingestion.preprocess import preprocess_data
from backend.rag.vector_store import get_vector_store
from backend.rag.retriever import retrieve_context
from backend.rag.chat import chat_pipeline
from backend.rules.sos_rules import check_sos

app = FastAPI(title="Healthcare RAG Assistant API")

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log API key presence on startup
@app.on_event("startup")
def log_api_key():
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        print(" OPENROUTER_API_KEY loaded")
    else:
        print(" OPENROUTER_API_KEY missing")

class ChatRequest(BaseModel):
    query: str
    
class SearchRequest(BaseModel):
    query: str

@app.get("/health")
def health_check():
    api_key_set = bool(os.environ.get("OPENROUTER_API_KEY"))
    return {
        "status": "ok",
        "message": "Healthcare RAG Assistant is running.",
        "api_key_configured": api_key_set
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
    return {"message": "Frontend build not found. Run npm run build in frontend directory."}

@app.post("/ingest")
def ingest_dataset():
    """
    Triggers dataset download, preprocessing, and vector store ingestion.
    """
    try:
        # 1. Download raw data
        download_and_export()
        # 2. Preprocess and normalize
        processed_file_path = preprocess_data()
        
        # 3. Load processed data
        with open(processed_file_path, "r", encoding="utf-8") as f:
            documents = json.load(f)
            
        # 4. Add to vector store
        store = get_vector_store()
        store.add_documents(documents)
        
        return {"status": "success", "message": f"Successfully ingested {len(documents)} records."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts PDF or TXT files, extracts text, chunks it, and adds to vector store.
    """
    try:
        content = await file.read()
        text = ""
        
        if file.filename.endswith(".pdf"):
            pdf = PdfReader(io.BytesIO(content))
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        elif file.filename.endswith(".txt"):
            text = content.decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported.")
            
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file.")
            
        # Format as document
        doc_id = str(uuid.uuid4())
        document = {
            "id": doc_id,
            "input": f"Content from uploaded file: {file.filename}",
            "output": text.strip(),
            "category": "user_upload",
            "metadata": {
                "source": file.filename,
                "original_id": doc_id
            }
        }
        
        # Add to vector store
        store = get_vector_store()
        store.add_documents([document])
        
        return {"status": "success", "message": f"Successfully processed and embedded {file.filename}."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(request: ChatRequest):
    """
    Main chat endpoint. Checks for SOS symptoms and generates an LLM response.
    """
    query = request.query
    
    # 1. Check SOS
    sos_result = check_sos(query)
    
    # 2. Run RAG Pipeline
    chat_result = chat_pipeline(query)
    
    return {
        "response": chat_result["response"],
        "retrieved_context": chat_result["retrieved_context"],
        "sos_detected": sos_result["is_sos"],
        "sos_details": sos_result if sos_result["is_sos"] else None
    }

@app.post("/search")
def search(request: SearchRequest):
    """
    Semantic search endpoint for testing retrieval.
    """
    retrieval_data = retrieve_context(request.query)
    
    return {
        "results": [
            {
                "content": res.page_content,
                "metadata": res.metadata
            } for res in retrieval_data["raw_results"]
        ]
    }
