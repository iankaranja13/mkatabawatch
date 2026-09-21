#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  🏛️ MkatabaWatch 🇹🇿 — Public Contracts, Public Evidence"
echo "=========================================================="

cd "$(dirname "$0")"

# Create venv if not exists
if [ ! -d "backend/.venv" ]; then
    echo "Creating Python virtual environment in backend/.venv..."
    python3 -m venv backend/.venv
fi

# Activate venv
source backend/.venv/bin/activate

# Install requirements
echo "Installing backend dependencies..."
pip install -q -r backend/requirements.txt

# Seed verified data if DB not present
if [ ! -f "mkatabawatch.db" ]; then
    echo "Seeding verified real OCDS projects and demo community evidence..."
    python -m backend.app.ingest
    python -m backend.app.seed_evidence
fi

DEFAULT_PORT=8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "ℹ️  Port 8000 is currently in use by another process. Automatically using port 8001."
    DEFAULT_PORT=8001
fi
PORT="${PORT:-$DEFAULT_PORT}"

echo ""
echo "🚀 Starting MkatabaWatch at http://localhost:${PORT}"
echo "📖 API documentation available at http://localhost:${PORT}/docs"
echo "=========================================================="
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT}"
