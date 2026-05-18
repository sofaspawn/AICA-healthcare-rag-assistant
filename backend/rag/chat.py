import os
from openai import OpenAI
from backend.rag.retriever import retrieve_context

def generate_chat_response(query: str, context_string: str) -> str:
    """
    Generates a response using the OpenRouter API based on the provided context.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set.")
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
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
        model="deepseek/deepseek-chat-v3-0324:free",
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
