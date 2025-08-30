#!/bin/bash

# Get the port from environment variable, default to 8000
PORT=${PORT:-8000}

echo "Starting application on port $PORT"

# Start the FastAPI application
exec uvicorn main:app --host 0.0.0.0 --port $PORT
