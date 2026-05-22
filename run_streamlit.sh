#!/bin/bash

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    chmod +x setup.sh
    ./setup.sh
fi

source venv/bin/activate

echo " Starting Healthcare RAG Assistant with Streamlit..."
echo " Open http://localhost:8501 in your browser"
echo ""

# Run Streamlit app
streamlit run streamlit_app.py --logger.level=info
