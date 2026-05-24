#!/bin/bash

# Wait for database to be ready (optional but recommended)
# You could use a tool like wait-for-it.sh here

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start server
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
