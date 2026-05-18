from langchain_community.embeddings import HuggingFaceEmbeddings

class EmbeddingModel:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            print("Loading local embedding model: sentence-transformers/all-MiniLM-L6-v2")
            cls._instance = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        return cls._instance

def get_embedding_model():
    return EmbeddingModel.get_instance()
