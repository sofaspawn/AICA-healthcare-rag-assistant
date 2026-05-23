import os
from openai import OpenAI
from backend.rag.retriever import retrieve_context

# Groq exposes an OpenAI-compatible API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required but not set. "
                     "Set it in your .env file or export it in the shell.")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def generate_chat_response(query: str, context_string: str) -> str:
    """
    Generates a response using Groq API via the OpenAI-compatible client.
    """
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
    )
    model_name = GROQ_MODEL
    
    system_prompt = """You are a highly cautious and helpful AI medical assistant.
Your goal is to answer the user's queries based SOLELY on the provided medical context.
You MUST follow these rules:
1. NEVER hallucinate medical diagnoses.
2. If the context does not contain the answer, explicitly state that you cannot answer based on the available information.
3. Always encourage the user to consult a qualified physician or healthcare professional for medical advice.
4. Explain your reasoning simply and clearly.
5. Be empathetic but maintain a professional, objective tone.

CONTEXT:
{context}
"""
    
    messages = [
        {"role": "system", "content": system_prompt.format(context=context_string)},
        {"role": "user", "content": query}
    ]
    
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.1, # Low temperature for more grounded/factual responses
    )
    
    return response.choices[0].message.content

def chat_pipeline(query: str):
    """
    1. Retrieve context
    2. Generate LLM response
    3. Return both
    """
    retrieval_data = retrieve_context(query)
    context_str = retrieval_data["context_string"]
    
    try:
        response_text = generate_chat_response(query, context_str)
    except Exception as e:
        response_text = f"Error generating response: {str(e)}"
        
    return {
        "response": response_text,
        "retrieved_context": retrieval_data["metadata"]
    }
