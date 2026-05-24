# IntelliHire Backend

FastAPI-based AI recruitment engine.

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- OpenAI API Key

### Running with Docker

1. Create a `.env` file in this directory based on the template.
2. Run:

```bash
docker-compose up --build
```

The API will be available at [http://localhost:8000](http://localhost:8000).
Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Local Development (without Docker)

1. Install [Poetry](https://python-poetry.org/).
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Run migrations:
   ```bash
   poetry run alembic upgrade head
   ```
4. Start the server:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## 🏗 Architecture

- **FastAPI:** High-performance web framework.
- **SQLAlchemy 2.0:** Modern async ORM.
- **Alembic:** Database migrations.
- **Redis:** Interview state management.
- **OpenAI GPT-4o & Whisper:** AI-powered interviewing.

## 📂 Structure

- `app/api/`: REST & WebSocket endpoints.
- `app/models/`: Database entities.
- `app/modules/`: Business logic & AI integrations.
- `app/schemas/`: Pydantic validation models.
