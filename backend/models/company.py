from sqlalchemy import Column, String, Float, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class Company(Base):
    __tablename__ = "companies"

    company_id = Column(
        String(50),
        primary_key=True
    )

    company_name = Column(
        String(150),
        nullable=False,
        unique=True
    )

    rating = Column(Float)

    website = Column(String(500))

    description = Column(
        Text,
        nullable=True
    )

    jobs = relationship(
        "Job",
        back_populates="company",
        cascade="all, delete-orphan"
    )
