from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from backend.database import Base


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    saved_job_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        String(50),
        ForeignKey("students.student_id"),
        nullable=False,
        index=True
    )

    # ---------------------------------------------------------
    # LEGACY JOB ID
    # ---------------------------------------------------------
    # Kept temporarily for old saved jobs.
    job_id = Column(
        String(50),
        ForeignKey("jobs.job_id"),
        nullable=True,
        index=True
    )

    # ---------------------------------------------------------
    # NEW LIVE JOB ID
    # ---------------------------------------------------------
    live_job_id = Column(
        Integer,
        ForeignKey("live_jobs.id"),
        nullable=True,
        index=True
    )

    saved_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------

    student = relationship(
        "Student",
        back_populates="saved_jobs"
    )

    # Legacy relationship
    job = relationship(
        "Job",
        back_populates="saved_jobs",
        foreign_keys=[job_id]
    )

    # New live-job relationship
    live_job = relationship(
        "LiveJob",
        foreign_keys=[live_job_id]
    )

    # ---------------------------------------------------------
    # CONSTRAINTS
    # ---------------------------------------------------------

    __table_args__ = (

        # Legacy saved-job protection
        UniqueConstraint(
            "student_id",
            "job_id",
            name="uq_student_saved_job"
        ),

        # New live-job protection
        UniqueConstraint(
            "student_id",
            "live_job_id",
            name="uq_student_saved_live_job"
        ),
    )