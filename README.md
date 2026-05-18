# Healthcare AI RAG Assistant

A local, AI-powered healthcare assistant built using Retrieval-Augmented Generation (RAG). It ingests a medical dataset, uses local embeddings to create a vector store, and employs an LLM to provide grounded, medically cautious answers while detecting SOS symptoms.

## Features

- **Dataset Ingestion:** Downloads and processes medical QA pairs from HuggingFace (`GuyDor007/medisimplifier-dataset`).
- **Local Embeddings:** Uses `sentence-transformers/all-MiniLM-L6-v2` locally to avoid embedding API costs.
- **Vector Database:** Persists vectorized chunks locally using ChromaDB.
- **SOS Detection:** Rule-based engine to detect emergency symptoms (e.g., chest pain, seizures) and flag them for immediate escalation.
- **Grounded Chat Engine:** Integrates with OpenRouter (using `deepseek-chat-v3-0324`) to provide informative but cautious responses based solely on retrieved context.
- **FastAPI Backend:** Exposes robust REST endpoints for ingestion, semantic search, and chat.
- **Interactive CLI:** Includes a terminal chat loop for rapid testing and debugging.

## Architecture

1. **Ingestion & Preprocessing:** Data is loaded via the `datasets` library, normalized into a standard JSON schema, and stored.
2. **Chunking & Embedding:** Text is split using `RecursiveCharacterTextSplitter` and embedded via `sentence-transformers`.
3. **Vector Storage & Retrieval:** ChromaDB stores the vectors. User queries are matched against the local DB.
4. **Chat Generation:** The retrieved context is passed alongside the user query to the OpenRouter LLM. A rule-based SOS engine runs concurrently to flag emergencies.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/samridh-111/AICA-healthcare-rag-assistant.git
   cd AICA-healthcare-rag-assistant
   ```

2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenRouter API Key
   ```

## API Usage

Start the backend:
```bash
uvicorn backend.main:app --reload
```

### 1. Health Check
```bash
curl -X GET http://127.0.0.1:8000/
```

### 2. Ingest Dataset
Downloads, preprocesses, chunks, embeds, and stores the medical dataset.
```bash
curl -X POST http://127.0.0.1:8000/ingest
```

### 3. Chat Endpoint
Chat with the assistant.
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the common symptoms of asthma?"}'
```

### 4. Semantic Search Endpoint
Test the retrieval system directly.
```bash
curl -X POST "http://127.0.0.1:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "chest pain"}'
```

## CLI Testing Support

You can test the assistant interactively in your terminal:
```bash
python backend/test_chat.py
```

## Future Roadmap

- [ ] Transition to more robust LLMs (e.g., Llama 3 via local Ollama).
- [ ] Add user session memory for multi-turn conversations.
- [ ] Implement GraphRAG for better contextual relationship mappings.
- [ ] Cloud deployment via Docker and Kubernetes.
