# Use an official Python image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire app
COPY . .

# Expose the port FastAPI will run on
EXPOSE 443

# Start the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "104.53.222.47", "--port", "443", "--ssl-keyfile", "watchdog.key", "--ssl-certfile", "watchdog.crt",]
