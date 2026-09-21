from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.live_job import LiveJob


router = APIRouter(
    prefix="/live-jobs",
    tags=["Live Jobs"]
)


@router.get("/{live_job_id}")
def get_live_job(
    live_job_id: int,
    db: Session = Depends(get_db)
):

    job = (
        db.query(LiveJob)
        .filter(
            LiveJob.id == live_job_id,
            LiveJob.status == "open"
        )
        .first()
    )

    if job is None:

        raise HTTPException(
            status_code=404,
            detail="Live job not found"
        )

    return {
        "id": job.id,
        "job_id": job.job_id,
        "company_name": job.company_name,
        "job_title": job.job_title,
        "department": job.department,
        "skills": job.skills,
        "experience": job.experience,
        "salary": job.salary,
        "location": job.location,
        "work_mode": job.work_mode,
        "job_description": job.job_description,
        "posted_date": job.posted_date,
        "updated_date": job.updated_date,
        "application_url": job.application_url,
        "source": job.source,
        "source_job_id": job.source_job_id,
        "status": job.status,
        "last_checked": job.last_checked
    }
