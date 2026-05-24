# server/app/models/candidate_profile.py
import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class JobMode(str, enum.Enum):
    REMOTE = "REMOTE"
    ONSITE = "ONSITE"
    HYBRID = "HYBRID"
    ANY = "ANY"

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Core fields
    skills: Mapped[str | None] = mapped_column(Text, nullable=True) 
    resume_path: Mapped[str | None] = mapped_column(String, nullable=True)
    desired_role: Mapped[str | None] = mapped_column(String, nullable=True)
    job_mode: Mapped[JobMode] = mapped_column(Enum(JobMode), default=JobMode.ANY, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="candidate_profile")
