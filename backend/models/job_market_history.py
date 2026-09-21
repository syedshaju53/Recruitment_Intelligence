from sqlalchemy import Column, Integer, String, Text, Float
from backend.database import Base


class JobMarketHistory(Base):
    __tablename__ = "job_market_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    title = Column(String(500))
    job_id = Column(String(100), index=True)
    currency = Column(String(20))
    job_uploaded = Column(String(100))

    company_name = Column(String(300), index=True)
    company_id = Column(String(100), index=True)

    tags_and_skills = Column(Text)
    experience = Column(String(200))
    salary = Column(String(200))

    location = Column(String(300), index=True)

    reviews_count = Column(Integer)
    aggregate_rating = Column(Float)

    job_description = Column(Text)

    minimum_salary = Column(Float)
    maximum_salary = Column(Float)

    minimum_experience = Column(Float)
    maximum_experience = Column(Float)