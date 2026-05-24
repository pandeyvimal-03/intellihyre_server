from typing import  Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import os # Re-add import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "IntelliHire"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str 
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # MongoDB
    MONGODB_URL: Optional[str] = None
    MONGODB_DB_NAME: Optional[str] = None
    
    # Redis
    REDIS_URL: str

    # Uploads (Re-add these settings)
    BASE_UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads"))
    RESUME_UPLOAD_DIR: str = os.path.join(BASE_UPLOAD_DIR, "resumes")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings() # type: ignore[call-arg]
