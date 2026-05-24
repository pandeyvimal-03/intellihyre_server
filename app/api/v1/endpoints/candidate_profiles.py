from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.candidate_profile import CandidateProfile
from app.schemas.candidate_profile import CandidateProfileCreate, CandidateProfileUpdate, CandidateProfile as CandidateProfileSchema
import os
from app.core.config import settings # Import settings

router = APIRouter()

# Utility to save resume (basic file system storage, can be extended to cloud storage)
UPLOAD_DIR = settings.RESUME_UPLOAD_DIR # Use standardized upload directory

@router.post("/me/upload-resume", response_model=CandidateProfileSchema)
async def upload_candidate_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Only candidates can upload resumes")
    
    # Ensure upload directory exists using the standardized path
    os.makedirs(settings.RESUME_UPLOAD_DIR, exist_ok=True)
    
    # Sanitize filename to prevent directory traversal or other attacks
    filename = "".join(x for x in file.filename if x.isalnum() or x in "._-")
    file_location = os.path.join(settings.RESUME_UPLOAD_DIR, f"{current_user.id}_{filename}")
    
    with open(file_location, "wb+") as file_object:
        content = await file.read() # Read file content asynchronously
        file_object.write(content)
    
    # Update candidate profile with resume path, storing it relative to project root's uploads
    result = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    candidate_profile = result.scalar_one_or_none()

    if not candidate_profile:
        # If profile doesn't exist, create a basic one (should ideally be created on signup)
        candidate_profile = CandidateProfile(user_id=current_user.id)
        db.add(candidate_profile)

    candidate_profile.resume_path = os.path.join("uploads", "resumes", f"{current_user.id}_{filename}")
    db.add(candidate_profile)
    await db.commit()
    await db.refresh(candidate_profile)
    return candidate_profile

@router.post("/me", response_model=CandidateProfileSchema)
async def create_candidate_profile(
    profile_in: CandidateProfileCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Only candidates can create their profile")
    
    result = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    candidate_profile = result.scalar_one_or_none()

    if candidate_profile:
        raise HTTPException(status_code=400, detail="Candidate profile already exists. Use PUT to update.")
    
    db_obj = CandidateProfile(user_id=current_user.id, **profile_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/me", response_model=CandidateProfileSchema)
async def get_candidate_profile(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Not a candidate account")
    
    result = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    candidate_profile = result.scalar_one_or_none()
    
    if not candidate_profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return candidate_profile

@router.put("/me", response_model=CandidateProfileSchema)
async def update_candidate_profile(
    profile_in: CandidateProfileUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Only candidates can update their profile")
    
    result = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    candidate_profile = result.scalar_one_or_none()

    if not candidate_profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(candidate_profile, field, value)
    
    db.add(candidate_profile)
    await db.commit()
    await db.refresh(candidate_profile)
    return candidate_profile
