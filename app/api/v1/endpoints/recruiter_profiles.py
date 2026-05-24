from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.recruiter_profile import RecruiterProfile
from app.schemas.recruiter_profile import RecruiterProfileCreate, RecruiterProfileUpdate, RecruiterProfile

router = APIRouter()

@router.post("/me", response_model=RecruiterProfile)
async def create_recruiter_profile(
    profile_in: RecruiterProfileCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    if current_user.role != UserRole.RECRUITER:
        raise HTTPException(status_code=403, detail="Only recruiters can create their profile")
    
    result = await db.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == current_user.id))
    recruiter_profile = result.scalar_one_or_none()

    if recruiter_profile:
        raise HTTPException(status_code=400, detail="Recruiter profile already exists. Use PUT to update.")
    
    db_obj = RecruiterProfile(user_id=current_user.id, **profile_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/me", response_model=RecruiterProfile)
async def get_recruiter_profile(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    if current_user.role != UserRole.RECRUITER:
        raise HTTPException(status_code=403, detail="Not a recruiter account")
    
    result = await db.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == current_user.id))
    recruiter_profile = result.scalar_one_or_none()
    
    if not recruiter_profile:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")
    return recruiter_profile

@router.put("/me", response_model=RecruiterProfile)
async def update_recruiter_profile(
    profile_in: RecruiterProfileUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    if current_user.role != UserRole.RECRUITER:
        raise HTTPException(status_code=403, detail="Only recruiters can update their profile")
    
    result = await db.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == current_user.id))
    recruiter_profile = result.scalar_one_or_none()

    if not recruiter_profile:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(recruiter_profile, field, value)
    
    db.add(recruiter_profile)
    await db.commit()
    await db.refresh(recruiter_profile)
    return recruiter_profile