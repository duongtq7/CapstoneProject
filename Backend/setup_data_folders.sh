#!/bin/bash

# Remove old data directory if it exists
if [ "$1" = "-r" ]; then
  if [ "$EUID" -ne 0 ]; then
    echo "Error: Removing data requires root permissions. Please run with sudo"
    exit 1
  fi
  echo "Removing existing data directory..."
  rm -rf data
fi

# Create the main data directory
mkdir -p data

# Create the required subdirectories
mkdir -p data/minio_data
mkdir -p data/minio_config
mkdir -p data/postgres_data
mkdir -p data/qdrant_data

echo "Created the following directories:"
echo "- data/minio_data"
echo "- data/minio_config"
echo "- data/postgres_data"
echo "- data/qdrant_data"

# Set appropriate permissions
chmod -R 755 data

echo "Directories are ready for Docker volumes"
