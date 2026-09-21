from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from backend.database import Base


class Student(Base):

    __tablename__ = "students"

    student_id = Column(
        String(50),
        primary_key=True
    )

    student_name = Column(
        String(150),
        nullable=False
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    department = Column(
        String(100),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ==========================================================
    # RELATIONSHIPS
    # ==========================================================

    profile = relationship(
        "StudentProfile",
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan"
    )

    resumes = relationship(
        "Resume",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    saved_jobs = relationship(
        "SavedJob",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    applications = relationship(
        "Application",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    notifications = relationship(
        "Notification",
        back_populates="student",
        cascade="all, delete-orphan"
    )