#!/bin/bash

# Start Nginx in background
nginx -g 'daemon off;' &

# Change to backend directory
cd /app/backend

# Start the backend service with uvicorn
PYTHONPATH=/app/backend uvicorn main:app --host 0.0.0.0 --port 8000