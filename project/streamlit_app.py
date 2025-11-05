"""
Streamlit entry point for the Financial Research Assistant.

This file is located at the project root to ensure proper package imports.
It imports and runs the main Streamlit application from app.ui.app.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in path
_project_root = Path(__file__).parent.absolute()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Set PYTHONPATH for subprocesses
os.environ["PYTHONPATH"] = (
    str(_project_root) + os.pathsep + os.environ.get("PYTHONPATH", "")
)

# Import the main function from the UI module
try:
    from app.ui.app import main
except ImportError as e:
    import streamlit as st

    st.error(f"Failed to import app: {e}")
    st.error(f"sys.path: {sys.path[:3]}")
    st.error(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}")
    st.stop()

if __name__ == "__main__":
    main()
