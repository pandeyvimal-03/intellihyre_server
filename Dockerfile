FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (Poetry will manage the virtualenv/environment)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy the rest of the application
COPY . .

# Ensure the start script is executable
RUN chmod +x start.sh

# Force removal of synchronous driver to prevent conflicts
RUN pip uninstall -y psycopg2 psycopg2-binary

# Expose port
EXPOSE 8000

# Use the start.sh script to run migrations and the server
CMD ["./start.sh"]
