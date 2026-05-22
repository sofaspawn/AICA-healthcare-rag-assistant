# Deployment Guide - Healthcare RAG Assistant on Streamlit

## Option 1: Streamlit Community Cloud (Recommended - Free)

### Setup

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Go to Streamlit Cloud**
   - Visit https://share.streamlit.io
   - Click "New app"
   - Select your GitHub repository
   - Enter: `streamlit_app.py` as the main file
   - Deploy!

3. **Configure Secrets**
   - In your Streamlit Cloud dashboard
   - Click the "⋮" menu → Settings
   - Select "Secrets"
   - Add your environment variables:
     ```
     OLLAMA_BASE_URL=http://your-ollama-url:11434/v1
     OLLAMA_MODEL=qwen2.5:7b
     OPENROUTER_API_KEY=your_key_here
     ```

4. **Optional: Deploy Ollama Separately**
   - Use a service like AWS EC2 or DigitalOcean
   - Run Ollama there
   - Point `OLLAMA_BASE_URL` to that instance

---

## Option 2: Render.com (Free tier available)

### Setup

1. **Create Web Service**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Choose Python runtime

2. **Configure Build & Start**
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     streamlit run streamlit_app.py --server.port=10000 --server.address=0.0.0.0
     ```

3. **Set Environment Variables**
   - In Render dashboard → Environment
   - Add all required `.env` variables
   - Add: `STREAMLIT_SERVER_HEADLESS=true`

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete

---

## Option 3: Hugging Face Spaces (Free)

### Setup

1. **Create New Space**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Name it `healthcare-rag-assistant`
   - Select **Streamlit** as runtime
   - Public or Private

2. **Upload Code**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/healthcare-rag-assistant
   cd healthcare-rag-assistant
   git remote add upstream https://github.com/samridh-111/healthcare-rag-assistant.git
   git pull upstream main
   git push
   ```

3. **Add Secrets**
   - In Space settings → Repository secrets
   - Add environment variables

4. **Deploy**
   - Automatically deploys on push!

---

## Option 4: Railway (Easy, paid after free credits)

### Setup

1. **Connect GitHub**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repo

2. **Configure**
   - Add variables in project settings
   - Railway auto-detects requirements.txt

3. **Set Start Command**
   - In deployment settings, add:
     ```
     streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
     ```

---

## Important Considerations

### LLM Inference

**For Cloud Deployment, you have options:**

1. **Local Ollama (Self-hosted)**
   - Deploy Ollama on your own server
   - Streamlit Cloud → connects to it
   - Full privacy, but you manage infra
   - Cheapest if you have existing server

2. **OpenRouter API** (Easiest)
   - Just add API key to secrets
   - No server management
   - Cost: ~$0.01-0.10 per query
   - Update `backend/rag/chat.py` to use OpenRouter

3. **Azure OpenAI** (Enterprise)
   - Update chat.py to use Azure endpoint
   - Professional support available

### Vector Store Persistence

- ChromaDB files are stored in `backend/db/`
- Cloud deployments use ephemeral storage
- **Solution:** Use persistent storage service
  - **Render:** Use volume mount
  - **Railway:** Attach PostgreSQL for persistence
  - **Hugging Face Spaces:** Use dataset library
  - **Streamlit Cloud:** Upload initial data on startup

### Environment File

**Don't commit `.env`!** Instead:
- Add to `.gitignore` (already done)
- Use cloud platform's secrets manager
- Each platform has different UI for this

---

## Quick Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Cloud platform account created
- [ ] Secrets configured (API keys, URLs)
- [ ] Start command configured
- [ ] Initial data ingestion plan (dataset or documents)
- [ ] Test on free tier first
- [ ] Monitor usage and costs

---

## Troubleshooting Cloud Deployment

### "Module not found" error
- Ensure `requirements.txt` includes all dependencies
- Run `pip install -r requirements.txt` locally to test

### "Connection refused" to Ollama
- If using local Ollama: not possible with cloud Streamlit
- Solution: Use OpenRouter or cloud-hosted Ollama
- Or: Deploy Ollama to same platform (complex)

### Slow responses
- Cloud free tiers have limited resources
- Consider paid tier or optimize model size
- Use faster model: `mistral:7b` instead of `qwen2.5:7b`

### Out of memory
- Reduce batch sizes in code
- Use smaller embedding models
- Add: `--logger.level=error` to reduce logs

### Data not persisting
- Cloud instances restart frequently
- Need persistent storage service
- Or regenerate from uploaded files each time

---

## Cost Estimates (Monthly)

| Platform | Model | Cost |
|----------|-------|------|
| Streamlit Cloud (Free) | Ollama (self-hosted) | $0 + server cost |
| Render (Free) | Ollama included | $0 (limited) |
| Railway | Ollama included | $5-20 |
| Hugging Face | Ollama included | $0 (limited) |
| With OpenRouter | API calls | $1-10 |

---

## Recommended for Production

**Best setup for production:**
1. Streamlit Cloud (or similar) for frontend
2. Dedicated Ollama server on:
   - AWS EC2 (g4dn instance, ~$0.50/hr)
   - DigitalOcean GPU ($60-120/month)
   - RunPod ($10-30/month)
3. Optional: PostgreSQL for data persistence

This keeps frontend cheap and inference optimized!
