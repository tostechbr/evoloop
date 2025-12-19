"""
EvoLoop UI Module.

Provides a visual interface for reviewing traces and annotating them.
This module requires the [ui] extra: pip install evoloop[ui]

Features:
- Browse traces with filtering
- Annotate with Pass/Fail + Critique
- View failure taxonomy
- Export annotations
"""

try:
    import streamlit  # noqa: F401
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def check_streamlit_installed() -> None:
    """Check if streamlit is installed, raise helpful error if not."""
    if not HAS_STREAMLIT:
        raise ImportError(
            "Streamlit is required for the EvoLoop UI. "
            "Install it with: pip install evoloop[ui]"
        )


def launch(port: int = 8501, db_path: str = "evoloop.db") -> None:
    """
    Launch the EvoLoop UI.
    
    Args:
        port: Port to run the Streamlit app on.
        db_path: Path to the SQLite database.
    
    Example:
        >>> from evoloop.ui import launch
        >>> launch(port=8501)
    """
    check_streamlit_installed()
    
    import subprocess
    import sys
    from pathlib import Path
    
    app_path = Path(__file__).parent / "app.py"
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", str(port),
        "--",
        "--db-path", db_path,
    ]
    
    subprocess.run(cmd)


__all__ = ["launch", "check_streamlit_installed", "HAS_STREAMLIT"]
