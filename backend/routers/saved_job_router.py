from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_student

from backend.models.student import Student
from backend.models.job import Job
from backend.models.live_job import LiveJob
from backend.models.saved_job import SavedJob

from backend.schemas.saved_job_schema import (
    SavedJobCreate,
    SavedJobResponse,
)


router = APIRouter(
    prefix="/saved-jobs",
    tags=["Saved Jobs"]
)


# =========================================================
# SAVE A LIVE JOB
# =========================================================

@router.post(
    "",
    response_model=SavedJobResponse,
    status_code=status.HTTP_201_CREATED
)
def save_job(
    saved_job_data: SavedJobCreate,
    current_student: Student = Depends(
        get_current_student
    ),
    db: Session = Depends(
        get_db
    )
):

    # -----------------------------------------------------
    # NEW LIVE JOB FLOW
    # -----------------------------------------------------

    live_job_id = getattr(
        saved_job_data,
        "live_job_id",
        None
    )

    if live_job_id is not None:

        live_job = (
            db.query(LiveJob)
            .filter(
                LiveJob.id == live_job_id,
                LiveJob.status == "open"
            )
            .first()
        )

        if not live_job:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Live job not found or is no longer open"
            )

        # -------------------------------------------------
        # DUPLICATE CHECK
        # -------------------------------------------------

        existing_saved_job = (
            db.query(SavedJob)
            .filter(
                SavedJob.student_id
                == current_student.student_id,

                SavedJob.live_job_id
                == live_job_id
            )
            .first()
        )

        if existing_saved_job:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job already saved"
            )

        # -------------------------------------------------
        # CREATE LIVE SAVED JOB
        # -------------------------------------------------

        new_saved_job = SavedJob(

            student_id=current_student.student_id,

            job_id=None,

            live_job_id=live_job.id
        )

        db.add(
            new_saved_job
        )

        db.commit()

        db.refresh(
            new_saved_job
        )

        return new_saved_job

    # =====================================================
    # LEGACY JOB FLOW
    # =====================================================

    job_id = getattr(
        saved_job_data,
        "job_id",
        None
    )

    if job_id:

        job = (
            db.query(Job)
            .filter(
                Job.job_id == job_id
            )
            .first()
        )

        if not job:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        existing_saved_job = (
            db.query(SavedJob)
            .filter(
                SavedJob.student_id
                == current_student.student_id,

                SavedJob.job_id
                == job_id
            )
            .first()
        )

        if existing_saved_job:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job already saved"
            )

        new_saved_job = SavedJob(

            student_id=current_student.student_id,

            job_id=job_id,

            live_job_id=None
        )

        db.add(
            new_saved_job
        )

        db.commit()

        db.refresh(
            new_saved_job
        )

        return new_saved_job

    # =====================================================
    # NOTHING PROVIDED
    # =====================================================

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either live_job_id or job_id is required"
    )


# =========================================================
# GET CURRENT STUDENT'S SAVED JOBS
# =========================================================

@router.get(
    "",
    response_model=list[SavedJobResponse]
)
def get_saved_jobs(
    current_student: Student = Depends(
        get_current_student
    ),
    db: Session = Depends(
        get_db
    )
):

    saved_jobs = (
        db.query(SavedJob)
        .filter(
            SavedJob.student_id
            == current_student.student_id
        )
        .order_by(
            SavedJob.saved_at.desc()
        )
        .all()
    )

    return saved_jobs


# =========================================================
# DELETE LIVE SAVED JOB
# =========================================================

@router.delete(
    "/live/{live_job_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_live_saved_job(
    live_job_id: int,
    current_student: Student = Depends(
        get_current_student
    ),
    db: Session = Depends(
        get_db
    )
):

    saved_job = (
        db.query(SavedJob)
        .filter(
            SavedJob.student_id
            == current_student.student_id,

            SavedJob.live_job_id
            == live_job_id
        )
        .first()
    )

    if not saved_job:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved live job not found"
        )

    db.delete(
        saved_job
    )

    db.commit()

    return None


# =========================================================
# DELETE LEGACY SAVED JOB
# =========================================================

@router.delete(
    "/legacy/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_legacy_saved_job(
    job_id: str,
    current_student: Student = Depends(
        get_current_student
    ),
    db: Session = Depends(
        get_db
    )
):

    saved_job = (
        db.query(SavedJob)
        .filter(
            SavedJob.student_id
            == current_student.student_id,

            SavedJob.job_id
            == job_id
        )
        .first()
    )

    if not saved_job:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved job not found"
        )

    db.delete(
        saved_job
    )

    db.commit()

    return None