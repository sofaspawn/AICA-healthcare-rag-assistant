# Deployment Guide — Multimodal Clinical Intelligence Platform

## Local Development (Recommended)

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| Ollama | latest | [ollama.com/download](https://ollama.com/download) |
| ffmpeg | any | `brew install ffmpeg` (macOS) |

### 1. Clone & Set Up Environment

```bash
git clone <repo-url>
cd healthcare-rag-assistant

python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 2. Pull Ollama Models

```bash
# Required: Clinical reasoning model
ollama pull qwen2.5:7b

# Required: Vision model for medical images and video frames
ollama pull llava

# Optional: Faster/lighter alternative for low-RAM machines
# ollama pull qwen2.5:3b
```

### 3. Start Services

Open **three separate terminals**:

**Terminal 1 — Ollama LLM Server:**
```bash
ollama serve
```

**Terminal 2 — FastAPI Backend:**
```bash
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 — Streamlit Dashboard:**
```bash
source venv/bin/activate
streamlit run streamlit_app.py
```

Then open **http://localhost:8501** in your browser.

---

## Running Just Streamlit (Standalone Mode)

The Streamlit app includes a **direct local fallback** — it will import backend modules
directly if the FastAPI backend is not running. This is the simplest way to run the platform:

```bash
source venv/bin/activate
streamlit run streamlit_app.py
```

> **Note:** Ollama must still be running (`ollama serve`) for reasoning and vision features.

---

## Hugging Face Spaces Deployment

### space configuration (`README.md` header)

```yaml
---
title: Multimodal Clinical Intelligence Platform
emoji: 🩺
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.32.0
app_file: streamlit_app.py
pinned: false
---
```

### System Packages (packages.txt)

Create a `packages.txt` file in the root:

```
ffmpeg
libgl1-mesa-glx
libglib2.0-0
```

### requirements.txt

Use the existing `requirements.txt`. Remove `ollama` if you are using a Groq/cloud fallback on Spaces, or ensure Ollama is available via a Docker-based Space.

### Important Limitations on Spaces

- **Ollama is NOT available on standard CPU/GPU Spaces** — you need to use a Docker Space or a hosted model endpoint.
- For Spaces deployment, consider adding a Groq API fallback for the reasoning layer (set `GROQ_API_KEY` in Spaces secrets).

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Optional: Groq API fallback (for cloud deployment)
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

> For **local deployment**, no API keys are required — the platform runs entirely on local Ollama models.

---

## Directory Structure

```
healthcare-rag-assistant/
├── backend/
│   ├── clinical/          # Patient state, scoring, emergency rules
│   ├── database/          # SQLite models and DatabaseManager
│   ├── ingestion/         # All ingestion modules (doc/image/audio/video)
│   │   └── documents/     # PDF, DOCX, TXT parsers
│   ├── knowledge/         # Clinical knowledge builder (→ ChromaDB)
│   ├── rag/               # Retriever, Ollama client, chat pipeline
│   └── rules/             # SOS detection rules
├── scratch/
│   └── uploads/           # Uploaded files (auto-created)
├── streamlit_app.py       # Main UI
├── backend/main.py        # FastAPI backend
├── requirements.txt
└── DEPLOYMENT.md
```

---

## Verification

After starting all services, run the following checks:

```bash
# 1. Check FastAPI health
curl http://localhost:8000/health

# 2. Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "I have a headache and mild fever", "patient_id": "patient_001"}'

# 3. Check patient timeline
curl http://localhost:8000/patient/timeline?patient_id=patient_001
```
