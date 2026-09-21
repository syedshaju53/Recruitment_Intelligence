from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApplicationCreate(BaseModel):

    job_id: Optional[str] = None

    live_job_id: Optional[int] = None

    cover_letter: Optional[str] = None
    resume_filename: Optional[str] = None
    resume_id: Optional[int] = None


class ApplicationResponse(BaseModel):
    application_id: int

    student_id: str

    # Old sample job
    job_id: Optional[str] = None

    # New live job
    live_job_id: Optional[int] = None

    company_name: Optional[str] = None
    job_title: Optional[str] = None

    source: Optional[str] = None
    source_job_id: Optional[str] = None

    status: str

    applied_at: datetime
    last_updated: datetime

    company_response: Optional[str] = None

    official_application_url: Optional[str] = None

    cover_letter: Optional[str] = None

    resume_filename: Optional[str] = None
    
    company_email: Optional[str] = None

    email_delivery_status: Optional[str] = None

    email_sent_at: Optional[datetime] = None

    email_error: Optional[str] = None

    class Config:
        from_attributes = True