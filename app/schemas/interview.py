from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.interview import InterviewStatus, RecommendationType

class InterviewBase(BaseModel):
    application_id: int
    scheduled_at: datetime

class InterviewCreate(InterviewBase):
    pass

class InterviewUpdate(BaseModel):
    status: Optional[InterviewStatus] = None

class Interview(InterviewBase):
    id: int
    token: str
    expires_at: datetime
    status: InterviewStatus
    created_at: datetime

    class Config:
        from_attributes = True

class InterviewSessionBase(BaseModel):
    interview_id: int

class InterviewSession(InterviewSessionBase):
    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    proctoring_flags: Optional[dict]

    class Config:
        from_attributes = True

class EvaluationReportBase(BaseModel):
    session_id: int
    total_score: float
    recommendation: RecommendationType
    summary: str

class EvaluationReport(EvaluationReportBase):
    id: int
    generated_at: datetime

    class Config:
        from_attributes = True
