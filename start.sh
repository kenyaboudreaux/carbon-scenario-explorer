#!/bin/bash
# Carbon Scenario Explorer — Local Launcher
set -e
cd "$(dirname "$0")"

VENV_PYTHON="backend/venv/bin/python"

echo ""
echo "  Carbon Scenario Explorer"
echo "  Local Launcher"
echo "  ────────────────────────"
echo ""

# --- Prerequisites ---

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Install Python 3.12+."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "ERROR: npm not found. Install Node.js 22+."
    exit 1
fi

# --- Setup venv if needed ---

if [ ! -f "$VENV_PYTHON" ]; then
    echo "  Setting up Python virtual environment..."
    python3 -m venv backend/venv
    "$VENV_PYTHON" -m pip install -r backend/requirements.txt --quiet
    echo "  Python environment ready."
else
    echo "  Python environment found."
fi

# Verify uvicorn is importable
if ! "$VENV_PYTHON" -c "import uvicorn" 2>/dev/null; then
    echo "  Installing backend dependencies..."
    "$VENV_PYTHON" -m pip install -r backend/requirements.txt --quiet
fi

# --- Setup node_modules if needed ---

if [ ! -d "frontend/node_modules" ]; then
    echo "  Installing frontend dependencies..."
    cd frontend && npm install --silent && cd ..
    echo "  Frontend dependencies ready."
else
    echo "  Frontend dependencies found."
fi

echo ""
echo "  Starting backend..."

# --- Start backend using venv Python directly ---

"$VENV_PYTHON" -m uvicorn --app-dir backend app.main:app --port 8000 &
BACKEND_PID=$!

# --- Health check: wait for backend to respond ---

RETRIES=0
MAX_RETRIES=15
BACKEND_OK=false

while [ $RETRIES -lt $MAX_RETRIES ]; do
    sleep 1
    if kill -0 $BACKEND_PID 2>/dev/null; then
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null | grep -q "200"; then
            BACKEND_OK=true
            break
        fi
    else
        echo ""
        echo "ERROR: Backend process exited. Check logs above."
        exit 1
    fi
    RETRIES=$((RETRIES + 1))
done

if [ "$BACKEND_OK" = false ]; then
    echo ""
    echo "ERROR: Backend did not respond within ${MAX_RETRIES}s. Stopping."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "  Backend ready."
echo "  Starting frontend..."

# --- Start frontend ---

cd frontend
npm run dev -- --host 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "  ┌──────────────────────────────────────────────┐"
echo "  │  Backend:  http://localhost:8000              │"
echo "  │  Frontend: http://localhost:5173              │"
echo "  │  API docs: http://localhost:8000/docs         │"
echo "  │                                              │"
echo "  │  Press Ctrl+C to stop both servers.          │"
echo "  └──────────────────────────────────────────────┘"
echo ""

# --- Cleanup on exit ---

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo 'Servers stopped.'" EXIT

wait
