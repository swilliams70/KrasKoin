#!/bin/bash

# Variables
IMAGE_NAME="watchdawgz.proto"
CONTAINER_NAME="watchdawgz.proto"

# Step 1: Build the Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

# Step 2: Stop and remove any existing container with the same name
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "🧹 Removing existing container..."
    docker rm -f $CONTAINER_NAME
fi

echo "Finished baking proto image for $IMAGE_NAME"
