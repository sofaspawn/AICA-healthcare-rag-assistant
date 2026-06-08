import os
import re
from backend.ingestion.documents.pdf_parser import extract_pdf_text
from backend.ingestion.documents.docx_parser import extract_docx_text
from backend.ingestion.documents.txt_parser import extract_txt_text
from backend.rag.chunker import chunk_document

def clean_text(text: str) -> str:
    """
    Cleans extracted text: replaces multiple whitespaces with single spaces,
    normalizes newlines, and strips padding.
    """
    # Normalize newlines
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    
    # Process line-by-line
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            # Replace multiple spaces within a line with a single space
            cleaned_line = re.sub(r'\s+', ' ', stripped)
            cleaned_lines.append(cleaned_line)
            
    return "\n".join(cleaned_lines)

def ingest_document(file_path: str) -> dict:
    """
    Main entry point for document ingestion.
    Extracts text based on file type, cleans it, chunks it, and returns details.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        raw_text = extract_pdf_text(file_path)
    elif ext == ".docx":
        raw_text = extract_docx_text(file_path)
    elif ext in [".txt", ".log", ".json"]:
        raw_text = extract_txt_text(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    if not raw_text.strip():
        raise ValueError(f"Could not extract any text from {filename}")

    cleaned = clean_text(raw_text)
    chunks = chunk_document(cleaned)

    return {
        "filename": filename,
        "raw_text": raw_text,
        "cleaned_text": cleaned,
        "chunks": chunks
    }
