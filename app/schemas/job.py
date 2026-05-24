from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.models.job import JobStatus
from app.models.candidate_profile import JobMode

class JobBase(BaseModel):
    title: str
    organization_name: str
    role: str
    experience_required: str
    work_mode: JobMode
    location: str
    salary_range: Optional[str] = None
    skills_required: str
    description: str
    status: JobStatus = JobStatus.ACTIVE

    @field_validator("status", mode="before")
    @classmethod
    def status_to_uppercase(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    organization_name: Optional[str] = None
    role: Optional[str] = None
    experience_required: Optional[str] = None
    work_mode: Optional[JobMode] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    skills_required: Optional[str] = None
    description: Optional[str] = None
    status: Optional[JobStatus] = None

class Job(JobBase):
    id: int
    recruiter_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
