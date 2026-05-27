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
            # ChromaDB has a max batch size (~5461). Process in batches.
            BATCH_SIZE = 5000
            total = len(texts)
            for start in range(0, total, BATCH_SIZE):
                end = min(start + BATCH_SIZE, total)
                self.db.add_texts(
                    texts=texts[start:end],
                    metadatas=metadatas[start:end],
                    ids=ids[start:end],
                )
                print(f"Added batch {start // BATCH_SIZE + 1}: chunks {start+1}-{end} of {total}")
            print(f"Finished adding {total} chunks to the vector store.")
            
    def add_raw_texts(self, texts: list[str], metadatas: list[dict], ids: list[str]):
        """
        Adds pre-chunked texts directly to the vector store.
        Used for uploaded documents (PDF/TXT) that don't need Q/A reformatting.
        """
        if texts:
            BATCH_SIZE = 5000
            total = len(texts)
            for start in range(0, total, BATCH_SIZE):
                end = min(start + BATCH_SIZE, total)
                self.db.add_texts(
                    texts=texts[start:end],
                    metadatas=metadatas[start:end],
                    ids=ids[start:end],
                )
                print(f"Added batch {start // BATCH_SIZE + 1}: chunks {start+1}-{end} of {total}")
            print(f"Finished adding {total} raw text chunks to the vector store.")

    def similarity_search(self, query: str, k: int = 4):
        return self.db.similarity_search(query, k=k)

    def similarity_search_with_filter(self, query: str, where_filter: dict, k: int = 4):
        """
        Similarity search filtered by metadata.
        Example: where_filter={"source": "myfile.pdf"}
        For multiple sources: where_filter={"source": {"$in": ["file1.pdf", "file2.pdf"]}}
        """
        return self.db.similarity_search(query, k=k, filter=where_filter)

vector_store_instance = None

def get_vector_store():
    global vector_store_instance
    if vector_store_instance is None:
        vector_store_instance = VectorStore()
    return vector_store_instance
