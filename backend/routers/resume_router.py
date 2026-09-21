
import os
import uuid
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_student
from backend.models.student import Student
from backend.models.resume import Resume


router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"]
)


# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# Resume storage location.
# Local default: uploads/resumes
# Production: configure RESUME_STORAGE_DIR as a persistent mounted directory.
RESUME_ROOT = Path(
    os.getenv(
        "RESUME_STORAGE_DIR",
        str(BASE_DIR / "uploads" / "resumes")
    )
)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


# ==========================================================
# UPLOAD RESUME
# ==========================================================

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_student: Student = Depends(
        get_current_student
    ),
    db: Session = Depends(get_db),
):

    # ------------------------------------------------------
    # Validate filename
    # ------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Resume filename is missing."
        )

    original_filename = Path(
        file.filename
    ).name

    extension = Path(
        original_filename
    ).suffix.lower()

    # ------------------------------------------------------
    # Validate file extension
    # ------------------------------------------------------

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported resume format. "
                "Only PDF, DOC, and DOCX files are allowed."
            )
        )

    # ------------------------------------------------------
    # Read file
    # ------------------------------------------------------

    file_data = await file.read()

    if not file_data:
        raise HTTPException(
            status_code=400,
            detail="Uploaded resume is empty."
        )

    # ------------------------------------------------------
    # Validate file size
    # ------------------------------------------------------

    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Resume file size must not exceed 5 MB."
        )

    # ------------------------------------------------------
    # Student-specific directory
    # ------------------------------------------------------

    student_directory = (
        RESUME_ROOT
        / current_student.student_id
    )

    student_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # ------------------------------------------------------
    # Generate safe unique filename
    # ------------------------------------------------------

    stored_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    stored_path = (
        student_directory
        / stored_filename
    )

    # ------------------------------------------------------
    # Save physical file
    # ------------------------------------------------------

    with open(
        stored_path,
        "wb"
    ) as resume_file:

        resume_file.write(
            file_data
        )

    # ------------------------------------------------------
    # Save database record
    # ------------------------------------------------------

    resume_record = Resume(
        student_id=current_student.student_id,
        file_name=original_filename,
        file_path=str(stored_path),
    )

    db.add(resume_record)

    try:

        db.commit()
        db.refresh(resume_record)

    except Exception:

        db.rollback()

        # Remove physical file if DB insert fails
        if stored_path.exists():
            stored_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Failed to save resume information."
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------


    return {
            "message": "Resume uploaded successfully.",
            "resume_id": resume_record.resume_id,
            "student_id": resume_record.student_id,
            "file_name": resume_record.file_name,
            "uploaded_at": resume_record.uploaded_at,
        }
