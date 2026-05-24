import enum
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING
from sqlalchemy import String, Enum, ForeignKey, Float, DateTime, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.application import Application

class InterviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"

class ProctoringEventType(str, enum.Enum):
    NO_FACE         = "NO_FACE"
    MULTI_FACE      = "MULTI_FACE"
    LOOKING_AWAY    = "LOOKING_AWAY"   # detected by face-api.js head pose
    TAB_SWITCH      = "TAB_SWITCH"     # detected by document.visibilityState
    FULLSCREEN_EXIT = "FULLSCREEN_EXIT" # detected by fullscreenchange event

class RecommendationType(str, enum.Enum):
    SELECTED = "SELECTED"
    HOLD = "HOLD"
    REJECTED = "REJECTED"

class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[InterviewStatus] = mapped_column(Enum(InterviewStatus), default=InterviewStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship("Application", back_populates="interviews")

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    proctoring_flags: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)  # Summary of flags

    interview: Mapped["Interview"] = relationship("Interview", backref="sessions")

class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id"), nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[RecommendationType] = mapped_column(Enum(RecommendationType), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["InterviewSession"] = relationship("InterviewSession", backref="report")

class ProctoringLog(Base):
    __tablename__ = "proctoring_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id"), nullable=False)
    event_type: Mapped[ProctoringEventType] = mapped_column(Enum(ProctoringEventType), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    frame_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    session: Mapped["InterviewSession"] = relationship("InterviewSession", backref="proctoring_logs")

class QALog(Base):
    __tablename__ = "qa_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["InterviewSession"] = relationship("InterviewSession", backref="qa_logs")
