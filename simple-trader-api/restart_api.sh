#!/bin/bash
# Restart API script

echo "Stopping existing API processes..."
# Find and kill any existing Python processes running app.main
pkill -f "python -m app.main" || echo "No existing API process found"

sleep 2

echo "Starting API..."
cd "$(dirname "$0")"
python -m app.main

echo "API should now be running on http://localhost:8000"
