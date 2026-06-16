import pytest
import asyncio
from backend.groq.provider import GroqProvider

@pytest.mark.asyncio
async def test_llm_client_initialization():
    provider = GroqProvider()
    assert provider is not None
    
    # Client should be None before first call
    assert provider.client is None
    
    # We mock or let it fail if no key, just testing lifecycle
    await provider.close()
    assert provider.client is None

@pytest.mark.asyncio
async def test_llm_client_streaming(monkeypatch):
    provider = GroqProvider()
    
    # Mock the client so we don't actually hit the API
    class MockDelta:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, content):
            self.delta = MockDelta(content)

    class MockChunk:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    class MockCompletions:
        async def create(self, **kwargs):
            async def stream():
                for word in ["Hello", " ", "World"]:
                    yield MockChunk(word)
            return stream()

    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()

    class MockClient:
        def __init__(self):
            self.chat = MockChat()
            
        async def close(self):
            pass

    provider.client = MockClient()
    
    # Test streaming
    chunks = []
    async for chunk in provider.generate_stream("Test prompt"):
        chunks.append(chunk)
        
    assert "".join(chunks) == "Hello World"
    await provider.close()
