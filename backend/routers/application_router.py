from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import get_current_student
from backend.database import get_db

from backend.application_email_service import send_application_email

from backend.models.application import Application
from backend.models.company_contact import CompanyContact
from backend.models.job import Job
from backend.models.live_job import LiveJob
from backend.models.resume import Resume
from backend.models.student import Student

from backend.schemas.application_schema import (
    ApplicationCreate,
    ApplicationResponse,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"]
)


# ============================================================
# APPLY FOR JOB
# ============================================================

@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED
)
def apply_for_job(
    application_data: ApplicationCreate,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):

    print(
        "DEBUG APPLICATION REQUEST:",
        "job_id =", application_data.job_id,
        "live_job_id =", application_data.live_job_id,
        "resume_id =", application_data.resume_id
    )

    # ========================================================
    # VALIDATE JOB SOURCE
    # ========================================================

    if not application_data.job_id and not application_data.live_job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either job_id or live_job_id is required."
        )

    if application_data.job_id and application_data.live_job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use either job_id or live_job_id, not both."
        )

    # ========================================================
    # VALIDATE RESUME
    # ========================================================

    resume = None

    if application_data.resume_id is not None:

        resume = (
            db.query(Resume)
            .filter(
                Resume.resume_id == application_data.resume_id,
                Resume.student_id == current_student.student_id
            )
            .first()
        )

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or does not belong to the current student."
            )

    # ========================================================
    # OLD SAMPLE JOB APPLICATION
    # ========================================================

    if application_data.job_id:

        job = (
            db.query(Job)
            .filter(
                Job.job_id == application_data.job_id
            )
            .first()
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        existing_application = (
            db.query(Application)
            .filter(
                Application.student_id == current_student.student_id,
                Application.job_id == application_data.job_id
            )
            .first()
        )

        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already applied for this job"
            )

        now = datetime.utcnow()

        new_application = Application(
            student_id=current_student.student_id,

            job_id=application_data.job_id,
            live_job_id=None,

            company_name=getattr(
                job,
                "company_name",
                None
            ),

            job_title=getattr(
                job,
                "role",
                None
            ),

            source="legacy",

            source_job_id=application_data.job_id,

            status="Applied",

            applied_at=now,
            last_updated=now,

            company_response=None,

            official_application_url=getattr(
                job,
                "application_url",
                None
            ),

            cover_letter=application_data.cover_letter,

            resume_filename=(
                application_data.resume_filename
                or (resume.file_name if resume else None)
            ),

            resume_id=(
                resume.resume_id
                if resume
                else None
            ),

            email_delivery_status="Pending"
        )

    # ========================================================
    # LIVE JOB APPLICATION
    # ========================================================

    else:

        live_job = (
            db.query(LiveJob)
            .filter(
                LiveJob.id == application_data.live_job_id,
                LiveJob.status == "open"
            )
            .first()
        )

        if not live_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Live job opening not found or no longer open."
            )

        # ----------------------------------------------------
        # DUPLICATE CHECK
        # ----------------------------------------------------

        existing_application = (
            db.query(Application)
            .filter(
                Application.student_id == current_student.student_id,
                Application.live_job_id == application_data.live_job_id
            )
            .first()
        )

        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already applied for this job"
            )

        # ----------------------------------------------------
        # CREATE LIVE APPLICATION
        # ----------------------------------------------------

        now = datetime.utcnow()

        new_application = Application(

            student_id=current_student.student_id,

            job_id=None,

            live_job_id=live_job.id,

            company_name=live_job.company_name,

            job_title=live_job.job_title,

            source=live_job.source,

            source_job_id=live_job.source_job_id,

            status="Applied",

            applied_at=now,

            last_updated=now,

            company_response=None,

            official_application_url=(
                live_job.application_url
            ),

            cover_letter=(
                application_data.cover_letter
            ),

            resume_filename=(
                application_data.resume_filename
                or (resume.file_name if resume else None)
            ),

            resume_id=(
                resume.resume_id
                if resume
                else None
            ),

            email_delivery_status="Pending"
        )

    # ========================================================
    # SAVE APPLICATION FIRST
    # ========================================================

    db.add(new_application)

    db.commit()

    db.refresh(new_application)

    # ========================================================
    # RESOLVE COMPANY CONTACT
    # ========================================================

    company_contact = None

    if new_application.company_name:

        company_contact = (
            db.query(CompanyContact)
            .filter(
                CompanyContact.company_name.ilike(
                    new_application.company_name
                ),
                CompanyContact.is_active == True
            )
            .first()
        )

    if not company_contact:

        new_application.email_delivery_status = "Not Configured"
        new_application.email_error = (
            "No active recruitment email is configured "
            "for this company."
        )

        db.commit()
        db.refresh(new_application)

        return new_application

    # ========================================================
    # STORE COMPANY EMAIL SNAPSHOT
    # ========================================================

    new_application.company_email = (
        company_contact.recruitment_email
    )

    db.commit()
    db.refresh(new_application)

    # ========================================================
    # SEND APPLICATION EMAIL
    # ========================================================

    try:

        if not resume:

            new_application.email_delivery_status = "Failed"
            new_application.email_error = (
                "No resume was attached to the application."
            )

            db.commit()
            db.refresh(new_application)

            return new_application

        send_application_email(

            recipient_email=(
                company_contact.recruitment_email
            ),

            student_name=current_student.student_name,

            student_email=current_student.email,

            student_id=current_student.student_id,

            application_id=new_application.application_id,

            company_name=new_application.company_name,

            job_title=new_application.job_title,

            location=(
                getattr(live_job, "location", None)
                if application_data.live_job_id
                else None
            ),

            cover_letter=(
                new_application.cover_letter
            ),

            resume_path=resume.file_path,

            resume_filename=resume.file_name,

            official_application_url=(
                new_application.official_application_url
            )
        )

        new_application.email_delivery_status = "Sent"

        new_application.email_sent_at = datetime.utcnow()

        new_application.email_error = None

        db.commit()
        db.refresh(new_application)

    except Exception as exc:

        new_application.email_delivery_status = "Failed"

        new_application.email_error = str(exc)

        db.commit()
        db.refresh(new_application)

    return new_application


# ============================================================
# GET MY APPLICATIONS
# ============================================================

@router.get(
    "",
    response_model=list[ApplicationResponse]
)
def get_my_applications(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):

    applications = (
        db.query(Application)
        .filter(
            Application.student_id ==
            current_student.student_id
        )
        .order_by(
            Application.applied_at.desc()
        )
        .all()
    )

    return applications


# ============================================================
# GET SINGLE APPLICATION
# ============================================================

@router.get(
    "/{application_id}",
    response_model=ApplicationResponse
)
def get_application(
    application_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):

    application = (
        db.query(Application)
        .filter(
            Application.application_id ==
            application_id,

            Application.student_id ==
            current_student.student_id
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    return application