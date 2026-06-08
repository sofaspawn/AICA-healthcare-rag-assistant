#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}Multimodal Clinical Intelligence Platform${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}\n"

# 1. Build frontend
echo -e "${YELLOW}Building modern Vite frontend...${NC}"
cd frontend
npm install
npm run build
cd ..
echo -e "${GREEN} Frontend built successfully.${NC}\n"

# 2. Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Running setup...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 3. Check Ollama
echo -e "${YELLOW}Checking Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN} Ollama is running${NC}\n"
else
    echo -e "${RED} Ollama is not detected!${NC}"
    echo -e "   Please open a separate terminal and run: ${GREEN}ollama serve${NC}\n"
    echo -e "   Ensure required models are pulled:"
    echo -e "     ${GREEN}ollama pull qwen2.5:7b${NC}"
    echo -e "     ${GREEN}ollama pull llava${NC}\n"
fi

# 4. Start Backend
echo -e "${GREEN}Starting backend server and unified UI...${NC}"
echo -e "The complete platform will be available at: ${GREEN}http://localhost:8000${NC}\n"

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
