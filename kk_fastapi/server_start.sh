#!/bin/bash


echo "Installing dependencies..."
pip install -r requirements.txt

echo "Dependencies installed."
echo "Starting FastAPI server..."

uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload
