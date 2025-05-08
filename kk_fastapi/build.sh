#!/bin/bash

# Variables
IMAGE_NAME="watchdog"
CONTAINER_NAME="watchdog"
PORT=443
HOST="104.53.222.47"

# Step 1: Build the Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

# Step 2: Stop and remove any existing container with the same name
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "🧹 Removing existing container..."
    docker rm -f $CONTAINER_NAME
fi

# Step 3: Run the container
echo "🚀 Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:443 \
  $IMAGE_NAME

echo "✅ Server is running at http://$HOST:$PORT"
