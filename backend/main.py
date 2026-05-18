import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.ingestion.download_dataset import download_and_export
from backend.ingestion.preprocess import preprocess_data
from backend.rag.vector_store import get_vector_store
from backend.rag.retriever import retrieve_context
from backend.rag.chat import chat_pipeline
from backend.rules.sos_rules import check_sos

app = FastAPI(title="Healthcare RAG Assistant API")

class ChatRequest(BaseModel):
    query: str
    
class SearchRequest(BaseModel):
    query: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Healthcare RAG Assistant is running."}

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
