#!/bin/bash

# AI Self-Reflection Backend Demo Runner
# This script sets up and runs the demo for the AI self-reflection backend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🤖 AI Self-Reflection Backend Demo"
echo "=================================="
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not found. Please install pip."
    exit 1
fi

# Install demo dependencies if needed
echo "🔍 Checking demo dependencies..."
if ! python3 -c "import requests, rich" 2>/dev/null; then
    echo "📦 Installing demo dependencies..."
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
else
    echo "✅ Demo dependencies are installed"
fi

echo

# Check if backend server is running
echo "🔍 Checking if backend server is running..."
if ! curl -s http://localhost:8087 > /dev/null; then
    echo "❌ Backend server is not running at http://localhost:8087"
    echo
    echo "💡 To start the backend server:"
    echo "   cd $PROJECT_ROOT/backend"
    echo "   uvicorn main:app --reload --port 8087"
    echo
    echo "⚠️  Make sure you have:"
    echo "   1. Set up your .env.local file with OPENAI_API_KEY"
    echo "   2. Installed backend dependencies (uv sync or pip install -r requirements.txt)"
    echo
    exit 1
fi

echo "✅ Backend server is running"
echo

# Run the demo
echo "🚀 Starting demo..."
echo
python3 "$SCRIPT_DIR/demo.py" "$@"