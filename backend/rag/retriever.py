from backend.rag.vector_store import get_vector_store

def retrieve_context(query: str, patient_id: str = None, top_k: int = 4):
    """
    Retrieves the most semantically relevant chunks for a given query.
    Returns structured results with a context string and metadata list.
    """
    store = get_vector_store()
    results = []
    try:
        if patient_id:
            results = store.similarity_search(query, patient_id=patient_id, k=top_k)
        else:
            # Some vector stores expect only query and k
            results = store.similarity_search(query, k=top_k)
    except Exception:
        results = []

    context_chunks = []
    metadata_list = []

    # Results may be a list of LangChain Documents, or dicts from supabase
    for i, item in enumerate(results):
        if isinstance(item, dict):
            content = item.get("content") or item.get("page_content") or str(item)
            metadata = item.get("metadata", {})
        else:
            # Try to access LangChain Document attributes
            content = getattr(item, "page_content", None) or getattr(item, "content", str(item))
            metadata = getattr(item, "metadata", {}) if hasattr(item, "metadata") else {}

        context_chunks.append(f"[Document {i+1}]:\n{content}")
        metadata_list.append(metadata)

    context_string = "\n\n".join(context_chunks)

    return {
        "context_string": context_string,
        "metadata": metadata_list,
        "raw_results": results
    }

