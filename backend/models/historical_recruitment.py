from sqlalchemy import Column, String, Integer

from backend.database import Base


class HistoricalRecruitment(Base):
    __tablename__ = "historical_recruitment"

    record_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    company = Column(
        String(150),
        nullable=False,
        index=True
    )

    year = Column(
        Integer,
        nullable=False,
        index=True
    )

    month = Column(
        String(30),
        nullable=False
    )

    department = Column(
        String(100),
        nullable=False,
        index=True
    )

    recruitment_count = Column(
        Integer,
        nullable=False
    )
