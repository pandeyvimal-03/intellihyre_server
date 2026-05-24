from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.application import ApplicationStatus

class ApplicationBase(BaseModel):
    job_id: int

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    match_score: Optional[float] = None

class UserBrief(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        from_attributes = True

class JobBrief(BaseModel):
    id: int
    title: str
    organization_name: str
    class Config:
        from_attributes = True

class EvaluationBrief(BaseModel):
    id: int
    total_score: float
    recommendation: str
    summary: str
    class Config:
        from_attributes = True

class Application(ApplicationBase):
    id: int
    candidate_id: int
    resume_url: str
    match_score: Optional[float]
    status: ApplicationStatus
    created_at: datetime
    
    candidate: Optional[UserBrief] = None
    job: Optional[JobBrief] = None
    # We might need to handle interview manually in the endpoint or via relationship
    interview_status: Optional[str] = None
    interview_result: Optional[EvaluationBrief] = None

    class Config:
        from_attributes = True

# Parsing schemas
class Experience(BaseModel):
    company: str
    role: str
    years: float

class Education(BaseModel):
    degree: str
    institution: str
    year: int

class ParsedResume(BaseModel):
    name: str
    email: str
    skills: List[str]
    experience: List[Experience]
    education: List[Education]
    certifications: List[str]
