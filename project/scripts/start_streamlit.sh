#!/bin/bash
# Wrapper script to start Streamlit with correct PYTHONPATH

set -e

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Activate virtual environment
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Set PYTHONPATH explicitly
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Change to project root
cd "$PROJECT_ROOT"

# Run Streamlit with explicit PYTHONPATH
exec python -m streamlit run app/ui/app.py "$@"
