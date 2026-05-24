from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import traceback
import logging
import os # Added os import

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.redis import connect_to_redis, close_redis_connection

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Serve uploaded files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.on_event("startup")
async def startup_db_client():
    await connect_to_redis()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_redis_connection()

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="http://localhost:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to IntelliHire API"}
