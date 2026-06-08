import re
import json
import ollama

def ensure_model_pulled(model_name: str):
    """
    Checks if a model is present in Ollama, and pulls it if not.
    """
    try:
        models_list = ollama.list()
        pulled_models = []
        if hasattr(models_list, 'models'):
            pulled_models = [m.model for m in models_list.models]
        elif isinstance(models_list, dict) and 'models' in models_list:
            pulled_models = [m['model'] for m in models_list['models']]
            
        # Check standard name or with latest tag
        if model_name not in pulled_models and f"{model_name}:latest" not in pulled_models:
            print(f"Model {model_name} not found locally. Pulling from Ollama registry...")
            ollama.pull(model_name)
            print(f"Model {model_name} successfully pulled!")
    except Exception as e:
        print(f"Failed to check/pull model {model_name}: {e}. Make sure Ollama is running.")

def query_ollama_text(prompt: str, system_prompt: str = "", model: str = "qwen2.5:7b") -> str:
    """
    Sends a query to local Ollama text model and returns raw text response.
    """
    try:
        ensure_model_pulled(model)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = ollama.chat(
            model=model,
            messages=messages,
            options={"temperature": 0.1}
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"Ollama text query failed: {e}")
        return f"Error: Local reasoning model query failed: {str(e)}"

def query_ollama_json(prompt: str, system_prompt: str = "", model: str = "qwen2.5:7b") -> dict | list:
    """
    Sends a query to local Ollama and expects a JSON output.
    """
    try:
        ensure_model_pulled(model)
        full_system = system_prompt + "\nOutput MUST be valid raw JSON. Do not include markdown code block formatting (like ```json)."
        
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.0} # deterministic
        )
        content = response['message']['content'].strip()
        
        # Clean markdown code blocks if present
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\n', '', content)
            content = re.sub(r'\n```$', '', content)
            content = content.strip()
            
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback regex search for JSON if there's surrounding text
            match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            raise
    except Exception as e:
        print(f"Ollama JSON query failed: {e}. Raw content: {content if 'content' in locals() else 'None'}")
        return []

def query_llava_image(image_path: str, prompt: str) -> str:
    """
    Calls local Ollama LLaVA model to analyze an image.
    """
    try:
        ensure_model_pulled('llava')
        response = ollama.chat(
            model='llava',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_path]
            }],
            options={"temperature": 0.1}
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"LLaVA query failed: {e}")
        return f"[Failed to analyze image with LLaVA: {e}]"
