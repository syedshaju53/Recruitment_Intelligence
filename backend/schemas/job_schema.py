from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobCreate(BaseModel):
    company_id: str
    company_name: str
    role: str
    department: str
    month: Optional[str] = None
    openings: int = 0
    salary: Optional[float] = None
    location: Optional[str] = None
    status: str = "Open"
    application_url: Optional[str] = None
    description: Optional[str] = None
    skills_required: Optional[str] = None
    posted_at: Optional[datetime] = None


class JobResponse(BaseModel):
    job_id: str
    company_id: str
    company_name: str
    role: str
    department: str
    month: Optional[str]
    openings: Optional[int]
    salary: Optional[float]
    location: Optional[str]
    status: Optional[str]
    application_url: Optional[str]
    description: Optional[str]
    skills_required: Optional[str]
    posted_at: Optional[datetime]

    class Config:
        from_attributes = True