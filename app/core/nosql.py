from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def connect_to_mongo():
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongodb.db = mongodb.client[settings.MONGODB_DB_NAME]

async def close_mongo_connection():
    mongodb.client.close()

def get_nosql_db():
    return mongodb.db
