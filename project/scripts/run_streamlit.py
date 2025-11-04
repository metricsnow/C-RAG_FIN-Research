"""
Script to run Streamlit frontend application.

Usage:
    python scripts/run_streamlit.py
    OR
    streamlit run app/ui/app.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    # Get path to app
    app_path = project_root / "app" / "ui" / "app.py"
    
    # Run Streamlit
    sys.argv = ["streamlit", "run", str(app_path)]
    stcli.main()

