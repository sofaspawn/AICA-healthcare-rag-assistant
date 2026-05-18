import os
import sys
from dotenv import load_dotenv

# Ensure we can import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag.chat import chat_pipeline
from backend.rules.sos_rules import check_sos

# Load env variables (for OPENROUTER_API_KEY)
load_dotenv()

def print_separator():
    print("=" * 60)

def main():
    print_separator()
    print("Healthcare RAG Assistant - CLI Mode")
    print("Type 'exit' or 'quit' to stop.")
    print_separator()
    
    while True:
        query = input("\nUser: ")
        if query.lower() in ["exit", "quit"]:
            break
            
        if not query.strip():
            continue
            
        # Check SOS
        sos_result = check_sos(query)
        if sos_result["is_sos"]:
            print("\n🚨 [EMERGENCY ALERT] 🚨")
            print(f"Detected critical symptoms: {', '.join(sos_result['matched_rules'])}")
            print("Please seek immediate medical attention or call emergency services!")
            print_separator()
            
        print("\nRetrieving context and generating response...")
        try:
            chat_result = chat_pipeline(query)
            
            print("\nSystem Response:")
            print("-" * 40)
            print(chat_result["response"])
            print("-" * 40)
            
            print("\n[Debug] Retrieved Context Chunks:")
            for meta in chat_result["retrieved_context"]:
                print(f"- Source ID: {meta.get('source_id')}, Chunk: {meta.get('chunk_index')}")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
