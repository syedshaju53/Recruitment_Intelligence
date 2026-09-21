from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from backend.database import Base


class CompanyContact(Base):
    __tablename__ = "company_contacts"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    company_name = Column(
        String(255),
        unique=True,
        nullable=False
    )

    recruitment_email = Column(
        String(255),
        nullable=False
    )

    contact_name = Column(
        String(255),
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
