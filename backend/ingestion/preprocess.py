import os
import json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def preprocess_data(include_secondary: bool = True) -> str:
    """Load pre‑processed Medisimplifier dataset (secondary) and optionally return its path.
    The original download step is omitted because the dataset is already present in
    `data/processed_dataset.json`.
    """
    processed_path = os.path.join(DATA_DIR, "processed_dataset.json")
    if not os.path.isfile(processed_path):
        raise FileNotFoundError(f"Processed dataset not found at {processed_path}")
    print(f"Loaded secondary dataset from {processed_path}")
    return processed_path

if __name__ == "__main__":
    preprocess_data()
