#!/bin/bash
# Starts the QuickRx backend. Run from anywhere: ./start-backend.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
  echo "Creating virtual environment (first run only)..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "Starting QuickRx backend at http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --port 8000
