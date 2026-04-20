"""Verify calculator.py has no IO or framework dependencies."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

FORBIDDEN_MODULES = {
    "fastapi", "uvicorn", "starlette", "requests", "httpx",
    "os", "sys", "subprocess", "pathlib", "shutil",
    "open", "io", "socket", "urllib",
}


def test_calculator_has_no_io_imports():
    calc_path = Path(__file__).parent.parent / "app" / "engine" / "calculator.py"
    source = calc_path.read_text()
    tree = ast.parse(source)

    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and not node.module.startswith("."):
                imported_modules.add(node.module.split(".")[0])

    violations = imported_modules & FORBIDDEN_MODULES
    assert not violations, (
        f"calculator.py imports forbidden modules: {violations}. "
        "The calculation layer must be pure — no IO or framework dependencies."
    )


def test_calculator_constants_dict_exists():
    from app.engine.calculator import CONSTANTS, DATA_KEYS

    assert isinstance(CONSTANTS, dict), "CONSTANTS must be a dict"
    assert len(CONSTANTS) >= 9, f"Expected >= 9 constants, got {len(CONSTANTS)}"

    assert isinstance(DATA_KEYS, dict), "DATA_KEYS must be a dict"
    assert len(DATA_KEYS) >= 9, f"Expected >= 9 data keys, got {len(DATA_KEYS)}"

    # Every constant should be a float
    for key, val in CONSTANTS.items():
        assert isinstance(val, (int, float)), f"CONSTANTS['{key}'] must be numeric, got {type(val)}"

    # Every data key should be a string
    for key, val in DATA_KEYS.items():
        assert isinstance(val, str), f"DATA_KEYS['{key}'] must be a string, got {type(val)}"
