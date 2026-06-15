import os
import logging
import requests
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

HF_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_MODEL_ID}"
EMBEDDING_DIM = 384  # Dimension of all-MiniLM-L6-v2 embeddings


def _get_hf_headers() -> dict:
    token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_hf_api(texts: List[str]) -> List[List[float]]:
    """Call Hugging Face Inference API for text embeddings."""
    headers = _get_hf_headers()
    payload = {
        "inputs": texts,
        "options": {"wait_for_model": True}
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


class EmbeddingModel:
    """Lightweight embedding model backed by Hugging Face Inference API.
    
    No local model weights are loaded — eliminates the ~400MB+ RAM cost
    of sentence-transformers + PyTorch at startup.
    """

    def encode(self, texts: List[str]) -> List[List[float]]:
        """Return a list of embedding vectors (as plain Python lists) for the given texts."""
        if not texts:
            return []

        try:
            embeddings = _call_hf_api(texts)
            # HF can return nested structure for certain models; normalise to
            # a flat list of vectors.
            if embeddings and isinstance(embeddings[0], list) and isinstance(embeddings[0][0], list):
                # Some models return [batch, seq, dim] — take CLS (index 0)
                embeddings = [e[0] for e in embeddings]
            logger.info(f"Got embeddings for {len(texts)} text(s) from HF API")
            return embeddings
        except Exception as e:
            logger.error(f"HF embedding API failed: {e}. Returning zero vectors.")
            # Return zero vectors so the app doesn't crash; similarity search
            # will simply return no matches for this batch.
            return [[0.0] * EMBEDDING_DIM for _ in texts]

    def encode_single(self, text: str) -> List[float]:
        """Convenience helper for a single text."""
        results = self.encode([text])
        return results[0] if results else [0.0] * EMBEDDING_DIM


# Module-level singleton — constructed lazily (no startup cost)
_instance: EmbeddingModel | None = None


def get_embedding_model() -> EmbeddingModel:
    global _instance
    if _instance is None:
        logger.info("Initialising cloud-backed EmbeddingModel (HF Inference API)")
        _instance = EmbeddingModel()
    return _instance
