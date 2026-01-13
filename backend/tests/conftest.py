"""
Pytest configuration file
"""
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
