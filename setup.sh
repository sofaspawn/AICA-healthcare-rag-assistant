#!/bin/bash
echo "Setting up Healthcare RAG Assistant..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo "Setup complete! Please configure your .env file."
echo "Run 'source venv/bin/activate' to activate the environment."
