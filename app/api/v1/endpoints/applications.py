import os
import shutil
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Body # Added Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.api import deps
from app.core.database import get_db
from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.models.user import UserRole, User
from app.schemas.application import Application as ApplicationSchema
from app.modules import ai_engine
from app.services.application_score_service import calculate_and_update_score # Import the new service function

from sqlalchemy.orm import selectinload
from app.core.config import settings # Import settings

router = APIRouter()

# Ensure upload directory exists based on settings
UPLOAD_DIR = settings.RESUME_UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

from app.models.candidate_profile import CandidateProfile
from app.models.interview import Interview, InterviewSession, EvaluationReport

@router.post("/apply", response_model=ApplicationSchema)
async def apply_for_job(
    *,
    db: AsyncSession = Depends(get_db),
    job_id: int = Form(...),
    background_tasks: BackgroundTasks, # Inject BackgroundTasks
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Apply for a job using the candidate's existing resume.
    """
    # 1. Verify Job exists
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2. Get Candidate's Resume
    result = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    
    if not profile or not profile.resume_path:
        raise HTTPException(status_code=400, detail="Candidate profile or resume not found. Please complete your profile.")

    # Check if candidate has already applied for this job
    existing_application_result = await db.execute(
        select(Application).where(
            Application.candidate_id == current_user.id, Application.job_id == job_id
        )
    )
    if existing_application_result.first():
        raise HTTPException(status_code=400, detail="You have already applied for this job.")

    # 3. Create application record
    db_obj = Application(
        candidate_id=current_user.id,
        job_id=job_id,
        resume_url=profile.resume_path,
        status=ApplicationStatus.APPLIED
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    # Schedule AI Parsing in background using FastAPI's BackgroundTasks
    background_tasks.add_task(
        calculate_and_update_score,
        app_id=db_obj.id,
        resume_path=profile.resume_path.lstrip('/'), # Ensure resume_path is relative
        job_description=job.description
    )

    # Eagerly load relationships for response serialization
    loaded_application_result = await db.execute(
        select(Application)
        .options(selectinload(Application.candidate), selectinload(Application.job))
        .where(Application.id == db_obj.id)
    )
    loaded_db_obj = loaded_application_result.scalar_one()
    
    return loaded_db_obj

@router.get("/", response_model=List[ApplicationSchema])
async def read_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Retrieve applications. 
    If Recruiter/Admin: Retrieve all applications for their jobs.
    If Candidate: Retrieve their own applications.
    """
    query = select(Application).options(
        selectinload(Application.candidate),
        selectinload(Application.job),
        selectinload(Application.interviews).selectinload(Interview.sessions).selectinload(InterviewSession.report)
    )

    if current_user.role in [UserRole.RECRUITER, UserRole.ADMIN]:
        # For recruiters, we want all applications for jobs they created
        if current_user.role == UserRole.ADMIN:
             result = await db.execute(query)
        else:
            result = await db.execute(
                query.join(Job).where(Job.recruiter_id == current_user.id)
            )
    else:
        # For candidates, same as /me
        result = await db.execute(
            query.where(Application.candidate_id == current_user.id)
        )
    
    apps = result.scalars().all()
    # Process additional fields
    for app in apps:
        if app.interviews:
            # Sort interviews by created_at desc
            latest_interview = sorted(app.interviews, key=lambda x: x.created_at, reverse=True)[0]
            app.interview_status = latest_interview.status.value
            if latest_interview.sessions:
                latest_session = sorted(latest_interview.sessions, key=lambda x: x.started_at, reverse=True)[0]
                if latest_session.report:
                    app.interview_result = latest_session.report
    
    return apps

@router.patch("/{application_id}/status", response_model=ApplicationSchema)
async def update_application_status(
    application_id: int,
    status: ApplicationStatus = Body(embed=True), # Accept status from JSON body
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.RECRUITER, UserRole.ADMIN]))
) -> Any:
    """
    Update application status (Recruiter/Admin only).
    """
    result = await db.execute(
        select(Application)
        .where(Application.id == application_id)
        .options(selectinload(Application.job), selectinload(Application.candidate))
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if recruiter owns the job
    if current_user.role == UserRole.RECRUITER and application.job.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this application")
    
    application.status = status
    await db.commit()
    await db.refresh(application)
    return application

@router.get("/me", response_model=List[ApplicationSchema])
async def read_my_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Retrieve current user's applications.
    """
    query = select(Application).where(Application.candidate_id == current_user.id).options(
        selectinload(Application.candidate),
        selectinload(Application.job),
        selectinload(Application.interviews).selectinload(Interview.sessions).selectinload(InterviewSession.report)
    )
    result = await db.execute(query)
    apps = result.scalars().all()
    # Process additional fields for interviews
    for app in apps:
        if app.interviews:
            latest_interview = sorted(app.interviews, key=lambda x: x.created_at, reverse=True)[0]
            app.interview_status = latest_interview.status.value
            if latest_interview.sessions:
                latest_session = sorted(latest_interview.sessions, key=lambda x: x.started_at, reverse=True)[0]
                if latest_session.report:
                    app.interview_result = latest_session.report
    return apps

@router.get("/job/{job_id}", response_model=List[ApplicationSchema])
async def read_job_applications(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.RECRUITER, UserRole.ADMIN]))
) -> Any:
    """
    Retrieve all applications for a specific job (Recruiter/Admin only).
    """
    result = await db.execute(
        select(Application).where(Application.job_id == job_id)
    )
    return result.scalars().all()