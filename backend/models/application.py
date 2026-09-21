from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Application(Base):
    __tablename__ = "applications"

    application_id = Column(
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

    # OLD SAMPLE JOB REFERENCE
    # Kept temporarily for existing applications.
    job_id = Column(
        String(50),
        ForeignKey("jobs.job_id"),
        nullable=True,
        index=True
    )

    # NEW — LIVE JOB DATABASE ID
    live_job_id = Column(
        Integer,
        ForeignKey("live_jobs.id"),
        nullable=True,
        index=True
    )

    # Snapshot information so My Applications
    # still displays the job even if the live opening
    # later disappears from live_jobs.
    company_name = Column(
        String(255),
        nullable=True
    )

    job_title = Column(
        String(500),
        nullable=True
    )

    source = Column(
        String(100),
        nullable=True
    )

    source_job_id = Column(
        String(255),
        nullable=True
    )

    status = Column(
        String(50),
        default="Applied",
        nullable=False
    )

    applied_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    company_response = Column(Text)

    cover_letter = Column(Text)

    resume_filename = Column(
        String(255)
    )
    resume_id = Column(
        Integer,
        ForeignKey("resumes.resume_id"),
        nullable=True,
        index=True
    )
    company_email = Column(
        String(255),
        nullable=True
    )

    email_delivery_status = Column(
        String(50),
        default="Pending",
        nullable=False
    )

    email_sent_at = Column(
        DateTime,
        nullable=True
    )

    email_error = Column(
        Text,
        nullable=True
    )

    official_application_url = Column(
        String(500)
    )

    student = relationship(
        "Student",
        back_populates="applications"
    )

    # OLD JOB RELATIONSHIP
    job = relationship(
        "Job",
        back_populates="applications"
    )

    # LIVE JOB RELATIONSHIP
    live_job = relationship(
        "LiveJob",
        foreign_keys=[live_job_id]
    )
    resume = relationship(
        "Resume",
        foreign_keys=[resume_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "job_id",
            name="uq_student_job_application"
        ),
        UniqueConstraint(
            "student_id",
            "live_job_id",
            name="uq_student_live_job_application"
        ),
    )