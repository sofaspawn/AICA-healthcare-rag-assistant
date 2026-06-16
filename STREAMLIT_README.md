# Healthcare RAG Assistant - Streamlit Edition 

This is a Streamlit-based version of the Healthcare RAG Assistant, making it easier to run without needing a separate FastAPI backend and React frontend.

## Features

 **All the same powerful features:**
- **Streamlit UI:** Modern, responsive web interface built with Streamlit
- **Dataset Ingestion:** Download and process medical QA pairs from HuggingFace
- **File Uploads:** Upload PDF and TXT medical documents directly
- **Local Embeddings:** Uses `sentence-transformers/all-MiniLM-L6-v2` for privacy
- **Vector Database:** ChromaDB for local vector persistence
- **SOS Detection:** Rule-based emergency symptom detection with alerts
- **Explainability:** View retrieved context chunks for each response
- **Local LLM Support:** Uses Ollama for private inference

## Quick Start

### 1. Prerequisites
- Python 3.8+
- Ollama (for local LLM inference) - [Download here](https://ollama.ai)
- At least 8GB RAM recommended

### 2. Clone & Setup

```bash
git clone https://github.com/samridh-111/AICA-healthcare-rag-assistant.git
cd AICA-healthcare-rag-assistant
chmod +x setup.sh run_streamlit.sh
./setup.sh
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API Key (or use Ollama locally)
```

### 4. Ensure Ollama is Running

```bash
# In a separate terminal, start Ollama
ollama serve

# In another terminal, pull a model
ollama pull qwen2.5:7b
# or
ollama pull mistral
```

### 5. Run the App

```bash
./run_streamlit.sh
```

The app will open at **http://localhost:8501**

## Usage

### Chat Interface
1. Type your healthcare question in the chat input at the bottom
2. The assistant retrieves relevant medical context from the database
3. An LLM generates a response based on that context
4. View retrieved documents in the "View Retrieved Context" expander

### Data Management (Sidebar)

**Download & Ingest Dataset:**
- Click to download ~1000 medical QA pairs from HuggingFace
- Automatically preprocesses and adds to vector store
- Takes ~2-5 minutes on first run

**Upload Documents:**
- Upload your own PDF or TXT medical documents
- Automatically chunked and embedded into the RAG context
- Supports multiple file uploads

**Status:**
- Shows if vector store is ready for queries

## Architecture

```
streamlit_app.py (UI Layer)
         ↓
backend/rag/ (Core RAG Logic)
  ├── chat.py → LLM generation
  ├── retriever.py → Context retrieval
  ├── vector_store.py → ChromaDB persistence
  ├── embeddings.py → Sentence embeddings
  ├── .py →chunker Document chunking
backend/ingestion/ (Data Loading)
  ├── download_dataset.py → HuggingFace data
  └── preprocess.py → Data normalization
backend/rules/ (Safety)
  └── sos_rules.py → Emergency detection
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# Ollama configuration (for local inference)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5:7b

# Or use OpenRouter (for cloud LLM)
OPENROUTER_API_KEY=your_api_key_here
```

## Troubleshooting

### "Vector store empty" warning
- Click "Download & Ingest Dataset" in the sidebar
- Or upload your own documents

### "Error generating response"
- Ensure Ollama is running: `ollama serve`
- Check Ollama model is available: `ollama pull qwen2.5:7b`
- Verify API keys in `.env`

### Slow responses
- Reduce number of retrieved chunks in code (default: 4)
- Use smaller Ollama model: `ollama pull mistral`
- Ensure sufficient RAM available

### Streamlit app not responding
- Clear cache: `streamlit cache clear`
- Restart with: `./run_streamlit.sh`

## Deployment

### On Render.com

1. Push your code to GitHub
2. Create new Web Service on Render
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run streamlit_app.py --server.port=10000`
5. Add environment variables
6. Deploy!

### On Hugging Face Spaces

1. Create a new Space with Streamlit runtime
2. Push this repo to the Space
3. Configure secrets in Space settings
4. App deploys automatically!

### On Railway/Heroku/DigitalOcean

Similar process - just ensure:
- Install dependencies from requirements.txt
- Run: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
- Set `STREAMLIT_SERVER_HEADLESS=true` environment variable

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|------------|
| RAM | 4GB | 8GB+ |
| Storage | 2GB | 5GB+ |
| Python | 3.8 | 3.10+ |
| Ollama Model | 4B params | 7B params |

## Performance Tips

1. **First load:** ~30-60s (downloads models and initializes)
2. **Subsequent queries:** ~5-15s (depends on Ollama model size)
3. **Document ingestion:** ~5-30s (depends on file size)

## Safety & Privacy

 **All processing is local by default**
- Documents never leave your machine
- Embeddings computed locally
- LLM inference via local Ollama
- SOS detection is rule-based and instant

## API Reference (if needed)

The original FastAPI backend is still available if you prefer:

```bash
uvicorn backend.main:app --reload
# API docs at http://localhost:8000/docs
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.

## Support

For issues or questions:
- GitHub Issues: https://github.com/samridh-111/AICA-healthcare-rag-assistant/issues
- Documentation: See README.md

---

**Remember:** This is an AI assistant for information retrieval. Always consult qualified healthcare professionals for medical advice.
