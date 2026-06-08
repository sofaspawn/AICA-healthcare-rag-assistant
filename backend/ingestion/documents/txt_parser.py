import os

def extract_txt_text(file_path: str) -> str:
    """
    Extracts text from a plain TXT file.
    """
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception as e:
        print(f"TXT read failed for {file_path}: {e}")
        return ""
