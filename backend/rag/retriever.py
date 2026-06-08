from backend.rag.vector_store import get_vector_store

def retrieve_context(query: str, patient_id: str = "patient_001", top_k: int = 5):
    """
    Retrieves the most semantically relevant chunks for a given query,
    filtering by patient_id to search across all uploaded modalities simultaneously.
    """
    store = get_vector_store()
    
    # Isolate queries to the specific patient
    where_filter = {"patient_id": patient_id}
    
    try:
        # chroma uses metadata filters
        results = store.db.similarity_search(query, k=top_k, filter=where_filter)
    except Exception as e:
        print(f"Similarity search with patient filter failed: {e}. Searching without filter.")
        results = store.similarity_search(query, k=top_k)

    # Format chunks into a readable string for the LLM
    context_chunks = []
    metadata_list = []

    for i, doc in enumerate(results):
        meta = doc.metadata
        source_type = meta.get("source_type", "document").upper()
        source_file = meta.get("source_file", "unknown")
        timestamp = meta.get("timestamp", "N/A")
        
        # Clean timestamp display
        if timestamp != "N/A":
            try:
                timestamp = timestamp.split("T")[0] + " " + timestamp.split("T")[1][:5]
            except Exception:
                pass
                
        context_chunks.append(
            f"[Source {i+1}]: {source_type} (File: {source_file}) - Time: {timestamp}\n"
            f"Clinical Content: {doc.page_content}"
        )
        metadata_list.append(meta)

    context_string = "\n\n".join(context_chunks)

    return {
        "context_string": context_string,
        "metadata": metadata_list,
        "raw_results": results
    }

