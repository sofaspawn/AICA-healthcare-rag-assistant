#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}Healthcare RAG Assistant - Streamlit Setup${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}\n"

# Check Python
echo -e "${YELLOW}Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED} Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN} Found: $PYTHON_VERSION${NC}\n"

# Check/Create venv
echo -e "${YELLOW}Checking virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN} Virtual environment ready${NC}\n"

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
pip install --quiet -r requirements.txt 2>&1 | grep -v "already satisfied" || true
echo -e "${GREEN} Dependencies installed${NC}\n"

# Check .env
echo -e "${YELLOW}Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env from template"
    else
        cat > .env << EOF
# Ollama Configuration (local inference)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5:7b

# OpenRouter (optional, cloud inference)
# OPENROUTER_API_KEY=your_key_here
EOF
        echo "Created default .env"
    fi
fi
echo -e "${GREEN} .env file ready${NC}\n"

# Ollama check
echo -e "${YELLOW}Checking Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN} Ollama is running${NC}"
else
    echo -e "${YELLOW}  Ollama not detected${NC}"
    echo "   To start Ollama, run in a separate terminal:"
    echo "   ${GREEN}ollama serve${NC}"
    echo "   Then pull a model: ${GREEN}ollama pull qwen2.5:7b${NC}"
fi
echo ""

# Verify app file
echo -e "${YELLOW}Verifying Streamlit app...${NC}"
if [ -f "streamlit_app.py" ]; then
    echo -e "${GREEN} streamlit_app.py found${NC}"
else
    echo -e "${RED} streamlit_app.py not found${NC}"
    exit 1
fi
echo ""

# Ready to run
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN} Setup complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}\n"

echo "To start the Healthcare RAG Assistant:"
echo -e "  ${GREEN}./run_streamlit.sh${NC}\n"

echo "Or manually run:"
echo -e "  ${GREEN}source venv/bin/activate${NC}"
echo -e "  ${GREEN}streamlit run streamlit_app.py${NC}\n"

echo "The app will be available at:"
echo -e "  ${GREEN}http://localhost:8501${NC}\n"

echo "For more information:"
echo "  • Setup guide: ${GREEN}STREAMLIT_README.md${NC}"
echo "  • Deployment: ${GREEN}DEPLOYMENT.md${NC}"
echo "  • Migration notes: ${GREEN}STREAMLIT_MIGRATION.md${NC}"
