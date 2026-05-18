import os
from langchain_community.vectorstores import Chroma
from backend.rag.embeddings import get_embedding_model
from backend.rag.chunker import chunk_document

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
COLLECTION_NAME = "healthcare_docs"

class VectorStore:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.embeddings = get_embedding_model()
        self.db = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=DB_DIR
        )
        
    def add_documents(self, documents: list[dict]):
        """
        Expects a list of dictionaries, each having 'input', 'output', 'id', 'metadata'.
        """
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
                
        if texts:
            self.db.add_texts(texts=texts, metadatas=metadatas, ids=ids)
            print(f"Added {len(texts)} chunks to the vector store.")
            
    def similarity_search(self, query: str, k: int = 4):
        return self.db.similarity_search(query, k=k)

vector_store_instance = None

def get_vector_store():
    global vector_store_instance
    if vector_store_instance is None:
        vector_store_instance = VectorStore()
    return vector_store_instance
