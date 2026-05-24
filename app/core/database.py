from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine import make_url

def get_engine():
    from app.core.config import settings
    url = make_url(settings.DATABASE_URL)
    if "+asyncpg" not in url.get_driver_name():
        url = url.set(drivername=f"{url.get_driver_name()}+asyncpg")
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
