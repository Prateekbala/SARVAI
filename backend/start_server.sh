#!/bin/bash
cd /Users/prateek/code/SarvAI/backend

echo "🚀 Starting SARVAI Backend Server..."
echo "=================================="

# Use the venv's python directly
export PYTHONPATH="/Users/prateek/code/SarvAI/backend:$PYTHONPATH"

exec venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
