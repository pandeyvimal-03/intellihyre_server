import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.candidate_profile import CandidateProfile # New import
from app.models.recruiter_profile import RecruiterProfile # New import

class UserRole(str, enum.Enum):
    CANDIDATE = "CANDIDATE"
    RECRUITER = "RECRUITER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CANDIDATE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="user", uselist=False)
    recruiter_profile: Mapped["RecruiterProfile"] = relationship("RecruiterProfile", back_populates="user", uselist=False)
