"""
Script to run Streamlit frontend application.

Usage:
    python scripts/run_streamlit.py
    OR
    streamlit run app/ui/app.py
"""

import os
import sys
from pathlib import Path

# Add project root to path - must be done before any app imports
project_root = Path(__file__).parent.parent
project_root_str = str(project_root.absolute())

# Add to Python path
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# CRITICAL: Set PYTHONPATH BEFORE importing streamlit
# This ensures Streamlit's subprocess execution inherits the correct path
os.environ["PYTHONPATH"] = (
    project_root_str + os.pathsep + os.environ.get("PYTHONPATH", "")
)

if __name__ == "__main__":
    # Change to project root directory to ensure correct working directory
    os.chdir(project_root_str)

    # CRITICAL: Export PYTHONPATH to environment so subprocesses inherit it
    # This must be done before importing streamlit
    os.environ["PYTHONPATH"] = (
        project_root_str + os.pathsep + os.environ.get("PYTHONPATH", "")
    )

    import streamlit.web.cli as stcli

    # Get path to app (relative to project root)
    app_path = project_root / "app" / "ui" / "app.py"

    # Run Streamlit from project root
    # The PYTHONPATH is now set in environment, so subprocesses will inherit it
    sys.argv = ["streamlit", "run", str(app_path)]
    stcli.main()
