import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.core.database import get_db
from app.models.interview import Interview, InterviewStatus
from app.models.application import Application, ApplicationStatus
from app.models.user import UserRole, User
from app.schemas.interview import InterviewCreate, Interview as InterviewSchema

router = APIRouter()

@router.post("/schedule", response_model=InterviewSchema)
async def schedule_interview(
    *,
    db: AsyncSession = Depends(get_db),
    interview_in: InterviewCreate,
    current_user: User = Depends(deps.RoleChecker([UserRole.RECRUITER, UserRole.ADMIN]))
) -> Any:
    """
    Schedule an interview for an application.
    """
    # 1. Verify Application exists
    result = await db.execute(select(Application).where(Application.id == interview_in.application_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # 2. Generate unique token and expiry (48 hours as per synopsis)
    token = str(uuid.uuid4())
    expires_at = interview_in.scheduled_at + timedelta(hours=48)

    db_obj = Interview(
        application_id=interview_in.application_id,
        token=token,
        scheduled_at=interview_in.scheduled_at,
        expires_at=expires_at,
        status=InterviewStatus.PENDING
    )
    db.add(db_obj)
    
    # Update application status
    application.status = ApplicationStatus.INTERVIEW_SCHEDULED
    
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/validate/{token}", response_model=InterviewSchema)
async def validate_interview_token(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Validate an interview token for the candidate to join.
    """
    result = await db.execute(select(Interview).where(Interview.token == token))
    interview = result.scalar_one_or_none()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Invalid interview link")
    
    if interview.status != InterviewStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Interview is already {interview.status}")
    
    if datetime.now(timezone.utc) > interview.expires_at.replace(tzinfo=timezone.utc):
        interview.status = InterviewStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Interview link has expired")
        
    return interview

@router.get("/application/{application_id}", response_model=InterviewSchema)
async def get_interview_by_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get interview details for a specific application.
    """
    result = await db.execute(
        select(Interview).where(Interview.application_id == application_id)
    )
    interview = result.scalar_one_or_none()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found for this application")
    
    # Check if the current user is the candidate who applied or a recruiter/admin
    res_app = await db.execute(select(Application).where(Application.id == application_id))
    application = res_app.scalar_one_or_none()
    
    if not application:
         raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role == UserRole.CANDIDATE and application.candidate_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    return interview

@router.get("/me", response_model=List[InterviewSchema])
async def get_my_scheduled_interviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.CANDIDATE]))
) -> Any:
    """
    Retrieve all scheduled interviews for the current candidate.
    """
    result = await db.execute(
        select(Interview)
        .join(Application)
        .where(Application.candidate_id == current_user.id)
    )
    return result.scalars().all()
