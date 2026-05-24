# server/app/models/recruiter_profile.py
import enum
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class RecruiterProfile(Base):
    __tablename__ = "recruiter_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Recruiter-specific fields
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    contact_person_name: Mapped[str | None] = mapped_column(String, nullable=True)
    mobile_no: Mapped[str | None] = mapped_column(String, nullable=True)
    company_size: Mapped[str | None] = mapped_column(String, nullable=True) # e.g., "1-10", "10-50", "50+"
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    company_website: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="recruiter_profile")
