import os
import io
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.application import Application, ApplicationStatus
from app.schemas.application import ParsedResume
from app.modules import ai_engine

# Database setup (should ideally be shared from app.core.database if possible)
DATABASE_URL = settings.DATABASE_URL
async_engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def calculate_and_update_score(app_id: int, resume_path: str, job_description: str):
    async with async_session_maker() as db:
        try:
            print(f"[{datetime.now()}] Processing score calculation for Application ID: {app_id}")
            print(f"[{datetime.now()}] Resume path: {resume_path}")
            print(f"[{datetime.now()}] Job description (truncated): {job_description[:100]}...")

            # Resolve the full path to the resume file
            # Since this service will be run within the FastAPI app, 
            # resume_path might need to be resolved relative to the project root
            # Let's assume UPLOAD_DIR is configured in settings or passed correctly.
            # For now, let's derive project_root from a known file like main.py or core/config.py
            # A more robust way would be to pass the absolute path or configure UPLOAD_DIR in settings.
            
            # Temporary derivation for project root - will be more robust in a real app
            # Assuming this service file is in server/app/services
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")) 
            full_resume_path = os.path.join(project_root, resume_path)
            
            if not os.path.exists(full_resume_path):
                print(f"[{datetime.now()}] Resume file not found at: {full_resume_path}")
                stmt = select(Application).where(Application.id == app_id)
                result = await db.execute(stmt)
                application = result.scalar_one_or_none()
                if application:
                    application.status = ApplicationStatus.APPLIED # Or a new error status
                    await db.commit()
                return

            with open(full_resume_path, "rb") as f:
                file_content = f.read()

            parsed_data = await ai_engine.parse_resume_with_ai(file_content)
            match_score = await ai_engine.calculate_match_score(parsed_data, job_description)

            stmt = select(Application).where(Application.id == app_id)
            result = await db.execute(stmt)
            application = result.scalar_one_or_none()

            if application:
                application.match_score = match_score
                if application.status == ApplicationStatus.APPLIED:
                    application.status = ApplicationStatus.PARSED
                await db.commit()
                print(f"[{datetime.now()}] Successfully updated match score for application {app_id}: {match_score}")
            else:
                print(f"[{datetime.now()}] Application {app_id} not found for score update.")

        except Exception as e:
            print(f"[{datetime.now()}] Error in background score calculation for app {app_id}: {e}")
            try:
                stmt = select(Application).where(Application.id == app_id)
                result = await db.execute(stmt)
                application = result.scalar_one_or_none()
                if application:
                    # Consider a more specific error status if available
                    # application.status = ApplicationStatus.ERROR
                    await db.commit()
            except Exception as db_e:
                print(f"[{datetime.now()}] Error updating application status after exception for app {app_id}: {db_e}")
