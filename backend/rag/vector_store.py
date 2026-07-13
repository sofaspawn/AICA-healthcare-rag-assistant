import logging
import os
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.rag.embeddings import get_embedding_model
from backend.rag.chunker import chunk_document
from backend.database.db import supabase

VECTOR_TABLE_NAME = os.getenv("VECTOR_TABLE_NAME", "clinical_knowledge")

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.embeddings = get_embedding_model()
        
    def add_documents(self, documents: list[dict]):
        """
        Expects a list of dictionaries, each having 'input', 'output', 'id', 'metadata'.
        """
        if not supabase:
            logger.warning("Supabase not configured. Skipping vector add.")
            return

        texts = []
        metadatas = []
        ids = []
        
        for doc in documents:
            # Combine input and output for meaningful retrieval context
            full_text = f"Q: {doc['input']}\nA: {doc['output']}"
            chunks = chunk_document(full_text)
            
            for i, chunk in enumerate(chunks):
                texts.append(chunk)
                meta = doc.get("metadata", {}).copy()
                meta["source_id"] = doc["id"]
                meta["chunk_index"] = i
                metadatas.append(meta)
                ids.append(f"{doc['id']}_{i}")
                
        self._batch_insert(texts, metadatas, ids)

    def add_raw_texts(self, texts: list[str], metadatas: list[dict], ids: list[str]):
        """
        Adds pre-chunked texts directly to the vector store.
        """
        if not supabase:
            logger.warning("Supabase not configured. Skipping vector add.")
            return
        self._batch_insert(texts, metadatas, ids)

    def _batch_insert(self, texts: list[str], metadatas: list[dict], ids: list[str]):
        if not texts:
            return
        
        # Generate embeddings
        embs = self.embeddings.encode(texts)  # returns List[List[float]]
        
        records = []
        for i in range(len(texts)):
            patient_id = metadatas[i].get("patient_id", "unknown")
            records.append({
                "patient_id": patient_id,
                "content": texts[i],
                "embedding": embs[i] if isinstance(embs[i], list) else list(embs[i]),
                "metadata": metadatas[i]
            })
            
        BATCH_SIZE = 100
        for start in range(0, len(records), BATCH_SIZE):
            end = min(start + BATCH_SIZE, len(records))
            batch = records[start:end]
            self._insert_with_retry(batch, start // BATCH_SIZE + 1)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _insert_with_retry(self, batch, batch_num):
        try:
            supabase.table(VECTOR_TABLE_NAME).insert(batch).execute()
            logger.info(f"Inserted vector batch {batch_num} into {VECTOR_TABLE_NAME}")
        except Exception as e:
            logger.error(f"Error inserting vector batch {batch_num} into {VECTOR_TABLE_NAME}: {e}")
            raise e

    def similarity_search(self, query: str, patient_id: str, k: int = 4):
        if not supabase:
            return []
            
        query_emb = self.embeddings.encode_single(query)
        
        try:
            response = supabase.rpc("match_clinical_knowledge", {
                "query_embedding": query_emb,
                "match_threshold": 0.5,
                "match_count": k,
                "p_patient_id": patient_id
            }).execute()
            return response.data
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def hybrid_search(self, query: str, patient_id: str, k: int = 20):
        if not supabase:
            return []
            
        query_emb = self.embeddings.encode_single(query)
        
        try:
            response = supabase.rpc("match_clinical_knowledge_hybrid", {
                "query_embedding": query_emb,
                "query_text": query,
                "match_threshold": 0.5,
                "match_count": k,
                "p_patient_id": patient_id,
                "full_text_weight": 1.0,
                "semantic_weight": 1.0,
                "rrf_k": 50
            }).execute()
            return response.data
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

vector_store_instance = None

def get_vector_store():
    global vector_store_instance
    if vector_store_instance is None:
        vector_store_instance = VectorStore()
    return vector_store_instance
