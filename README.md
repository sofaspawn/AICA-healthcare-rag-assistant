# Healthcare AI RAG Assistant

A local and cloud-deployable AI-powered healthcare assistant built using Retrieval-Augmented Generation (RAG). It features a robust FastAPI backend and a clean, interactive Streamlit frontend UI.

## Features

- **Streamlit Frontend:** A modern, healthcare-themed UI for chatting and uploading files.
- **Dataset Ingestion:** Downloads and processes medical QA pairs from HuggingFace (`GuyDor007/medisimplifier-dataset`).
- **File Uploads:** Upload your own PDF and TXT medical documents directly through the UI to be chunked and embedded into the RAG context.
- **Local Embeddings:** Uses `sentence-transformers/all-MiniLM-L6-v2` locally to avoid embedding API costs.
- **Vector Database:** Persists vectorized chunks locally using ChromaDB.
- **SOS Detection:** Rule-based engine to detect emergency symptoms (e.g., chest pain, seizures) and flag them with prominent UI alerts.
- **Explainability:** Displays exactly which document chunks were retrieved to ground the LLM's response.
- **FastAPI Backend:** Exposes robust REST endpoints for ingestion, search, file uploads, and chat.

## Architecture

1. **Frontend (Streamlit):** Handles UI, user inputs, file uploads, and renders AI responses + SOS alerts.
2. **Backend (FastAPI):** Exposes endpoints (`/chat`, `/upload`, `/ingest`, `/search`).
3. **Ingestion & Chunking:** Data is loaded (from HF or file uploads), normalized, and split.
4. **Vector Storage & Retrieval:** ChromaDB stores vectors locally.
5. **Chat Generation:** The retrieved context is passed alongside the user query to the Groq LLM. A rule-based SOS engine runs concurrently to flag emergencies.

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/samridh-111/AICA-healthcare-rag-assistant.git
   cd AICA-healthcare-rag-assistant
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS / Linux
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # For Streamlit-specific dependencies:
   pip install -r requirements-streamlit.txt
   ```

4. **Configure your Groq API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your Groq API Key:
   # GROQ_API_KEY=your_groq_api_key_here
   ```
   Alternatively, export it directly in the shell:
   ```bash
   export GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Run the Streamlit application**
   ```bash
   ./run_streamlit.sh
   # or directly:
   streamlit run streamlit_app.py
   ```
   The app will be available at `http://localhost:8501` (or the port printed by Streamlit).

## Running Backend and Frontend Separately

If you prefer to start the FastAPI backend and the Streamlit frontend in separate terminals:

**Start the Backend:**
```bash
uvicorn backend.main:app --reload
```

**Start the Frontend (in a new terminal):**
```bash
streamlit run streamlit_app.py
```

## Deployment Instructions

### HuggingFace Spaces

This project is compatible with HuggingFace Spaces (Streamlit environment).
1. Create a new Space on HuggingFace and select "Streamlit" as the SDK.
2. Upload the repository files to the Space.
3. Configure the `GROQ_API_KEY` in the Space's Settings -> Secrets.
4. The space will automatically run `app.py` if placed at the root, or you can point it to `streamlit_app.py`. Note: HF Spaces runs everything on a single instance, so you would need to run the FastAPI backend in a background thread or merge the logic. However, for a split architecture, Render is recommended.

### Render Deployment

The repository includes a `render.yaml` Blueprint for deploying both the backend and frontend as separate web services.
1. Connect your GitHub repository to Render.
2. Go to Blueprints -> New Blueprint Instance -> Select your repo.
3. Render will detect the `render.yaml` and create two services: `healthcare-rag-backend` and `healthcare-rag-frontend`.
4. Ensure you set the `GROQ_API_KEY` environment variable in the Render Dashboard for the backend service.
5. Update the `BACKEND_URL` environment variable for the frontend service to match your actual deployed backend URL once it's created.
