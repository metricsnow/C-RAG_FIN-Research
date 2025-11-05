#!/bin/bash
# Local Deployment Script
# This script sets up and runs the Streamlit app locally with proper environment configuration

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Local Deployment Setup ===${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found.${NC}"
    echo "Please create it first: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found.${NC}"
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file and add your configuration (especially OPENAI_API_KEY if using OpenAI embeddings)${NC}"
    else
        echo -e "${RED}Error: .env.example not found. Please create .env file manually.${NC}"
        exit 1
    fi
fi

# Verify Ollama is running
echo -e "${YELLOW}Checking Ollama service...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}Error: Ollama is not running on http://localhost:11434${NC}"
    echo "Please start Ollama: ollama serve"
    exit 1
fi
echo -e "${GREEN}Ollama is running${NC}"

# Check if ChromaDB data exists
if [ ! -d "data/chroma_db" ]; then
    echo -e "${YELLOW}Warning: ChromaDB data directory not found.${NC}"
    echo "You may need to ingest documents first. See README.md for instructions."
fi

# Start Streamlit
echo -e "${GREEN}Starting Streamlit application...${NC}"
echo "Application will be available at: http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

python scripts/run_streamlit.py
