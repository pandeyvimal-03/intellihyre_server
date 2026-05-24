import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Enum, ForeignKey, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.job import Job
    from app.models.interview import Interview

class ApplicationStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    PARSED = "PARSED"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    COMPLETED = "COMPLETED"

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    resume_url: Mapped[str] = mapped_column(String, nullable=False)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped["User"] = relationship("User", backref="applications")
    job: Mapped["Job"] = relationship("Job", backref="applications")
    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="application")
