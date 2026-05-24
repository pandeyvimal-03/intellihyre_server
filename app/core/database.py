from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine import URL
from app.core.config import settings

# Force the async driver
url = URL.create_from_string(settings.DATABASE_URL)
if "+asyncpg" not in url.get_driver_name():
    url = url.set(drivername="postgresql+asyncpg")

engine = create_async_engine(url, echo=True)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session
