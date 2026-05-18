import os
import json
from datasets import load_dataset

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def download_and_export():
    print("Downloading dataset: GuyDor007/medisimplifier-dataset...")
    dataset = load_dataset("GuyDor007/medisimplifier-dataset")
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    for split in dataset.keys():
        print(f"Inspecting schema for split: {split}")
        print(dataset[split].features)
        
        # Convert to list of dicts
        records = dataset[split].to_list()
        
        output_file = os.path.join(DATA_DIR, f"raw_{split}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=4, ensure_ascii=False)
            
        print(f"Exported {len(records)} records to {output_file}")

if __name__ == "__main__":
    download_and_export()
