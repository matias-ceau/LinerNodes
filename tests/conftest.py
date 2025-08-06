# Install a minimal Streamlit stub before anything else so tests can patch it
import tests._bootstrap_streamlit_stub  # noqa: F401

# Ensure 'src' directory is on sys.path so 'linernodes' imports resolve during pytest
# This file is intentionally minimal and safe to import in any environment.
import sys
from pathlib import Path

# Project root assumed two levels up from this file: /project/tests/conftest.py
root = Path(__file__).resolve().parents[1]
src = root / "src"

# Prepend to sys.path if not already present
src_str = str(src)
if src_str not in sys.path:
    sys.path.insert(0, src_str)