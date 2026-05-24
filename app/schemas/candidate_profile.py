# server/app/schemas/candidate_profile.py
from typing import Optional
from pydantic import BaseModel
from app.models.candidate_profile import JobMode

class CandidateProfileBase(BaseModel):
    skills: Optional[str] = None 
    resume_path: Optional[str] = None
    desired_role: Optional[str] = None
    job_mode: JobMode = JobMode.ANY
class CandidateProfileCreate(CandidateProfileBase):
    pass

class CandidateProfileUpdate(CandidateProfileBase):
    pass

class CandidateProfile(CandidateProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
