"""Pytest configuration for the Piano Performance Analyzer test suite.

Adds the backend directory to sys.path so test files can import
project modules (models, comparator, etc.).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
