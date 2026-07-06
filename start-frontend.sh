#!/bin/bash
# Starts the QuickRx frontend dev server. Run from anywhere: ./start-frontend.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
  echo "Installing dependencies (first run only)..."
  npm install
fi

echo ""
echo "Starting QuickRx frontend at http://localhost:5173"
echo ""

npm run dev
