# server/app/schemas/recruiter_profile.py
from typing import Optional
from pydantic import BaseModel

class RecruiterProfileBase(BaseModel):
    company_name: Optional[str] = None
    contact_person_name: Optional[str] = None
    mobile_no: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    company_website: Optional[str] = None

class RecruiterProfileCreate(RecruiterProfileBase):
    pass

class RecruiterProfileUpdate(RecruiterProfileBase):
    pass

class RecruiterProfile(RecruiterProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
