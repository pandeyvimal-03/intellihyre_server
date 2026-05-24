from datetime import timedelta, datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload # New import

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole # Import UserRole
from app.models.candidate_profile import CandidateProfile # New import
from app.models.recruiter_profile import RecruiterProfile # New import
from app.schemas.user import UserCreate, User as UserSchema, RefreshTokenRequest # Removed Token

router = APIRouter()

@router.post("/login", response_model=UserSchema)
async def login(
    response: Response,
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    # Eager load profiles for login response
    result = await db.execute(
        select(User)
        .options(selectinload(User.candidate_profile), selectinload(User.recruiter_profile))
        .where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    access_token = security.create_access_token(user.email, expires_delta=access_token_expires_delta)
    refresh_token = security.create_refresh_token(user.email, expires_delta=refresh_token_expires_delta)

    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, 
        expires=int(access_token_expires_delta.total_seconds()),
        samesite="lax",
        secure=False,
        path="/",
        domain="localhost"
    )
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        httponly=True, 
        expires=int(refresh_token_expires_delta.total_seconds()),
        samesite="lax",
        secure=False,
        path="/",
        domain="localhost"
    )
    
    return user

@router.post("/signup", response_model=UserSchema)
async def signup(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate
) -> Any:
    print(f"Signup attempt for email: {user_in.email}, role: {user_in.role}")
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    db_obj = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        name=user_in.name,
        role=user_in.role,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj) # Refresh to get ID and ensure it's in session for relationships

    # Create empty profile immediately after user registration
    if db_obj.role == UserRole.CANDIDATE:
        candidate_profile = CandidateProfile(user_id=db_obj.id)
        db.add(candidate_profile)
    elif db_obj.role == UserRole.RECRUITER:
        recruiter_profile = RecruiterProfile(user_id=db_obj.id)
        db.add(recruiter_profile)
    
    await db.commit()
    # Refresh again to load the newly created profile relationship
    await db.refresh(db_obj) 

    # Eager load profiles for signup response
    result_with_profile = await db.execute(
        select(User)
        .options(selectinload(User.candidate_profile), selectinload(User.recruiter_profile))
        .where(User.id == db_obj.id)
    )
    user_with_profile = result_with_profile.scalar_one_or_none()
    
    return user_with_profile

@router.post("/refresh-token", response_model=UserSchema)
async def refresh_token(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = security.decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Eager load profiles for refresh response
    result = await db.execute(
        select(User)
        .options(selectinload(User.candidate_profile), selectinload(User.recruiter_profile))
        .where(User.email == user_email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token_expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    new_access_token = security.create_access_token(user.email, expires_delta=access_token_expires_delta)
    new_refresh_token = security.create_refresh_token(user.email, expires_delta=refresh_token_expires_delta)

    response.set_cookie(
        key="access_token", 
        value=new_access_token, 
        httponly=True, 
        expires=int(access_token_expires_delta.total_seconds()),
        samesite="lax",
        secure=True,
        #domain="yourdomain.com",
    )
    response.set_cookie(
        key="refresh_token", 
        value=new_refresh_token, 
        httponly=True, 
        expires=int(refresh_token_expires_delta.total_seconds()),
        samesite="lax",
        secure=True,
        #domain="yourdomain.com",
    )
    
    return user

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/", httponly=True, secure=False, samesite="lax", domain="localhost")
    response.delete_cookie(key="refresh_token", path="/", httponly=True, secure=False, samesite="lax", domain="localhost")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserSchema)
async def read_user_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get current user.
    """
    # Eager load profiles for /me endpoint
    result = await db.execute(
        select(User)
        .options(selectinload(User.candidate_profile), selectinload(User.recruiter_profile))
        .where(User.id == current_user.id)
    )
    user_with_profile = result.scalar_one_or_none()
    
    if not user_with_profile:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user_with_profile
