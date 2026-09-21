from sqlalchemy import Column, Integer, String, Text, DateTime

from backend.database import Base


class LiveJob(Base):

    __tablename__ = "live_jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    job_id = Column(
        String(255),
        nullable=False,
        index=True
    )

    company_name = Column(
        String(255),
        nullable=False,
        index=True
    )

    job_title = Column(
        String(500),
        nullable=False,
        index=True
    )

    department = Column(
        String(255)
    )

    skills = Column(
        Text
    )

    experience = Column(
        String(100)
    )

    salary = Column(
        String(255)
    )

    location = Column(
        String(500)
    )

    work_mode = Column(
        String(100)
    )

    job_description = Column(
        Text
    )

    posted_date = Column(
        DateTime
    )

    updated_date = Column(
        DateTime
    )

    application_url = Column(
        Text
    )

    source = Column(
        String(100),
        nullable=False
    )

    source_job_id = Column(
        String(255),
        index=True
    )

    status = Column(
        String(50),
        default="open",
        index=True
    )

    last_checked = Column(
        DateTime
    )