from datetime import datetime

from pydantic import BaseModel


# ============================================================
# SAVE JOB REQUEST
# ============================================================

class SavedJobCreate(BaseModel):

    # New live-job system
    live_job_id: int | None = None

    # Legacy job system
    # Kept temporarily for backward compatibility
    job_id: str | None = None


# ============================================================
# SAVED JOB RESPONSE
# ============================================================

class SavedJobResponse(BaseModel):

    saved_job_id: int

    student_id: str

    # Legacy job ID
    job_id: str | None = None

    # New live job ID
    live_job_id: int | None = None

    saved_at: datetime

    class Config:
        from_attributes = True