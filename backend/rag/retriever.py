from backend.rag.vector_store import get_vector_store

def retrieve_context(query: str, top_k: int = 4, uploaded_sources: list[str] = None):
    """
    Retrieves the most semantically relevant chunks for a given query.
    If uploaded_sources is provided, prioritizes those documents.
    """
    store = get_vector_store()
    results = []

    if uploaded_sources:
        # Prioritize uploaded documents: get most results from them
        uploaded_k = min(top_k, max(top_k - 1, 1))  # e.g. 3 out of 4
        base_k = top_k - uploaded_k  # e.g. 1 out of 4

        if len(uploaded_sources) == 1:
            where_filter = {"source": uploaded_sources[0]}
        else:
            where_filter = {"source": {"$in": uploaded_sources}}

        try:
            uploaded_results = store.similarity_search_with_filter(
                query, where_filter=where_filter, k=uploaded_k
            )
            results.extend(uploaded_results)
        except Exception as e:
            print(f"Filtered search failed: {e}")

        # Supplement with base dataset results
        if base_k > 0:
            try:
                base_results = store.similarity_search(query, k=base_k)
                results.extend(base_results)
            except Exception:
                pass
    else:
        # No uploaded docs — search everything
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
