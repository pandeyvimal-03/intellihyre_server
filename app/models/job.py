import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Enum, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User

class JobStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"

from app.models.candidate_profile import JobMode

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    organization_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    experience_required: Mapped[str] = mapped_column(String, nullable=False)
    work_mode: Mapped[JobMode] = mapped_column(Enum(JobMode), nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    salary_range: Mapped[str] = mapped_column(String, nullable=True)
    skills_required: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.ACTIVE, nullable=False)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    recruiter: Mapped["User"] = relationship("User", backref="jobs")
