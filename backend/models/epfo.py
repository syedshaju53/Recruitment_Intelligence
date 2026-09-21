from sqlalchemy import Column, Integer, String, Float
from backend.database import Base


class EPFONationalPayroll(Base):
    __tablename__ = "epfo_national_payroll"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(50), nullable=False)
    age_group = Column(String(50))
    member_count = Column(Integer)
    establishments = Column(Integer)


class EPFOStatePayroll(Base):
    __tablename__ = "epfo_state_payroll"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(50), nullable=False)
    state = Column(String(100), nullable=False)
    member_count = Column(Integer)
    establishments = Column(Integer)


class EPFOIndustryPayroll(Base):
    __tablename__ = "epfo_industry_payroll"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(50), nullable=False)
    industry = Column(String(200), nullable=False)
    member_count = Column(Integer)
    establishments = Column(Integer)