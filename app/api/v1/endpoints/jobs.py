from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.core.database import get_db
from app.models.job import Job
from app.models.user import UserRole, User
from app.schemas.job import JobCreate, JobUpdate, Job as JobSchema

router = APIRouter()

@router.get("/", response_model=List[JobSchema])
async def read_jobs(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve jobs.
    """
    result = await db.execute(select(Job).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=JobSchema)
async def create_job(
    *,
    db: AsyncSession = Depends(get_db),
    job_in: JobCreate,
    current_user: User = Depends(deps.RoleChecker([UserRole.RECRUITER, UserRole.ADMIN]))
) -> Any:
    """
    Create new job.
    """
    db_obj = Job(
        **job_in.model_dump(),
        recruiter_id=current_user.id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/{id}", response_model=JobSchema)
async def read_job(
    *,
    db: AsyncSession = Depends(get_db),
    id: int
) -> Any:
    """
    Get job by ID.
    """
    result = await db.execute(select(Job).where(Job.id == id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{id}", response_model=JobSchema)
async def update_job(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    job_in: JobUpdate,
    current_user: User = Depends(deps.RoleChecker([UserRole.RECRUITER, UserRole.ADMIN]))
) -> Any:
    """
    Update a job.
    """
    result = await db.execute(select(Job).where(Job.id == id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if current_user.role != UserRole.ADMIN and job.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = job_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job
