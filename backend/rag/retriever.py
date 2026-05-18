from backend.rag.vector_store import get_vector_store

def retrieve_context(query: str, top_k: int = 4):
    """
    Retrieves the most semantically relevant chunks for a given query.
    """
    store = get_vector_store()
    results = store.similarity_search(query, k=top_k)
    
    # Format chunks into a readable string for the LLM
    context_chunks = []
    metadata_list = []
    
    for i, doc in enumerate(results):
        context_chunks.append(f"[Document {i+1}]:\n{doc.page_content}")
        metadata_list.append(doc.metadata)
        
    context_string = "\n\n".join(context_chunks)
    
    return {
        "context_string": context_string,
        "metadata": metadata_list,
        "raw_results": results
    }
