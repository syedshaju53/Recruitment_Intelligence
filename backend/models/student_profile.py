import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from backend.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    profile_id = Column(
        String(50),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    student_id = Column(
        String(50),
        ForeignKey("students.student_id"),
        unique=True,
        nullable=False
    )

    full_name = Column(String(150))
    email = Column(String(150))
    phone = Column(String(30))
    location = Column(String(150))

    headline = Column(String(255))
    about = Column(Text)

    department = Column(String(100))
    degree = Column(String(100))
    graduation_year = Column(Integer)
    college = Column(String(200))
    cgpa = Column(Float)

    skills = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    experience = Column(JSON, default=list)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    student = relationship(
        "Student",
        back_populates="profile"
    )