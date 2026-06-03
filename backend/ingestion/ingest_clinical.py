import os
import uuid
import pdfplumber
from typing import List, Dict

# Determine project root (two levels up from this file)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_CLINICAL_DIR = os.path.join(PROJECT_ROOT, "Data_clinical")

def ingest_clinical() -> List[Dict]:
    """Ingest clinical PDF documents from the Data_clinical directory.

    Returns a list of document dictionaries compatible with the existing vector store.
    Each document has fields: id, input, output, category, metadata (including priority).
    """
    documents: List[Dict] = []
    if not os.path.isdir(DATA_CLINICAL_DIR):
        print(f"Data_clinical directory not found at {DATA_CLINICAL_DIR}")
        return documents
    for filename in os.listdir(DATA_CLINICAL_DIR):
        if not filename.lower().endswith('.pdf'):
            continue
        file_path = os.path.join(DATA_CLINICAL_DIR, filename)
        try:
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as e:
            print(f"Failed to extract {filename}: {e}")
            continue
        doc_id = str(uuid.uuid4())
        document = {
            "id": doc_id,
            "input": f"Clinical document: {filename}",
            "output": text.strip(),
            "category": "clinical",
            "metadata": {
                "source": filename,
                "priority": "primary"
            }
        }
        documents.append(document)
    print(f"Ingested {len(documents)} clinical PDF documents.")
    return documents
