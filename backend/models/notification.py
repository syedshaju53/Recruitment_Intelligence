from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(
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

    title = Column(
        String(200),
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    notification_type = Column(
        String(50),
        default="General"
    )

    is_read = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    student = relationship(
        "Student",
        back_populates="notifications"
    )
