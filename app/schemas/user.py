from typing import Optional, ForwardRef
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import UserRole
# New imports
from app.schemas.candidate_profile import CandidateProfile
from app.schemas.recruiter_profile import RecruiterProfile

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.CANDIDATE

    @field_validator("role", mode="before")
    @classmethod
    def role_to_uppercase(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: int
    candidate_profile: Optional[CandidateProfile] = None
    recruiter_profile: Optional[RecruiterProfile] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

User.model_rebuild()
