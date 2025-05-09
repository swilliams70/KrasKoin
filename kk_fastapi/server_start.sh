#!/bin/bash


echo "Installing dependencies..."
pip install -r requirements.txt

echo "Dependencies installed."
echo "Starting FastAPI server..."

# uvicorn app.main:app --host 104.53.222.47 --port 443 --reload --proxy-headers --ssl-keyfile watchdog.key --ssl-certfile watchdog.crt
uvicorn app.main:app --host 0.0.0.0 --port 8443 --reload
