#!/bin/bash


echo "Installing dependencies..."
pip install -r requirements.txt

echo "Dependencies installed."
echo "Starting FastAPI server..."

# uvicorn app.main:app --host 104.53.222.47 --port 8888 --reload --proxy-headers --ssl-keyfile watchdog.key --ssl-certfile watchdog.crt
uvicorn app.main:app --host localhost --port 8888 --reload --proxy-headers --ssl-keyfile watchdog.key --ssl-certfile watchdog.crt
