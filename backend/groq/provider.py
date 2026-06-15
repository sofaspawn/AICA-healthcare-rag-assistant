import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> Any:
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, system_prompt: str = None, **kwargs) -> AsyncGenerator[str, None]:
        pass

class GroqProvider(LLMProvider):
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            logger.warning("GROQ_API_KEY is missing. GroqProvider will fail on calls.")
        self.client = AsyncGroq(api_key=api_key)
        self.default_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> Any:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        base64_image = kwargs.get("base64_image")
        if base64_image:
            # Use Llama 3.2 Vision model
            model = kwargs.get("model", "llama-3.2-11b-vision-preview")
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})
            model = kwargs.get("model", self.default_model)
        
        try:
            response = await self.client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024),
                response_format=kwargs.get("response_format", None)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_stream(self, prompt: str, system_prompt: str = None, **kwargs) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        model = kwargs.get("model", self.default_model)
        
        try:
            stream = await self.client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Groq streaming generation failed: {e}")
            raise e

# Singleton instance for easy importing
_provider_instance = None

def get_llm_provider() -> LLMProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = GroqProvider()
    return _provider_instance
