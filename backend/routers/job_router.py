from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.job import Job
from backend.schemas.job_schema import JobCreate, JobResponse


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


# --------------------------------------------------
# GET ALL JOBS
# --------------------------------------------------

@router.get("", response_model=list[JobResponse])
def get_all_jobs(db: Session = Depends(get_db)):
    jobs = (
        db.query(Job)
        .filter(Job.status.ilike("Open"))
        .order_by(Job.openings.desc())
        .all()
    )

    return jobs

# --------------------------------------------------
# GET JOB BY ID
# --------------------------------------------------

@router.get(
    "/{job_id}",
    response_model=JobResponse
)
def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = (
        db.query(Job)
        .filter(Job.job_id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


# --------------------------------------------------
# GET JOBS BY DEPARTMENT
# --------------------------------------------------

@router.get(
    "/department/{department}",
    response_model=list[JobResponse]
)
def get_jobs_by_department(
    department: str,
    db: Session = Depends(get_db)
):
    jobs = (
        db.query(Job)
        .filter(Job.department.ilike(department))
        .order_by(Job.openings.desc())
        .all()
    )

    return jobs


# --------------------------------------------------
# CREATE JOB
# --------------------------------------------------

@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED
)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db)
):

    job_id = f"JOB-{uuid4().hex[:8].upper()}"

    new_job = Job(
    job_id=job_id,
    company_id=job_data.company_id,
    company_name=job_data.company_name,
    role=job_data.role,
    department=job_data.department,
    month=job_data.month,
    openings=job_data.openings,
    salary=job_data.salary,
    location=job_data.location,
    status=job_data.status,
    application_url=job_data.application_url,
    description=job_data.description,
    skills_required=job_data.skills_required,
    posted_at=job_data.posted_at
)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job