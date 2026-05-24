from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine import make_url
import asyncpg

def get_engine():
    from app.core.config import settings
    url = make_url(settings.DATABASE_URL)
    # Explicitly set the driver to asyncpg to avoid plugin loading errors
    url = url.set(drivername="postgresql+asyncpg")
    return create_async_engine(url, echo=True)

engine = get_engine()

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(DeclarativeBase):
    pass
async def get_db():
    async with async_session() as session:
        yield session
