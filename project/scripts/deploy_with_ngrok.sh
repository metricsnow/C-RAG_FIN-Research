#!/bin/bash
# Local Deployment with ngrok Tunneling
# This script runs the Streamlit app locally and creates an ngrok tunnel for external access
# Useful for demos and testing without VPS deployment

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Local Deployment with ngrok Tunneling ===${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}Error: ngrok is not installed.${NC}"
    echo "Install ngrok:"
    echo "  macOS: brew install ngrok/ngrok/ngrok"
    echo "  Or download from: https://ngrok.com/download"
    echo ""
    echo "After installation, you may need to authenticate:"
    echo "  ngrok config add-authtoken YOUR_AUTH_TOKEN"
    exit 1
fi

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
        echo -e "${YELLOW}Please edit .env file and add your configuration${NC}"
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

# Start Streamlit in background
echo -e "${GREEN}Starting Streamlit application in background...${NC}"
python scripts/run_streamlit.py &
STREAMLIT_PID=$!

# Wait a moment for Streamlit to start
sleep 3

# Check if Streamlit started successfully
if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo -e "${RED}Error: Streamlit failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}Streamlit is running on http://localhost:8501${NC}"

# Start ngrok tunnel
echo -e "${YELLOW}Starting ngrok tunnel...${NC}"
echo "Creating tunnel to http://localhost:8501"
echo ""

# Kill ngrok if already running on port 8501
pkill -f "ngrok.*8501" || true

# Start ngrok
ngrok http 8501 &
NGROK_PID=$!

# Wait a moment for ngrok to start
sleep 2

# Get ngrok public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$NGROK_URL" ]; then
    echo -e "${YELLOW}Waiting for ngrok to initialize...${NC}"
    sleep 3
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)
fi

if [ -n "$NGROK_URL" ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment successful!${NC}"
    echo -e "${GREEN}Public URL: ${NGROK_URL}${NC}"
    echo -e "${GREEN}Local URL: http://localhost:8501${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Press Ctrl+C to stop both Streamlit and ngrok"
    echo ""
    echo -e "${YELLOW}Note:${NC} The ngrok URL will change each time you restart ngrok (free tier)."
    echo "For a permanent URL, consider VPS deployment (see docs/reference/deployment.md)"
else
    echo -e "${YELLOW}Warning: Could not retrieve ngrok URL.${NC}"
    echo "Check ngrok dashboard: http://localhost:4040"
fi

# Wait for user interrupt
trap "echo ''; echo -e '${YELLOW}Stopping services...${NC}'; kill $STREAMLIT_PID $NGROK_PID 2>/dev/null; exit" INT TERM

# Keep script running
wait
