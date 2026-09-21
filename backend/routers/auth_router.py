import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.student import Student
from backend.schemas.auth_schema import (
    StudentLogin,
    LoginResponse
)
from backend.auth import create_access_token


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/students",
    tags=["Student Authentication"]
)


# ==========================================================
# STUDENT LOGIN
# ==========================================================

@router.post(
    "/login",
    response_model=LoginResponse
)
def student_login(
    login_data: StudentLogin,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # FIND STUDENT
    # ------------------------------------------------------

    student = (
        db.query(Student)
        .filter(
            Student.username == login_data.username
        )
        .first()
    )

    if not student:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # ------------------------------------------------------
    # VERIFY PASSWORD
    # ------------------------------------------------------

    try:

        password_valid = bcrypt.checkpw(
            login_data.password.encode("utf-8"),
            student.password_hash.encode("utf-8")
        )

    except ValueError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password format"
        )

    if not password_valid:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # ------------------------------------------------------
    # CREATE JWT
    # ------------------------------------------------------

    access_token = create_access_token(
        data={
            "student_id": student.student_id
        }
    )

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student_id": student.student_id,
        "student_name": student.student_name,
        "username": student.username,
        "department": student.department
    }