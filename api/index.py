"""Vercel serverless entrypoint for the Carbon Scenario Explorer API.

Vercel's @vercel/python builder detects the module-level ``app`` ASGI
application and serves it as a serverless function. All requests routed to
``/api/*`` (see ``vercel.json``) are handled by the existing FastAPI backend.

The backend package lives in ``backend/``, which is not importable by default
from this file's location, so we add it to ``sys.path`` before importing.

Public deployments should set ``PUBLIC_DEMO_MODE=true`` (and optionally
``DATA_MODE=external``) in the Vercel project environment so the backend loads
only demo-safe, external/synthetic data. See ``backend/app/config.py``.
"""

import sys
from pathlib import Path

# Make the backend package importable (repo_root/backend).
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402  (path setup must run first)

# Vercel's Python runtime looks for a module-level ASGI/WSGI callable named `app`.
__all__ = ["app"]
