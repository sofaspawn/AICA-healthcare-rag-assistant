import uuid
from datetime import datetime
from backend.rag.vector_store import get_vector_store
from backend.rag.chunker import chunk_document

def create_unified_record(patient_id: str, source_type: str, clinical_content: str, metadata: dict = None, timestamp: str = None) -> dict:
    """
    Creates a dictionary conforming to the unified patient knowledge schema.
    Unified Schema:
    {
      "patient_id": "...",
      "source_type": "...",
      "timestamp": "...",
      "clinical_content": "...",
      "metadata": {...}
    }
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    if metadata is None:
        metadata = {}
        
    # Ensure patient_id, source_type, and timestamp are inside metadata for Chroma filtering
    meta_copy = metadata.copy()
    meta_copy["patient_id"] = patient_id
    meta_copy["source_type"] = source_type
    meta_copy["timestamp"] = timestamp

    return {
        "patient_id": patient_id,
        "source_type": source_type,
        "timestamp": timestamp,
        "clinical_content": clinical_content.strip(),
        "metadata": meta_copy
    }

def add_to_knowledge_base(record: dict):
    """
    Chunks the unified record's clinical_content, generates embeddings, and stores in ChromaDB.
    """
    content = record["clinical_content"]
    metadata = record["metadata"]
    patient_id = record["patient_id"]
    source_type = record["source_type"]
    
    if not content.strip():
        print(f"Warning: Empty clinical content for source {source_type}. Skipping database insert.")
        return

    # Chunk the text
    chunks = chunk_document(content)
    
    texts = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        texts.append(chunk)
        
        # Build metadata for this chunk
        meta = metadata.copy()
        meta["chunk_index"] = i
        metadatas.append(meta)
        
        # Generate unique ID for this chunk
        ids.append(f"{patient_id}_{source_type}_{uuid.uuid4().hex[:8]}_{i}")

    # Add directly to ChromaDB
    store = get_vector_store()
    store.add_raw_texts(texts=texts, metadatas=metadatas, ids=ids)
    print(f"Ingested {len(texts)} chunks of source type '{source_type}' into ChromaDB vector store.")
