import os
import json
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def preprocess_data():
    raw_files = [f for f in os.listdir(DATA_DIR) if f.startswith("raw_") and f.endswith(".json")]
    
    all_normalized_records = []
    
    for filename in raw_files:
        input_path = os.path.join(DATA_DIR, filename)
        with open(input_path, "r", encoding="utf-8") as f:
            records = json.load(f)
            
        for record in records:
            # Assuming 'input' and 'output' or 'instruction' are common fields
            # Let's cleanly extract what we can. 
            # Medisimplifier usually has 'input' and 'output' or similar.
            
            input_text = str(record.get("input", "") or record.get("instruction", "")).strip()
            output_text = str(record.get("output", "") or record.get("response", "")).strip()
            
            if not input_text or not output_text:
                continue # Skip malformed or empty
                
            normalized_record = {
                "id": str(uuid.uuid4()),
                "input": input_text,
                "output": output_text,
                "category": record.get("category", "medical"),
                "metadata": {
                    "source": "GuyDor007/medisimplifier-dataset",
                    "original_id": str(record.get("id", ""))
                }
            }
            
            all_normalized_records.append(normalized_record)
            
    output_file = os.path.join(DATA_DIR, "processed_dataset.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_normalized_records, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully normalized and exported {len(all_normalized_records)} records to {output_file}")
    return output_file

if __name__ == "__main__":
    preprocess_data()
