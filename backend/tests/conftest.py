"""Shared test fixtures."""

import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.data_loader import load_all


@pytest.fixture(scope="session")
def data():
    return load_all()


SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def load_snapshots():
    """Load all snapshot JSON files from the snapshots directory."""
    snapshots = []
    for f in sorted(SNAPSHOT_DIR.glob("*.json")):
        snapshots.append(json.loads(f.read_text()))
    return snapshots
