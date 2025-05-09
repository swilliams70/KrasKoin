#!/bin/bash

# Variables
IMAGE_NAME="watchdog.dev"
CONTAINER_NAME="watchdog.dev"
PORT=8443
HOST="localhost"

# Step 1: Build the Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME -f Dockerfile.dev .

# Step 2: Stop and remove any existing container with the same name
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "🧹 Removing existing container..."
    docker rm -f $CONTAINER_NAME
fi

echo "🚀 Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  -v "$(pwd)/app/data:/app/app/data" \
  -v "$(pwd)/app/data/tars:/app/app/data/tars" \
  -p $PORT:8443 \
  $IMAGE_NAME

echo "✅ Server is running at http://localhost:$PORT"
