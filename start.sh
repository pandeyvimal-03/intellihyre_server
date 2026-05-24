#!/bin/bash

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start server using the PORT provided by Railway
echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
