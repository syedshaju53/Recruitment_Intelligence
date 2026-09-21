from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String(50), primary_key=True)

    company_id = Column(
        String(50),
        ForeignKey("companies.company_id"),
        nullable=False,
        index=True
    )

    company_name = Column(
        String(150),
        nullable=False,
        index=True
    )

    role = Column(
        String(150),
        nullable=False,
        index=True
    )

    department = Column(
        String(100),
        nullable=False,
        index=True
    )

    month = Column(String(30), nullable=True)

    openings = Column(
        Integer,
        nullable=True,
        default=0
    )

    salary = Column(
        Float,
        nullable=True
    )

    location = Column(
        String(150),
        nullable=True
    )

    status = Column(
        String(50),
        nullable=True,
        default="Open",
        index=True
    )

    application_url = Column(
        String(500),
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    skills_required = Column(
        Text,
        nullable=True
    )

    posted_at = Column(
        DateTime,
        nullable=True
    )

    # created_at = Column(
    #     DateTime,
    #     default=datetime.utcnow,
    #     nullable=False
    # )

    # Company relationship
    company = relationship(
        "Company",
        back_populates="jobs"
    )

    # Saved jobs relationship
    saved_jobs = relationship(
        "SavedJob",
        back_populates="job",
        cascade="all, delete-orphan"
    )

    # Applications relationship
    applications = relationship(
        "Application",
        back_populates="job",
        cascade="all, delete-orphan"
    )