from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    resume_id = Column(
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

    file_name = Column(
        String(255),
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    student = relationship(
        "Student",
        back_populates="resumes"
    )
