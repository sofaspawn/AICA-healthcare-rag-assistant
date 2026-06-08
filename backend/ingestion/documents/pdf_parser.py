import fitz  # PyMuPDF
import pdfplumber
import os

def extract_pdf_text(file_path: str) -> str:
    """
    Extracts text from a PDF file using pdfplumber (better layout/tables) 
    and PyMuPDF (backup/scanned).
    """
    text = ""
    if not os.path.exists(file_path):
        return ""
        
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"pdfplumber failed for {file_path}: {e}. Trying PyMuPDF...")
        text = ""

    if not text.strip():
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            print(f"PyMuPDF text extraction failed for {file_path}: {e}")

    if not text.strip():
        print(f"No text found in PDF, falling back to EasyOCR via PyMuPDF images...")
        try:
            from backend.ingestion.prescription_parser import get_ocr_reader
            import numpy as np
            import cv2
            reader = get_ocr_reader()
            doc = fitz.open(file_path)
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                if pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                elif pix.n == 1:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                results = reader.readtext(img)
                text += " ".join([res[1] for res in results]) + "\n"
            doc.close()
        except Exception as e:
            print(f"OCR fallback failed: {e}")

    return text.strip()
