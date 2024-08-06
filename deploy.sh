#!/bin/bash

# Set the remote server details
REMOTE_SERVER="me-aws-demo"

# Define the commands to be executed on the remote server
REMOTE_COMMANDS=$(cat <<'ENDSSH'
set -e

# Navigate to the PDF-generator directory
cd ./PDF-generator/

# Pull the latest changes from git
echo "Pulling latest changes from git..."
if ! git pull; then
  echo "Error: Failed to pull latest changes from git."
  exit 1
fi

# Check for merge conflicts
if git ls-files -u | grep .; then
  echo "Error: Merge conflicts detected. Resolve conflicts and try again."
  exit 1
fi

# Build Docker containers
echo "Building Docker containers..."
if ! sudo docker-compose build; then
  echo "Error: Docker build failed."
  exit 1
fi

# Start Docker containers
echo "Starting Docker containers..."
if ! sudo docker-compose up -d; then
  echo "Error: Failed to start Docker containers."
  exit 1
fi

echo "Deployment successful."
ENDSSH
)

# Connect to the remote server and execute the commands
ssh "$REMOTE_SERVER" "$REMOTE_COMMANDS"

if [ $? -eq 0 ]; then
  echo "Deployment completed successfully."
  # Redirect to the specified URL after successful deployment
  xdg-open "http://13.233.223.115"
else
  echo "Deployment failed."
fi
